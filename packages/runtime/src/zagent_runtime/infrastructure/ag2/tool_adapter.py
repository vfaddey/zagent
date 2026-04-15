"""AG2 tool adapter."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from zagent_runtime.application.observe_run import RunObserverPort
from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.tools import ToolCallStatus, ToolEvent
from zagent_runtime.infrastructure.tools.base import ToolBackend, ToolExecutionResult
from zagent_runtime.infrastructure.tools.builtin.files import FilesTool
from zagent_runtime.infrastructure.tools.builtin.git import GitTool
from zagent_runtime.infrastructure.tools.builtin.shell import ShellTool
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class Ag2FunctionTool:
    name: str
    description: str
    function: Callable[..., str]

    def __call__(self, **kwargs: object) -> str:
        return self.function(**kwargs)


class Ag2RuntimeToolAdapter:
    def __init__(
        self,
        files_tool: FilesTool,
        git_tool: GitTool,
        shell_tool: ShellTool,
        observer: RunObserverPort,
    ) -> None:
        self._files_tool = files_tool
        self._git_tool = git_tool
        self._shell_tool = shell_tool
        self._observer = observer

    def build_tools(
        self,
        context: RuntimeContext,
        tool_registry: ToolRegistry,
    ) -> tuple[Ag2FunctionTool, ...]:
        runtime_native_names = set(tool_registry.backend_names(ToolBackend.RUNTIME_NATIVE))
        tools: list[Ag2FunctionTool] = []

        if "files" in runtime_native_names:
            tools.extend(
                (
                    self._files_read_text(context),
                    self._files_write_text(context),
                    self._files_list_dir(context),
                )
            )

        if "git" in runtime_native_names:
            tools.extend(
                (
                    self._git_status(context),
                    self._git_diff(context),
                )
            )

        if "shell" in runtime_native_names:
            tools.append(self._shell_run(context))

        return tuple(tools)

    def _files_read_text(self, context: RuntimeContext) -> Ag2FunctionTool:
        def files_read_text(path: str, max_chars: int = 20_000) -> str:
            """Read a UTF-8 text file from the workspace."""
            return self._execute(
                context=context,
                tool="files_read_text",
                args={"path": path, "max_chars": max_chars},
                call=lambda: self._files_tool.read_text(
                    context,
                    path=path,
                    max_chars=max_chars,
                ),
            )

        return Ag2FunctionTool(
            name="files_read_text",
            description="Read a UTF-8 text file from the workspace.",
            function=files_read_text,
        )

    def _files_write_text(self, context: RuntimeContext) -> Ag2FunctionTool:
        def files_write_text(path: str, content: str) -> str:
            return self._execute(
                context=context,
                tool="files_write_text",
                args={"path": path, "content": content},
                call=lambda: self._files_tool.write_text(
                    context,
                    path=path,
                    content=content,
                ),
            )

        return Ag2FunctionTool(
            name="files_write_text",
            description="Write a UTF-8 text file inside writable workspace roots.",
            function=files_write_text,
        )

    def _files_list_dir(self, context: RuntimeContext) -> Ag2FunctionTool:
        def files_list_dir(path: str = ".") -> str:
            """List a directory inside the workspace."""
            return self._execute(
                context=context,
                tool="files_list_dir",
                args={"path": path},
                call=lambda: self._files_tool.list_dir(context, path=path),
            )

        return Ag2FunctionTool(
            name="files_list_dir",
            description="List a directory inside the workspace.",
            function=files_list_dir,
        )

    def _git_status(self, context: RuntimeContext) -> Ag2FunctionTool:
        def git_status() -> str:
            """Return short git status for the workspace."""
            return self._execute(
                context=context,
                tool="git_status",
                args={},
                call=lambda: self._git_tool.status(context),
            )

        return Ag2FunctionTool(
            name="git_status",
            description="Return short git status for the workspace.",
            function=git_status,
        )

    def _git_diff(self, context: RuntimeContext) -> Ag2FunctionTool:
        def git_diff(staged: bool = False) -> str:
            """Return git diff for the workspace."""
            return self._execute(
                context=context,
                tool="git_diff",
                args={"staged": staged},
                call=lambda: self._git_tool.diff(context, staged=staged),
            )

        return Ag2FunctionTool(
            name="git_diff",
            description="Return git diff for the workspace.",
            function=git_diff,
        )

    def _shell_run(self, context: RuntimeContext) -> Ag2FunctionTool:
        def shell_run(
            command: str,
            timeout_seconds: int = 60,
            max_output_chars: int = 20_000,
        ) -> str:
            """Run a shell command in the workspace."""
            return self._execute(
                context=context,
                tool="shell_run",
                args={
                    "command": command,
                    "timeout_seconds": timeout_seconds,
                    "max_output_chars": max_output_chars,
                },
                call=lambda: self._shell_tool.run(
                    context,
                    command=command,
                    timeout_seconds=timeout_seconds,
                    max_output_chars=max_output_chars,
                ),
            )

        return Ag2FunctionTool(
            name="shell_run",
            description="Run a shell command in the workspace.",
            function=shell_run,
        )

    def _execute(
        self,
        context: RuntimeContext,
        tool: str,
        args: dict[str, Any],
        call: Callable[[], ToolExecutionResult],
    ) -> str:
        trace_args = self._trace_args(args)
        self._observer.on_tool_started(
            context.paths,
            ToolEvent(
                ts=self._now(),
                tool=tool,
                status=ToolCallStatus.STARTED,
                args=trace_args,
            ),
        )

        try:
            result = call()
        except Exception as error:
            self._observer.on_tool_finished(
                context.paths,
                ToolEvent(
                    ts=self._now(),
                    tool=tool,
                    status=ToolCallStatus.FAILED,
                    args=trace_args,
                    stderr=str(error),
                ),
            )
            raise

        status = ToolCallStatus.FINISHED if result.ok else ToolCallStatus.FAILED
        self._observer.on_tool_finished(
            context.paths,
            ToolEvent(
                ts=self._now(),
                tool=tool,
                status=status,
                args=trace_args,
                exit_code=result.exit_code,
                stdout=result.output,
                stderr=result.error,
            ),
        )
        return self._render(result)

    def _render(self, result: ToolExecutionResult) -> str:
        return json.dumps(asdict(result), ensure_ascii=False)

    def _trace_args(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            key: self._trace_value(value)
            for key, value in args.items()
        }

    def _trace_value(self, value: Any, max_chars: int = 2_000) -> Any:
        if isinstance(value, str):
            if len(value) <= max_chars:
                return value
            omitted = len(value) - max_chars
            return f"{value[:max_chars]}...[truncated {omitted} chars]"
        if isinstance(value, dict):
            return {
                str(key): self._trace_value(nested_value, max_chars=max_chars)
                for key, nested_value in value.items()
            }
        if isinstance(value, tuple | list):
            return [self._trace_value(item, max_chars=max_chars) for item in value]
        return value

    def _now(self) -> datetime:
        return datetime.now(UTC)
