"""Built-in git tool."""

from __future__ import annotations

import subprocess

from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.infrastructure.tools.base import ToolExecutionResult


class GitTool:
    def status(self, context: RuntimeContext) -> ToolExecutionResult:
        return self._run(context, ("status", "--short"))

    def diff(self, context: RuntimeContext, staged: bool = False) -> ToolExecutionResult:
        args = ("diff", "--cached") if staged else ("diff",)
        return self._run(context, args)

    def show(self, context: RuntimeContext, revision: str = "HEAD") -> ToolExecutionResult:
        return self._run(context, ("show", "--stat", "--oneline", revision))

    def _run(
        self,
        context: RuntimeContext,
        args: tuple[str, ...],
        timeout_seconds: int = 30,
    ) -> ToolExecutionResult:
        completed = subprocess.run(
            ("git", "-C", str(context.paths.workspace), *args),
            capture_output=True,
            check=False,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
        return ToolExecutionResult(
            tool=f"git.{args[0]}",
            ok=completed.returncode == 0,
            output=completed.stdout,
            exit_code=completed.returncode,
            error=completed.stderr or None,
            data={"args": list(args)},
        )
