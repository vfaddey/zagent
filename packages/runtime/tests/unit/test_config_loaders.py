from __future__ import annotations

from pathlib import Path

import pytest
from zagent_runtime.application.use_cases.load_agent_env import LoadAgentEnv
from zagent_runtime.application.use_cases.load_run_spec import LoadRunSpec
from zagent_runtime.domain.model import ModelProvider
from zagent_runtime.domain.run import RunMode
from zagent_runtime.infrastructure.config.errors import (
    ConfigDirectoryNotFoundError,
    ConfigFileNotFoundError,
    ConfigParseError,
)
from zagent_runtime.infrastructure.config.loaders import (
    DirectoryAgentEnvLoader,
    YamlRunSpecLoader,
)


def test_load_run_spec_from_file(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: python-bugfix-smoke
mode: fix
task:
  title: Test
  prompt_file: prompts/task.md
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
runtime:
  image: zagent-runtime:local
  workdir: /workspace
  max_turns: 40
tools:
  builtin:
    - shell
    - files
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    run_spec = LoadRunSpec(YamlRunSpecLoader())(path)

    assert run_spec.run_id == "python-bugfix-smoke"
    assert run_spec.mode is RunMode.FIX
    assert run_spec.model.provider is ModelProvider.OPENAI_COMPATIBLE
    assert run_spec.runtime.max_turns == 40
    assert run_spec.runtime.final_marker == "ZAGENT_DONE"
    assert run_spec.task.prompt_file == "prompts/task.md"
    assert run_spec.tools.builtin == ("shell", "files")


def test_load_agent_env_from_directory(tmp_path: Path) -> None:
    env_dir = tmp_path / ".zagent"
    env_dir.mkdir()
    (env_dir / "name.txt").write_text("zagent-env\n")

    prompts_dir = env_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "system.md").touch()

    rules_dir = env_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / "global.md").touch()
    (rules_dir / "research.md").touch()

    skills_dir = env_dir / "skills"
    skills_dir.mkdir()
    (skills_dir / "research.md").touch()

    mcp_dir = env_dir / "mcp"
    mcp_dir.mkdir()
    (mcp_dir / "servers.yaml").touch()

    agent_env = LoadAgentEnv(DirectoryAgentEnvLoader())(env_dir)

    assert agent_env.name == "zagent-env"
    assert agent_env.prompts.system == "prompts/system.md"
    assert agent_env.rules == ("rules/global.md", "rules/research.md")
    assert agent_env.skills == ("skills/research.md",)
    assert agent_env.mcp_servers_file == "mcp/servers.yaml"


def test_run_spec_defaults_agent_env_path_when_omitted(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: default-env
mode: task
task:
  title: Test
  prompt: Test
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
runtime:
  image: zagent-runtime:local
  workdir: /workspace
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    run_spec = LoadRunSpec(YamlRunSpecLoader())(path)

    assert run_spec.agent_env.path == ".zagent"


def test_missing_agent_env_directory_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigDirectoryNotFoundError, match="Configuration directory not found"):
        LoadAgentEnv(DirectoryAgentEnvLoader())(tmp_path / ".zagent")


def test_missing_config_file_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigFileNotFoundError):
        LoadRunSpec(YamlRunSpecLoader())(tmp_path / "missing.yaml")


def test_unknown_run_spec_field_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: broken
mode: fix
unknown: true
task:
  title: Test
  prompt: Test
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
agent_env:
  path: /workspace/.zagent
runtime:
  image: zagent-runtime:local
  workdir: /workspace
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigParseError):
        LoadRunSpec(YamlRunSpecLoader())(path)


def test_task_requires_exactly_one_prompt_source(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: broken
mode: task
task:
  title: Test
  prompt: Inline
  prompt_file: prompts/task.md
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
runtime:
  image: zagent-runtime:local
  workdir: /workspace
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigParseError):
        LoadRunSpec(YamlRunSpecLoader())(path)


def test_task_requires_prompt_source(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: broken
mode: task
task:
  title: Test
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
runtime:
  image: zagent-runtime:local
  workdir: /workspace
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigParseError):
        LoadRunSpec(YamlRunSpecLoader())(path)


def test_runtime_final_marker_field_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: broken
mode: fix
task:
  title: Test
  prompt: Test
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
agent_env:
  path: /workspace/.zagent
runtime:
  image: zagent-runtime:local
  workdir: /workspace
  final_marker: DONE
tools: {}
policy: {}
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigParseError):
        LoadRunSpec(YamlRunSpecLoader())(path)
