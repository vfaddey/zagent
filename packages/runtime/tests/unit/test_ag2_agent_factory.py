from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from zagent_runtime.application.prompt_context import PromptContext
from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.observability import ChatMessage, RunEvent
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RunState, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.domain.tools import ToolEvent
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentFactory
from zagent_runtime.infrastructure.ag2.model_adapter import Ag2ModelConfigBuilder
from zagent_runtime.infrastructure.ag2.tool_adapter import Ag2RuntimeToolAdapter
from zagent_runtime.infrastructure.security.policies import FileSystemPolicy
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.builtin.files import FilesTool
from zagent_runtime.infrastructure.tools.builtin.git import GitTool
from zagent_runtime.infrastructure.tools.builtin.shell import ShellTool
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


def test_ag2_agent_factory_creates_bundle_with_runtime_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    context = _context(tmp_path, builtin_tools=("files", "git"))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)
    factory = Ag2AgentFactory(
        model_config_builder=Ag2ModelConfigBuilder(),
        runtime_tool_adapter=Ag2RuntimeToolAdapter(
            files_tool=FilesTool(FileSystemPolicy()),
            git_tool=GitTool(),
            shell_tool=ShellTool(),
            observer=TraceObserver(),
        ),
        tool_registry=registry,
    )

    bundle = factory.create(
        context=context,
        prompt=_prompt(),
    )

    assert bundle.assistant.name == "zagent_assistant"
    assert bundle.executor.name == "zagent_runtime_executor"
    assert bundle.executor._is_termination_msg({"content": "done\n\nZAGENT_DONE"})
    assert not bundle.executor._is_termination_msg({"content": "still working"})
    assert [tool.name for tool in bundle.runtime_tools] == [
        "files_read_text",
        "files_write_text",
        "files_list_dir",
        "git_status",
        "git_diff",
    ]


def test_ag2_agent_factory_creates_bundle_with_ag2_native_tools_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    context = _context(tmp_path, builtin_tools=("apply_patch", "web_search"))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)
    factory = Ag2AgentFactory(
        model_config_builder=Ag2ModelConfigBuilder(),
        runtime_tool_adapter=Ag2RuntimeToolAdapter(
            files_tool=FilesTool(FileSystemPolicy()),
            git_tool=GitTool(),
            shell_tool=ShellTool(),
            observer=TraceObserver(),
        ),
        tool_registry=registry,
    )

    bundle = factory.create(
        context=context,
        prompt=_prompt(),
    )

    assert bundle.runtime_tools == ()


def _prompt() -> PromptContext:
    return PromptContext(
        system_message="You are a runtime agent.",
        task_message="Do the task.",
        rules=(),
        skills=(),
    )


@dataclass(slots=True)
class TraceObserver:
    tool_events: list[ToolEvent] = field(default_factory=list)

    def on_run_started(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_message(self, paths: RuntimePaths, message: ChatMessage) -> None:
        return None

    def on_tool_started(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self.tool_events.append(event)

    def on_tool_finished(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self.tool_events.append(event)

    def on_phase_changed(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_run_finished(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None


def _context(workspace: Path, builtin_tools: tuple[str, ...]) -> RuntimeContext:
    agent_env_dir = workspace / ".agent"
    run_dir = agent_env_dir / "artifacts" / "run-1"
    return RuntimeContext(
        run_spec=RunSpec(
            run_id="run-1",
            mode=RunMode.FIX,
            task=TaskSpec(
                title="Fix",
                description="Fix",
                workspace=str(workspace),
            ),
            model=ModelSpec(
                provider=ModelProvider.OPENAI_COMPATIBLE,
                model="gpt-5",
                api_key_env="OPENAI_API_KEY",
                api_base="https://api.openai.com/v1",
            ),
            agent_env=AgentEnvRef(path=str(agent_env_dir)),
            runtime=RuntimeSpec(image="zagent-runtime:local", workdir=str(workspace)),
            tools=ToolsConfig(builtin=builtin_tools),
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
