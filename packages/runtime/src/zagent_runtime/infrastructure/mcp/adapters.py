"""AG2 MCP adapters."""

from __future__ import annotations

import inspect
import json
from collections.abc import Coroutine
from datetime import UTC, datetime
from typing import Any

from autogen.tools import Tool  # type: ignore[import-untyped]

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.application.ports.observe_run import RunObserverPort
from zagent_runtime.application.ports.register_mcp import McpServerLoader
from zagent_runtime.domain.mcp import McpServerSpec
from zagent_runtime.domain.observability import RunEvent
from zagent_runtime.domain.tools import ToolCallStatus, ToolEvent
from zagent_runtime.infrastructure.async_bridge import AsyncBridge
from zagent_runtime.infrastructure.mcp.client_factory import (
    Ag2McpToolkitFactory,
    Ag2McpToolkitHandle,
)


class Ag2McpToolAdapter:
    def __init__(
        self,
        server_loader: McpServerLoader,
        toolkit_factory: Ag2McpToolkitFactory,
        async_bridge: AsyncBridge,
        observer: RunObserverPort,
    ) -> None:
        self._server_loader = server_loader
        self._toolkit_factory = toolkit_factory
        self._async_bridge = async_bridge
        self._observer = observer

    def register(
        self,
        context: RuntimeContext,
        assistant: Any,
        executor: Any,
    ) -> tuple[Ag2McpToolkitHandle, ...]:
        if not context.run_spec.tools.enable_mcp:
            return ()
        if context.agent_env.mcp_servers_file is None:
            return ()

        config_file = context.paths.agent_env_dir / context.agent_env.mcp_servers_file
        server_config = self._server_loader.load(config_file)
        handles: list[Ag2McpToolkitHandle] = []

        current_server: McpServerSpec | None = None
        try:
            for server in server_config.enabled_servers():
                current_server = server
                self._emit_event(
                    context,
                    "mcp_server_connecting",
                    {"server": server.name, "transport": server.transport.value},
                )

                def create_toolkit(
                    server: McpServerSpec = server,
                ) -> Coroutine[Any, Any, Ag2McpToolkitHandle]:
                    return self._create_toolkit(server, context)

                handle = self._async_bridge.run(create_toolkit)
                handles.append(handle)
                self._wrap_toolkit(context, server.name, handle.toolkit)
                handle.register(assistant=assistant, executor=executor)

                self._emit_event(
                    context,
                    "mcp_server_connected",
                    {
                        "server": server.name,
                        "transport": server.transport.value,
                        "tools": self._tool_names(handle.toolkit),
                    },
                )
        except Exception:
            payload: dict[str, Any] = {"error": "MCP server registration failed"}
            if current_server is not None:
                payload["server"] = current_server.name
                payload["transport"] = current_server.transport.value
            self._emit_event(
                context,
                "mcp_server_failed",
                payload,
            )
            for handle in reversed(handles):
                self._async_bridge.run(handle.aclose)
            raise

        return tuple(handles)

    def _create_toolkit(
        self,
        server: McpServerSpec,
        context: RuntimeContext,
    ) -> Coroutine[Any, Any, Ag2McpToolkitHandle]:
        return self._toolkit_factory.create(server, context)

    def _wrap_toolkit(self, context: RuntimeContext, server_name: str, toolkit: Any) -> None:
        for tool in list(toolkit.tools):
            toolkit.set_tool(self._wrapped_tool(context, server_name, tool))

    def _wrapped_tool(self, context: RuntimeContext, server_name: str, tool: Any) -> Tool:
        func = tool.func
        trace_name = f"mcp:{server_name}.{tool.name}"

        def traced_tool(*args: Any, **kwargs: Any) -> Any:
            trace_args = self._trace_args(args, kwargs)
            self._emit_tool_started(context, trace_name, trace_args)
            try:
                if inspect.iscoroutinefunction(func):
                    result = self._async_bridge.run(lambda: func(*args, **kwargs))
                else:
                    result = func(*args, **kwargs)
            except Exception as error:
                self._emit_tool_finished(
                    context,
                    trace_name,
                    ToolCallStatus.FAILED,
                    trace_args,
                    stderr=str(error),
                )
                raise

            self._emit_tool_finished(
                context,
                trace_name,
                ToolCallStatus.FINISHED,
                trace_args,
                stdout=self._trace_value(result),
            )
            return result

        traced_tool.__name__ = tool.name
        traced_tool.__doc__ = tool.description
        return Tool(
            name=tool.name,
            description=tool.description,
            func_or_tool=traced_tool,
            parameters_json_schema=self._parameters_schema(tool),
        )

    def _parameters_schema(self, tool: Any) -> dict[str, Any] | None:
        raw_func_schema = getattr(tool, "_func_schema", None)
        if isinstance(raw_func_schema, dict):
            function = raw_func_schema.get("function")
            if isinstance(function, dict):
                parameters = function.get("parameters")
                if isinstance(parameters, dict):
                    return parameters

        function_schema = getattr(tool, "function_schema", None)
        if isinstance(function_schema, dict):
            parameters = function_schema.get("parameters")
            if isinstance(parameters, dict):
                return parameters

        tool_schema = getattr(tool, "tool_schema", None)
        if isinstance(tool_schema, dict):
            function = tool_schema.get("function")
            if isinstance(function, dict):
                parameters = function.get("parameters")
                if isinstance(parameters, dict):
                    return parameters

        return None

    def _tool_names(self, toolkit: Any) -> list[str]:
        return [str(tool.name) for tool in toolkit.tools]

    def _trace_args(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        trace_args = self._trace_mapping(kwargs)
        if args:
            trace_args["args"] = self._trace_value(list(args))
        return trace_args

    def _trace_mapping(self, mapping: dict[str, Any]) -> dict[str, Any]:
        return {str(key): self._trace_value(value) for key, value in mapping.items()}

    def _trace_value(self, value: Any, max_chars: int = 20_000) -> Any:
        if isinstance(value, str):
            return self._truncate(value, max_chars)
        if isinstance(value, int | float | bool) or value is None:
            return value

        try:
            rendered = json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            rendered = repr(value)

        return self._truncate(rendered, max_chars)

    def _truncate(self, value: str, max_chars: int) -> str:
        if len(value) <= max_chars:
            return value
        omitted = len(value) - max_chars
        return f"{value[:max_chars]}...[truncated {omitted} chars]"

    def _emit_tool_started(
        self,
        context: RuntimeContext,
        tool: str,
        args: dict[str, Any],
    ) -> None:
        self._observer.on_tool_started(
            context.paths,
            ToolEvent(
                ts=self._now(),
                tool=tool,
                status=ToolCallStatus.STARTED,
                args=args,
            ),
        )

    def _emit_tool_finished(
        self,
        context: RuntimeContext,
        tool: str,
        status: ToolCallStatus,
        args: dict[str, Any],
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> None:
        self._observer.on_tool_finished(
            context.paths,
            ToolEvent(
                ts=self._now(),
                tool=tool,
                status=status,
                args=args,
                stdout=stdout,
                stderr=stderr,
            ),
        )

    def _emit_event(self, context: RuntimeContext, event: str, payload: dict[str, Any]) -> None:
        self._observer.on_event(
            context.paths,
            RunEvent(
                ts=self._now(),
                event=event,
                payload=payload,
            ),
        )

    def _now(self) -> datetime:
        return datetime.now(UTC)
