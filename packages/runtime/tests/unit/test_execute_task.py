from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.application.use_cases.create_agent import AgentSession
from zagent_runtime.application.use_cases.execute_task import ExecuteTask
from zagent_runtime.application.use_cases.register_tools import RegisteredTools
from zagent_runtime.domain.run import (
    ResultStatus,
    RunResult,
)

from .factories import create_context


def test_execute_task_delegates_to_backend_runner(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    session = AgentSession(
        prompt=PromptContext(
            system_message="system",
            task_message="task",
            rules=(),
            skills=(),
        ),
        registered_tools=RegisteredTools(specs=()),
        backend=object(),
    )

    result = ExecuteTask(FakeRunner())(context, session)

    assert result.status is ResultStatus.SUCCESS
    assert result.final_message == "done\n\nZAGENT_DONE"


@dataclass(slots=True)
class FakeRunner:
    def run(
        self,
        context: RuntimeContext,
        session: AgentSession,
        continue_msg: str | None = None,
    ) -> RunResult:
        return RunResult(
            run_id=context.run_spec.run_id,
            status=ResultStatus.SUCCESS,
            summary=session.prompt.task_message,
            final_message="done\n\nZAGENT_DONE",
        )


