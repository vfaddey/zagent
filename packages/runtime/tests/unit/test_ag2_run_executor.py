from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zagent_runtime.application.create_agent import AgentSession
from zagent_runtime.application.prompt_context import PromptContext
from zagent_runtime.application.register_tools import RegisteredTools
from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import ResultStatus, RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentBundle
from zagent_runtime.infrastructure.ag2.run_executor import Ag2RunExecutor


def test_ag2_run_executor_passes_max_turns_and_adds_final_marker(tmp_path: Path) -> None:
    executor = FakeExecutor(
        response=FakeResponse(
            messages=[{"role": "assistant", "content": "I changed the file."}],
            summary="I changed the file.",
        )
    )
    session = _session(executor=executor)
    context = _context(tmp_path, max_turns=7, final_marker="DONE")

    result = Ag2RunExecutor().run(context, session)

    assert executor.calls[0]["max_turns"] == 7
    assert "finish your final response with `DONE`" in executor.calls[0]["message"]
    assert result.status is ResultStatus.SUCCESS
    assert result.summary == "I changed the file."
    assert result.final_message == "I changed the file.\n\nDONE"


def test_ag2_run_executor_preserves_existing_final_marker(tmp_path: Path) -> None:
    executor = FakeExecutor(
        response=FakeResponse(
            messages=[{"role": "assistant", "content": "Summary\n\nZAGENT_DONE"}],
            summary="Summary",
        )
    )
    session = _session(executor=executor)
    context = _context(tmp_path, max_turns=3, final_marker="ZAGENT_DONE")

    result = Ag2RunExecutor().run(context, session)

    assert result.final_message == "Summary\n\nZAGENT_DONE"


@dataclass(slots=True)
class FakeResponse:
    messages: list[dict[str, str]]
    summary: str
    processed: bool = False

    def process(self) -> None:
        self.processed = True


@dataclass(slots=True)
class FakeExecutor:
    response: FakeResponse
    calls: list[dict[str, Any]] = field(default_factory=list)

    def run(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self.response


def _session(executor: FakeExecutor) -> AgentSession:
    return AgentSession(
        prompt=PromptContext(
            system_message="system",
            task_message="Do the task.",
            rules=(),
            skills=(),
        ),
        registered_tools=RegisteredTools(specs=()),
        backend=Ag2AgentBundle(
            assistant=object(),
            executor=executor,
            llm_config=object(),
            runtime_tools=(),
        ),
    )


def _context(workspace: Path, max_turns: int, final_marker: str) -> RuntimeContext:
    agent_env_dir = workspace / ".agent"
    run_dir = agent_env_dir / "artifacts" / "run-1"
    return RuntimeContext(
        run_spec=RunSpec(
            run_id="run-1",
            mode=RunMode.FIX,
            task=TaskSpec(
                title="Fix",
                description="Fix bug.",
                workspace=str(workspace),
            ),
            model=ModelSpec(
                provider=ModelProvider.OPENAI_COMPATIBLE,
                model="gpt-5",
                api_key_env="OPENAI_API_KEY",
            ),
            agent_env=AgentEnvRef(path=str(agent_env_dir)),
            runtime=RuntimeSpec(
                image="zagent-runtime:local",
                workdir=str(workspace),
                max_turns=max_turns,
                final_marker=final_marker,
            ),
            tools=ToolsConfig(),
            policy=PolicySpec(writable_paths=(str(workspace),)),
        ),
        agent_env=AgentEnv(
            name="test",
            prompts=PromptFiles(),
        ),
        paths=RuntimePaths(
            run_spec_file=workspace / "run.yaml",
            workspace=workspace,
            agent_env_dir=agent_env_dir,
            agent_env_config_file=agent_env_dir / "config.yaml",
            artifacts_root_dir=agent_env_dir / "artifacts",
            run_artifacts_dir=run_dir,
            state_file=run_dir / "state.json",
            chat_file=run_dir / "chat.jsonl",
            events_file=run_dir / "events.jsonl",
            tools_file=run_dir / "tools.jsonl",
            result_file=run_dir / "result.json",
            summary_file=run_dir / "summary.md",
        ),
    )
