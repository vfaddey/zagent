from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.observability import ChatMessage, RunEvent
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RunState, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.domain.tools import ToolCallStatus, ToolEvent
from zagent_runtime.infrastructure.ag2.model_adapter import Ag2ModelConfigBuilder
from zagent_runtime.infrastructure.ag2.tool_adapter import Ag2RuntimeToolAdapter
from zagent_runtime.infrastructure.security.policies import FileSystemPolicy
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.builtin.files import FilesTool
from zagent_runtime.infrastructure.tools.builtin.shell import ShellTool
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


def test_ag2_model_config_builder_includes_native_builtin_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    context = _context(tmp_path, builtin_tools=("apply_patch", "web_search"))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)

    config = Ag2ModelConfigBuilder().build(context, registry)

    assert config.config_list["api_type"] == "responses_v2"
    assert config.config_list["api_key"] == "test-key"
    assert config.config_list["built_in_tools"] == ["apply_patch", "web_search"]
    assert config.config_list["workspace_dir"] == str(tmp_path)


def test_ag2_model_config_builder_uses_openai_api_without_native_tools(tmp_path: Path) -> None:
    context = _context(tmp_path, builtin_tools=("files", "shell"))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)

    config = Ag2ModelConfigBuilder().build(context, registry)

    assert config.config_list["api_type"] == "openai"
    assert config.config_list["timeout"] == 120
    assert "built_in_tools" not in config.config_list


def test_ag2_runtime_tool_adapter_builds_runtime_native_tools(tmp_path: Path) -> None:
    context = _context(tmp_path, builtin_tools=("files", "shell"))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)
    adapter = Ag2RuntimeToolAdapter(
        files_tool=FilesTool(FileSystemPolicy()),
        shell_tool=ShellTool(),
        observer=TraceObserver(),
    )

    tools = adapter.build_tools(context, registry)

    assert [tool.name for tool in tools] == [
        "files_read_text",
        "files_write_text",
        "files_list_dir",
        "shell_run",
    ]


def test_ag2_runtime_files_tool_function_returns_json_result(tmp_path: Path) -> None:
    context = _context(tmp_path, builtin_tools=("files",))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)
    adapter = Ag2RuntimeToolAdapter(
        files_tool=FilesTool(FileSystemPolicy()),
        shell_tool=ShellTool(),
        observer=TraceObserver(),
    )
    tools = {tool.name: tool for tool in adapter.build_tools(context, registry)}

    write_result = json.loads(tools["files_write_text"](path="note.txt", content="hello"))
    read_result = json.loads(tools["files_read_text"](path="note.txt"))

    assert write_result["ok"] is True
    assert read_result["output"] == "hello"


def test_ag2_runtime_shell_tool_function_returns_json_result(tmp_path: Path) -> None:
    context = _context(tmp_path, builtin_tools=("shell",))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)
    adapter = Ag2RuntimeToolAdapter(
        files_tool=FilesTool(FileSystemPolicy()),
        shell_tool=ShellTool(),
        observer=TraceObserver(),
    )
    tools = {tool.name: tool for tool in adapter.build_tools(context, registry)}

    result = json.loads(tools["shell_run"](command="printf hello"))

    assert result["ok"] is True
    assert result["output"] == "hello"


def test_ag2_runtime_tool_adapter_traces_tool_calls(tmp_path: Path) -> None:
    context = _context(tmp_path, builtin_tools=("shell",))
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(context.run_spec.tools.builtin)
    observer = TraceObserver()
    adapter = Ag2RuntimeToolAdapter(
        files_tool=FilesTool(FileSystemPolicy()),
        shell_tool=ShellTool(),
        observer=observer,
    )
    tools = {tool.name: tool for tool in adapter.build_tools(context, registry)}

    tools["shell_run"](command="printf traced")

    assert [event.status for event in observer.tool_events] == [
        ToolCallStatus.STARTED,
        ToolCallStatus.FINISHED,
    ]
    assert observer.tool_events[0].tool == "shell_run"
    assert observer.tool_events[0].args["command"] == "printf traced"
    assert observer.tool_events[1].stdout == "traced"
    assert observer.tool_events[1].exit_code == 0


@dataclass(slots=True)
class TraceObserver:
    tool_events: list[ToolEvent] = field(default_factory=list)

    def on_run_started(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_event(self, paths: RuntimePaths, event: RunEvent) -> None:
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
    agent_env_dir = workspace / ".zagent"
    run_dir = agent_env_dir / "artifacts" / "run-1"
    return RuntimeContext(
        run_spec=RunSpec(
            run_id="run-1",
            mode=RunMode.FIX,
            task=TaskSpec(
                title="Fix",
                workspace=str(workspace),
                prompt="Fix",
            ),
            model=ModelSpec(
                provider=ModelProvider.OPENAI_COMPATIBLE,
                model="gpt-5",
                api_key_env="OPENAI_API_KEY",
                api_base="https://api.openai.com/v1",
                timeout_seconds=120,
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
