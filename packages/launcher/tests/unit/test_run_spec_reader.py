from __future__ import annotations

from pathlib import Path

import pytest
from zagent_launcher.application.errors import RunSpecNotFoundError
from zagent_launcher.infrastructure.config import YamlRunSpecReader


def test_yaml_run_spec_reader_reads_launcher_subset(tmp_path: Path) -> None:
    path = tmp_path / "run.yaml"
    path.write_text(
        """
run_id: test-run
model:
  api_key_env: OPENAI_API_KEY
runtime:
  image: dummy-image:test
  workdir: /workspace
policy:
  network: disabled
""".lstrip(),
        encoding="utf-8",
    )

    run_spec = YamlRunSpecReader().read(path)

    assert run_spec.run_id == "test-run"
    assert run_spec.model_api_key_env == "OPENAI_API_KEY"
    assert run_spec.runtime_image == "dummy-image:test"
    assert run_spec.runtime_workdir == "/workspace"
    assert run_spec.policy_network == "disabled"
    assert run_spec.agent_env_path == "/workspace/.zagent"


def test_yaml_run_spec_reader_requires_file(tmp_path: Path) -> None:
    with pytest.raises(RunSpecNotFoundError):
        YamlRunSpecReader().read(tmp_path / "missing.yaml")
