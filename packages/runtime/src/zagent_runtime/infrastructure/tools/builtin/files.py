"""Built-in file tool."""

from __future__ import annotations

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.infrastructure.security.policies import FileSystemPolicy
from zagent_runtime.infrastructure.tools.base import ToolExecutionResult


class FilesTool:
    def __init__(self, policy: FileSystemPolicy) -> None:
        self._policy = policy

    def read_text(
        self,
        context: RuntimeContext,
        path: str,
        max_chars: int = 20_000,
    ) -> ToolExecutionResult:
        resolved = self._policy.resolve_workspace_path(context, path)
        self._policy.ensure_read_allowed(context, resolved)
        content = resolved.read_text(encoding="utf-8")
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars]
        return ToolExecutionResult(
            tool="files.read_text",
            ok=True,
            output=content,
            data={
                "path": str(resolved),
                "truncated": truncated,
            },
        )

    def write_text(
        self,
        context: RuntimeContext,
        path: str,
        content: str,
    ) -> ToolExecutionResult:
        resolved = self._policy.resolve_workspace_path(context, path)
        self._policy.ensure_write_allowed(context, resolved)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return ToolExecutionResult(
            tool="files.write_text",
            ok=True,
            output=str(resolved),
            data={
                "path": str(resolved),
                "bytes_written": len(content.encode("utf-8")),
            },
        )

    def list_dir(self, context: RuntimeContext, path: str = ".") -> ToolExecutionResult:
        resolved = self._policy.resolve_workspace_path(context, path)
        self._policy.ensure_read_allowed(context, resolved)
        entries = sorted(item.name for item in resolved.iterdir())
        return ToolExecutionResult(
            tool="files.list_dir",
            ok=True,
            output="\n".join(entries),
            data={
                "path": str(resolved),
                "entries": entries,
            },
        )
