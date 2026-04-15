"""Load agent environment use case."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_runtime.domain.agent_env import AgentEnv


class AgentEnvLoader(Protocol):
    def load(self, path: Path) -> AgentEnv: ...


class LoadAgentEnv:
    def __init__(self, loader: AgentEnvLoader) -> None:
        self._loader = loader

    def __call__(self, path: Path) -> AgentEnv:
        return self._loader.load(path)
