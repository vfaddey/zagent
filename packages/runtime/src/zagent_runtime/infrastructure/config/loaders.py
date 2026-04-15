"""YAML-backed runtime configuration loaders."""

from __future__ import annotations

from pathlib import Path

from zagent_runtime.domain.agent_env import AgentEnv
from zagent_runtime.domain.run import RunSpec
from zagent_runtime.infrastructure.config.dto import AgentEnvConfig, RunSpecConfig
from zagent_runtime.infrastructure.config.yaml_loader import load_config_model


class YamlRunSpecLoader:
    def load(self, path: Path) -> RunSpec:
        return load_config_model(path, RunSpecConfig).to_domain()


class YamlAgentEnvLoader:
    def load(self, path: Path) -> AgentEnv:
        return load_config_model(path, AgentEnvConfig).to_domain()
