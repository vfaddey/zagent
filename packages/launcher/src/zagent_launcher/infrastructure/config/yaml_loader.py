"""Launcher YAML loader."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError
from yaml import YAMLError

from zagent_launcher.application.dto import LauncherRunSpec
from zagent_launcher.application.errors import RunSpecNotFoundError, RunSpecParseError
from zagent_launcher.application.interfaces import RunSpecReader


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class _ModelConfig(_StrictModel):
    api_key_env: str


class _RuntimeConfig(_StrictModel):
    image: str
    workdir: str = "/workspace"


class _AgentEnvConfig(_StrictModel):
    path: str = "/workspace/.zagent"


class _PolicyConfig(_StrictModel):
    network: str = "restricted"


class _RunSpecConfig(_StrictModel):
    run_id: str
    model: _ModelConfig
    runtime: _RuntimeConfig
    agent_env: _AgentEnvConfig = _AgentEnvConfig()
    policy: _PolicyConfig = _PolicyConfig()

    def to_launcher_spec(self) -> LauncherRunSpec:
        return LauncherRunSpec(
            run_id=self.run_id,
            runtime_image=self.runtime.image,
            runtime_workdir=self.runtime.workdir,
            model_api_key_env=self.model.api_key_env,
            policy_network=self.policy.network,
            agent_env_path=self.agent_env.path,
        )


class YamlRunSpecReader(RunSpecReader):
    """Read the launcher subset of .zagent/run.yaml."""

    def read(self, path: Path) -> LauncherRunSpec:
        if not path.is_file():
            raise RunSpecNotFoundError(path)

        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except YAMLError as error:
            raise RunSpecParseError(path, str(error)) from error
        except OSError as error:
            raise RunSpecParseError(path, str(error)) from error

        if not isinstance(loaded, dict):
            raise RunSpecParseError(path, "top-level YAML value must be a mapping")

        try:
            return _RunSpecConfig.model_validate(loaded).to_launcher_spec()
        except ValidationError as error:
            raise RunSpecParseError(path, str(error)) from error
