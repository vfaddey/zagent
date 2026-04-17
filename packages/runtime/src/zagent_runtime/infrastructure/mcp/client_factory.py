"""AG2 MCP client factory."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any, cast

from autogen.mcp import create_toolkit  # type: ignore[import-untyped]
from autogen.mcp.mcp_client import (  # type: ignore[import-untyped]
    MCPClientSessionManager,
    SseConfig,
    StdioConfig,
)
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.mcp import McpServerSpec, McpTransport
from zagent_runtime.infrastructure.mcp.server_spec import resolve_env_mapping


@dataclass(frozen=True, slots=True)
class StreamableHttpSessionConfig:
    server_name: str
    url: str
    headers: dict[str, str] | None = None
    timeout_seconds: float = 30
    read_timeout_seconds: float = 300

    @asynccontextmanager
    async def create_session(self, exit_stack: AsyncExitStack) -> AsyncIterator[ClientSession]:
        client = streamablehttp_client(
            self.url,
            headers=self.headers,
            timeout=self.timeout_seconds,
            sse_read_timeout=self.read_timeout_seconds,
        )
        read, write, _ = await exit_stack.enter_async_context(client)
        session = cast(
            ClientSession,
            await exit_stack.enter_async_context(ClientSession(read, write)),
        )
        yield session


@dataclass(slots=True)
class Ag2McpToolkitHandle:
    server_name: str
    toolkit: Any
    session_manager: MCPClientSessionManager
    session_context: AbstractAsyncContextManager[ClientSession]

    async def aclose(self) -> None:
        toolkit_close = getattr(self.toolkit, "close", None)
        if callable(toolkit_close):
            close_result = toolkit_close()
            if inspect.isawaitable(close_result):
                await close_result

        await self.session_context.__aexit__(None, None, None)
        await self.session_manager.exit_stack.aclose()

    def register(self, assistant: Any, executor: Any) -> None:
        self.toolkit.register_for_llm(assistant)
        self.toolkit.register_for_execution(executor)


class Ag2McpToolkitFactory:
    async def create(self, server: McpServerSpec, context: RuntimeContext) -> Ag2McpToolkitHandle:
        session_manager = MCPClientSessionManager()
        session_config = self._session_config(server)
        session_context = session_manager.open_session(session_config)
        session = await session_context.__aenter__()

        try:
            toolkit = await create_toolkit(
                session=session,
                use_mcp_tools=server.use_tools,
                use_mcp_resources=server.use_resources,
                resource_download_folder=context.paths.run_artifacts_dir / "mcp_resources",
            )
        except Exception:
            await session_context.__aexit__(None, None, None)
            await session_manager.exit_stack.aclose()
            raise

        return Ag2McpToolkitHandle(
            server_name=server.name,
            toolkit=toolkit,
            session_manager=session_manager,
            session_context=session_context,
        )

    def _session_config(self, server: McpServerSpec) -> Any:
        if server.transport is McpTransport.STDIO:
            return self._stdio_config(server)
        if server.transport is McpTransport.SSE:
            return self._sse_config(server)
        if server.transport is McpTransport.STREAMABLE_HTTP:
            return self._streamable_http_config(server)
        raise ValueError(f"Unsupported MCP transport: {server.transport}")

    def _stdio_config(self, server: McpServerSpec) -> StdioConfig:
        if server.command is None:
            raise ValueError(f"MCP server {server.name} requires command")

        environment = resolve_env_mapping(server.environment, server.environment_env)
        return StdioConfig(
            server_name=server.name,
            command=server.command,
            args=list(server.args),
            environment=environment or None,
            working_dir=server.working_dir,
        )

    def _sse_config(self, server: McpServerSpec) -> SseConfig:
        if server.url is None:
            raise ValueError(f"MCP server {server.name} requires url")

        headers = resolve_env_mapping(server.headers, server.headers_env)
        return SseConfig(
            server_name=server.name,
            url=server.url,
            headers=headers or None,
            timeout=server.timeout_seconds or 5,
            sse_read_timeout=server.read_timeout_seconds or 300,
        )

    def _streamable_http_config(self, server: McpServerSpec) -> StreamableHttpSessionConfig:
        if server.url is None:
            raise ValueError(f"MCP server {server.name} requires url")

        headers = resolve_env_mapping(server.headers, server.headers_env)
        return StreamableHttpSessionConfig(
            server_name=server.name,
            url=server.url,
            headers=headers or None,
            timeout_seconds=server.timeout_seconds or 30,
            read_timeout_seconds=server.read_timeout_seconds or 300,
        )
