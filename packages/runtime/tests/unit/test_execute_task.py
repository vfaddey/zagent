from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zagent_runtime.application.create_agent import AgentSession
from zagent_runtime.application.execute_task import ExecuteTask
from zagent_runtime.application.prompt_context import PromptContext
from zagent_runtime.application.register_tools import RegisteredTools
from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import (
    ResultStatus,
    RunMode,
    RunResult,
    RunSpec,
    RuntimeSpec,
    ToolsConfig,
)
from zagent_runtime.domain.task import TaskSpec


def test_execute_task_delegates_to_backend_runner(tmp_path: Path) -> None:
    context = _context(tmp_path)
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
    def run(self, context: RuntimeContext, session: AgentSession) -> RunResult:
        return RunResult(
            run_id=context.run_spec.run_id,
            status=ResultStatus.SUCCESS,
            summary=session.prompt.task_message,
            final_message="done\n\nZAGENT_DONE",
        )


def _context(workspace: Path) -> RuntimeContext:
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
            runtime=RuntimeSpec(image="zagent-runtime:local", workdir=str(workspace)),
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

