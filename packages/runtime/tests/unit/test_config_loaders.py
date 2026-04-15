from __future__ import annotations

from pathlib import Path

import pytest
from zagent_runtime.application.load_agent_env import LoadAgentEnv
from zagent_runtime.application.load_run_spec import LoadRunSpec
from zagent_runtime.domain.model import ModelProvider
from zagent_runtime.domain.run import RunMode
from zagent_runtime.infrastructure.config.errors import (
    ConfigFileNotFoundError,
    ConfigParseError,
)
from zagent_runtime.infrastructure.config.loaders import (
    YamlAgentEnvLoader,
    YamlRunSpecLoader,
)

ROOT = Path(__file__).resolve().parents[4]


def test_load_run_spec_from_example() -> None:
    run_spec = LoadRunSpec(YamlRunSpecLoader())(ROOT / "examples/run.fix.yaml")

    assert run_spec.run_id == "fix-example"
    assert run_spec.mode is RunMode.FIX
    assert run_spec.model.provider is ModelProvider.OPENAI_COMPATIBLE
    assert run_spec.runtime.max_turns == 20
    assert run_spec.runtime.final_marker == "ZAGENT_DONE"
    assert run_spec.tools.builtin == ("shell", "files", "git", "apply_patch")


def test_load_agent_env_from_example() -> None:
    agent_env = LoadAgentEnv(YamlAgentEnvLoader())(ROOT / "examples/agent-env/config.yaml")

    assert agent_env.name == "python-dev-env"
    assert agent_env.prompts.system == "prompts/system.md"
    assert agent_env.rules == ("rules/global.md", "rules/repo.md")
    assert agent_env.mcp_servers_file == "mcp/servers.yaml"


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
  description: Test
  workspace: /workspace
model:
  provider: openai_compatible
  model: gpt-5
  api_key_env: OPENAI_API_KEY
agent_env:
  path: /workspace/.agent
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
