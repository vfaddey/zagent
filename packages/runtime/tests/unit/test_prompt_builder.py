from __future__ import annotations

from pathlib import Path

import pytest
from zagent_runtime.application.dto.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.application.use_cases.build_prompt_context import BuildPromptContext
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.infrastructure.config.errors import ConfigFileNotFoundError
from zagent_runtime.infrastructure.prompts.loader import MarkdownPromptDocumentLoader
from zagent_runtime.infrastructure.prompts.prompt_builder import RuntimePromptBuilder


def test_prompt_context_indexes_rules_and_skills_without_inlining_bodies(tmp_path: Path) -> None:
    context = _context(tmp_path)
    _write_agent_env_files(tmp_path)

    prompt = BuildPromptContext(MarkdownPromptDocumentLoader())(context)

    assert "System prompt body." in prompt.system_message
    assert "Developer prompt body." in prompt.system_message
    assert "# You have rules:" in prompt.system_message
    assert "# You have skills:" in prompt.system_message
    assert (
        "- `.zagent/rules/global.md` - Keep Diffs Small: Keep changes focused."
        in prompt.system_message
    )
    assert (
        "- `.zagent/skills/python.md` - Python Testing: Python test workflow."
        in prompt.system_message
    )
    assert "Read a skill file before using that workflow." in prompt.system_message
    assert "Read a rule file before applying it" in prompt.system_message
    assert "This rule body must not be inlined." not in prompt.system_message
    assert "This skill body must not be inlined." not in prompt.system_message
    assert prompt.rules[0].title == "Keep Diffs Small"
    assert prompt.rules[0].description == "Keep changes focused."
    assert prompt.skills[0].path == ".zagent/skills/python.md"
    assert prompt.skills[0].description == "Python test workflow."


def test_runtime_prompt_builder_delegates_to_prompt_context_builder(tmp_path: Path) -> None:
    context = _context(tmp_path, prompt=None, prompt_file="prompts/task.md")
    _write_agent_env_files(tmp_path)
    builder = RuntimePromptBuilder(BuildPromptContext(MarkdownPromptDocumentLoader()))

    prompt = builder.build(context)

    assert prompt.task_message.startswith("# Task: Fix")
    assert "Task prompt body." in prompt.task_message


def test_task_prompt_file_must_exist(tmp_path: Path) -> None:
    context = _context(tmp_path, prompt=None, prompt_file="prompts/missing.md")
    _write_agent_env_files(tmp_path)
    builder = RuntimePromptBuilder(BuildPromptContext(MarkdownPromptDocumentLoader()))

    with pytest.raises(ConfigFileNotFoundError, match="Configuration file not found"):
        builder.build(context)


def _write_agent_env_files(workspace: Path) -> None:
    agent_env = workspace / ".zagent"
    (agent_env / "prompts").mkdir(parents=True)
    (agent_env / "rules").mkdir()
    (agent_env / "skills").mkdir()
    (agent_env / "prompts/system.md").write_text("System prompt body.", encoding="utf-8")
    (agent_env / "prompts/developer.md").write_text("Developer prompt body.", encoding="utf-8")
    (agent_env / "prompts/task.md").write_text("Task prompt body.", encoding="utf-8")
    (agent_env / "rules/global.md").write_text(
        "# Keep Diffs Small\n\nKeep changes focused.\n\nThis rule body must not be inlined.",
        encoding="utf-8",
    )
    (agent_env / "skills/python.md").write_text(
        "# Python Testing\n\nTitle: Python test workflow.\n\nThis skill body must not be inlined.",
        encoding="utf-8",
    )


def _context(
    workspace: Path,
    prompt: str | None = "Fix bug.",
    prompt_file: str | None = None,
) -> RuntimeContext:
    agent_env_dir = workspace / ".zagent"
    run_dir = agent_env_dir / "artifacts" / "run-1"
    return RuntimeContext(
        run_spec=RunSpec(
            run_id="run-1",
            mode=RunMode.FIX,
            task=TaskSpec(
                title="Fix",
                workspace=str(workspace),
                prompt=prompt,
                prompt_file=prompt_file,
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
            prompts=PromptFiles(
                system="prompts/system.md",
                developer="prompts/developer.md",
            ),
            rules=("rules/global.md",),
            skills=("skills/python.md",),
        ),
        paths=RuntimePaths(
            run_spec_file=agent_env_dir / "run.yaml",
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
