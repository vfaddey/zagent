"""Execute task use case."""

from __future__ import annotations

from typing import Protocol

from zagent_runtime.application.create_agent import AgentSession
from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.run import RunResult


class AgentBackendRunner(Protocol):
    def run(self, context: RuntimeContext, session: AgentSession) -> RunResult: ...


class ExecuteTask:
    def __init__(self, runner: AgentBackendRunner) -> None:
        self._runner = runner

    def __call__(self, context: RuntimeContext, session: AgentSession) -> RunResult:
        return self._runner.run(context, session)
