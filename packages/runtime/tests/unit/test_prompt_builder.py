from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.build_prompt_context import BuildPromptContext
from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.infrastructure.prompts.loader import MarkdownPromptDocumentLoader
from zagent_runtime.infrastructure.prompts.prompt_builder import RuntimePromptBuilder


def test_prompt_context_indexes_rules_and_skills_without_inlining_bodies(tmp_path: Path) -> None:
    context = _context(tmp_path)
    _write_agent_env_files(tmp_path)

    prompt = BuildPromptContext(MarkdownPromptDocumentLoader())(context)

    assert "System prompt body." in prompt.system_message
    assert "Developer prompt body." in prompt.system_message
    assert "- Keep Diffs Small: `.agent/rules/global.md`" in prompt.system_message
    assert "- Python Testing: `.agent/skills/python.md`" in prompt.system_message
    assert "This rule body must not be inlined." not in prompt.system_message
    assert "This skill body must not be inlined." not in prompt.system_message
    assert prompt.rules[0].title == "Keep Diffs Small"
    assert prompt.skills[0].path == ".agent/skills/python.md"


def test_runtime_prompt_builder_delegates_to_prompt_context_builder(tmp_path: Path) -> None:
    context = _context(tmp_path)
    _write_agent_env_files(tmp_path)
    builder = RuntimePromptBuilder(BuildPromptContext(MarkdownPromptDocumentLoader()))

    prompt = builder.build(context)

    assert prompt.task_message.startswith("# Task: Fix")
    assert "Task prompt body." in prompt.task_message


def _write_agent_env_files(workspace: Path) -> None:
    agent_env = workspace / ".agent"
    (agent_env / "prompts").mkdir(parents=True)
    (agent_env / "rules").mkdir()
    (agent_env / "skills").mkdir()
    (agent_env / "prompts/system.md").write_text("System prompt body.", encoding="utf-8")
    (agent_env / "prompts/developer.md").write_text("Developer prompt body.", encoding="utf-8")
    (agent_env / "prompts/task.md").write_text("Task prompt body.", encoding="utf-8")
    (agent_env / "rules/global.md").write_text(
        "# Keep Diffs Small\n\nThis rule body must not be inlined.",
        encoding="utf-8",
    )
    (agent_env / "skills/python.md").write_text(
        "title: Python Testing\n\nThis skill body must not be inlined.",
        encoding="utf-8",
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
            prompts=PromptFiles(
                system="prompts/system.md",
                developer="prompts/developer.md",
                task="prompts/task.md",
            ),
            rules=("rules/global.md",),
            skills=("skills/python.md",),
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
