"""Built-in shell tool."""

from __future__ import annotations

import subprocess

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.infrastructure.tools.base import ToolExecutionResult


class ShellTool:
    def run(
        self,
        context: RuntimeContext,
        command: str,
        timeout_seconds: int = 60,
        max_output_chars: int = 20_000,
    ) -> ToolExecutionResult:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                cwd=context.paths.workspace,
                encoding="utf-8",
                shell=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            return ToolExecutionResult(
                tool="shell.run",
                ok=False,
                output=self._preview(error.stdout, max_output_chars),
                error=f"Command timed out after {timeout_seconds} seconds.",
                exit_code=None,
                data={
                    "command": command,
                    "timeout_seconds": timeout_seconds,
                    "stderr": self._preview(error.stderr, max_output_chars),
                    "timed_out": True,
                },
            )

        stdout = self._preview(completed.stdout, max_output_chars)
        stderr = self._preview(completed.stderr, max_output_chars)
        return ToolExecutionResult(
            tool="shell.run",
            ok=completed.returncode == 0,
            output=stdout,
            exit_code=completed.returncode,
            error=stderr or None,
            data={
                "command": command,
                "timeout_seconds": timeout_seconds,
                "stdout_truncated": len(completed.stdout) > max_output_chars,
                "stderr": stderr,
                "stderr_truncated": len(completed.stderr) > max_output_chars,
            },
        )

    def _preview(self, value: str | bytes | None, max_chars: int) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            value = value.decode(errors="replace")
        if len(value) <= max_chars:
            return value
        return value[:max_chars]
