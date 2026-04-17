from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.application.use_cases.create_agent import CreateAgent
from zagent_runtime.application.use_cases.register_tools import RegisterTools
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


def test_create_agent_registers_tools_and_builds_backend(tmp_path: Path) -> None:
    context = _context(tmp_path)
    registry = ToolRegistry(BuiltinToolCatalog())
    prompt_builder = FakePromptBuilder()
    agent_factory = FakeAgentFactory()

    session = CreateAgent(
        register_tools=RegisterTools(registry),
        prompt_builder=prompt_builder,
        agent_factory=agent_factory,
    )(context)

    assert [tool.name for tool in session.registered_tools.specs] == ["files"]
    assert session.prompt.system_message == "system"
    assert session.backend == {"run_id": "run-1", "system": "system"}


@dataclass(slots=True)
class FakePromptBuilder:
    def build(self, context: RuntimeContext) -> PromptContext:
        return PromptContext(
            system_message="system",
            task_message=context.run_spec.task.prompt or "",
            rules=(),
            skills=(),
        )


@dataclass(slots=True)
class FakeAgentFactory:
    def create(self, context: RuntimeContext, prompt: PromptContext) -> object:
        return {
            "run_id": context.run_spec.run_id,
            "system": prompt.system_message,
        }


def _context(workspace: Path) -> RuntimeContext:
    agent_env_dir = workspace / ".zagent"
    run_dir = agent_env_dir / "artifacts" / "run-1"
    return RuntimeContext(
        run_spec=RunSpec(
            run_id="run-1",
            mode=RunMode.FIX,
            task=TaskSpec(
                title="Fix",
                workspace=str(workspace),
                prompt="Fix bug.",
            ),
            model=ModelSpec(
                provider=ModelProvider.OPENAI_COMPATIBLE,
                model="gpt-5",
                api_key_env="OPENAI_API_KEY",
            ),
            agent_env=AgentEnvRef(path=str(agent_env_dir)),
            runtime=RuntimeSpec(image="zagent-runtime:local", workdir=str(workspace)),
            tools=ToolsConfig(builtin=("files",)),
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
            artifacts_root_dir=agent_env_dir / "artifacts",
            run_artifacts_dir=run_dir,
            state_file=run_dir / "state.json",
            chat_file=run_dir / "chat.jsonl",
            ag2_history_file=run_dir / "ag2_history.json",
            events_file=run_dir / "events.jsonl",
            tools_file=run_dir / "tools.jsonl",
            result_file=run_dir / "result.json",
            summary_file=run_dir / "summary.md",
        ),
    )
