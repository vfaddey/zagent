from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.build_runtime_context import BuildRuntimeContext
from zagent_runtime.infrastructure.config.loaders import YamlAgentEnvLoader, YamlRunSpecLoader
from zagent_runtime.infrastructure.config.path_resolver import DefaultRuntimePathResolver


def test_build_runtime_context_resolves_agent_env_and_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    agent_env_dir = workspace / ".agent"
    agent_env_dir.mkdir(parents=True)
    (agent_env_dir / "config.yaml").write_text(
        """
name: test-env
prompts:
  system: prompts/system.md
rules:
  - rules/global.md
""".lstrip(),
        encoding="utf-8",
    )

    run_spec_file = tmp_path / "run.yaml"
    run_spec_file.write_text(
        f"""
run_id: fix-123
mode: fix
task:
  title: Fix test
  description: Fix test
  workspace: {workspace}
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
agent_env:
  path: .agent
runtime:
  image: zagent-runtime:local
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
        agent_env_loader=YamlAgentEnvLoader(),
        path_resolver=DefaultRuntimePathResolver(),
    )(run_spec_file)

    assert context.run_spec.run_id == "fix-123"
    assert context.agent_env.name == "test-env"
    assert context.paths.workspace == workspace.resolve()
    assert context.paths.agent_env_config_file == (agent_env_dir / "config.yaml").resolve()
    assert context.paths.run_artifacts_dir == (agent_env_dir / "artifacts/fix-123").resolve()
    assert context.paths.state_file.name == "state.json"


def test_build_runtime_context_resolves_relative_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "relative-workspace"
    agent_env_dir = workspace / ".agent"
    agent_env_dir.mkdir(parents=True)
    (agent_env_dir / "config.yaml").write_text("name: relative-env\n", encoding="utf-8")

    run_spec_file = tmp_path / "run.yaml"
    run_spec_file.write_text(
        """
run_id: research-123
mode: research
task:
  title: Research test
  description: Research test
  workspace: relative-workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
agent_env:
  path: .agent
runtime:
  image: zagent-runtime:local
  workdir: /workspace
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    context = BuildRuntimeContext(
        run_spec_loader=YamlRunSpecLoader(),
        agent_env_loader=YamlAgentEnvLoader(),
        path_resolver=DefaultRuntimePathResolver(),
    )(run_spec_file)

    assert context.paths.workspace == workspace.resolve()
    assert context.paths.agent_env_dir == agent_env_dir.resolve()
