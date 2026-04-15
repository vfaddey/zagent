from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.infrastructure.security.errors import PolicyViolationError
from zagent_runtime.infrastructure.security.policies import FileSystemPolicy
from zagent_runtime.infrastructure.tools.builtin.files import FilesTool
from zagent_runtime.infrastructure.tools.builtin.git import GitTool
from zagent_runtime.infrastructure.tools.builtin.shell import ShellTool


def test_files_tool_reads_writes_and_lists_workspace_files(tmp_path: Path) -> None:
    context = _context(tmp_path)
    tool = FilesTool(FileSystemPolicy())

    write_result = tool.write_text(context, "src/example.txt", "hello")
    read_result = tool.read_text(context, "src/example.txt")
    list_result = tool.list_dir(context, "src")

    assert write_result.ok
    assert read_result.output == "hello"
    assert list_result.data == {
        "path": str(tmp_path / "src"),
        "entries": ["example.txt"],
    }


def test_files_tool_blocks_writes_outside_writable_roots(tmp_path: Path) -> None:
    context = _context(tmp_path)
    tool = FilesTool(FileSystemPolicy())

    with pytest.raises(PolicyViolationError):
        tool.write_text(context, str(tmp_path.parent / "outside.txt"), "blocked")


def test_git_tool_status_and_diff(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("initial\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "Initial")
    (tmp_path / "README.md").write_text("changed\n", encoding="utf-8")

    context = _context(tmp_path)
    tool = GitTool()

    status = tool.status(context)
    diff = tool.diff(context)

    assert status.ok
    assert "M README.md" in status.output
    assert diff.ok
    assert "-initial" in diff.output
    assert "+changed" in diff.output


def test_shell_tool_runs_command_in_workspace(tmp_path: Path) -> None:
    context = _context(tmp_path)
    tool = ShellTool()

    result = tool.run(context, "pwd && printf done")

    assert result.ok
    assert str(tmp_path) in result.output
    assert result.output.endswith("done")


def _context(workspace: Path) -> RuntimeContext:
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
            ),
            agent_env=AgentEnvRef(path=str(agent_env_dir)),
            runtime=RuntimeSpec(image="zagent-runtime:local", workdir=str(workspace)),
            tools=ToolsConfig(builtin=("files", "git")),
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


def _git(workspace: Path, *args: str) -> None:
    subprocess.run(
        ("git", "-C", str(workspace), *args),
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
