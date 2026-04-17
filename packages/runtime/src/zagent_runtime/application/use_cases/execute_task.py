"""Execute task use case."""

from __future__ import annotations

from typing import Protocol

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.application.use_cases.create_agent import AgentSession
from zagent_runtime.domain.run import RunResult


class AgentBackendRunner(Protocol):
    def run(
        self, context: RuntimeContext, session: AgentSession, continue_msg: str | None = None
    ) -> RunResult: ...


class ExecuteTask:
    def __init__(self, runner: AgentBackendRunner) -> None:
        self._runner = runner

    def __call__(
        self, context: RuntimeContext, session: AgentSession, continue_msg: str | None = None
    ) -> RunResult:
        return self._runner.run(context, session, continue_msg)
