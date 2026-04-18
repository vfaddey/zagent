from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.use_cases.build_runtime_context import BuildRuntimeContext
from zagent_runtime.infrastructure.config.loaders import DirectoryAgentEnvLoader, YamlRunSpecLoader
from zagent_runtime.infrastructure.config.path_resolver import DefaultRuntimePathResolver


def test_build_runtime_context_resolves_agent_env_and_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    agent_env_dir = workspace / ".zagent"
    (agent_env_dir / "prompts").mkdir(parents=True)
    (agent_env_dir / "rules").mkdir()
    (agent_env_dir / "prompts/system.md").write_text("System prompt.", encoding="utf-8")
    (agent_env_dir / "rules/global.md").write_text("# Global Rule\n", encoding="utf-8")

    run_spec_file = agent_env_dir / "run.yaml"
    run_spec_file.write_text(
        f"""
run_id: fix-123
mode: fix
task:
  title: Fix test
  prompt: Fix test
  workspace: {workspace}
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
runtime:
  image: ghcr.io/vfaddey/zagent-runtime:latest
  workdir: /workspace
tools:
  builtin:
    - shell
policy:
  writable_paths:
    - /workspace
""".lstrip(),
        encoding="utf-8",
    )

    context = BuildRuntimeContext(
        run_spec_loader=YamlRunSpecLoader(),
        agent_env_loader=DirectoryAgentEnvLoader(),
        path_resolver=DefaultRuntimePathResolver(),
    )(run_spec_file)

    assert context.run_spec.run_id == "fix-123"
    assert context.agent_env.name == "zagent-env"
    assert context.agent_env.prompts.system == "prompts/system.md"
    assert context.agent_env.rules == ("rules/global.md",)
    assert context.paths.workspace == workspace.resolve()
    assert context.paths.run_artifacts_dir == (agent_env_dir / "artifacts/fix-123").resolve()
    assert context.paths.state_file.name == "state.json"


def test_build_runtime_context_resolves_relative_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "relative-workspace"
    agent_env_dir = workspace / ".zagent"
    agent_env_dir.mkdir(parents=True)

    run_spec_file = workspace / ".zagent" / "run.yaml"
    run_spec_file.write_text(
        """
run_id: research-123
mode: research
task:
  title: Research test
  prompt: Research test
  workspace: ..
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
runtime:
  image: ghcr.io/vfaddey/zagent-runtime:latest
  workdir: /workspace
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    context = BuildRuntimeContext(
        run_spec_loader=YamlRunSpecLoader(),
        agent_env_loader=DirectoryAgentEnvLoader(),
        path_resolver=DefaultRuntimePathResolver(),
    )(run_spec_file)

    assert context.paths.workspace == workspace.resolve()
    assert context.paths.agent_env_dir == agent_env_dir.resolve()
