"""YAML-backed runtime configuration loaders."""

from __future__ import annotations

from pathlib import Path

from zagent_runtime.domain.agent_env import AgentEnv, PromptFiles
from zagent_runtime.domain.mcp import McpServersConfig
from zagent_runtime.domain.run import RunSpec
from zagent_runtime.infrastructure.config.dto import (
    McpServersConfigDto,
    RunSpecConfig,
)
from zagent_runtime.infrastructure.config.errors import ConfigDirectoryNotFoundError
from zagent_runtime.infrastructure.config.yaml_loader import load_config_model


class YamlRunSpecLoader:
    def load(self, path: Path) -> RunSpec:
        return load_config_model(path, RunSpecConfig).to_domain()


class DirectoryAgentEnvLoader:
    def load(self, path: Path) -> AgentEnv:
        env_dir = path.expanduser().resolve(strict=False)
        if not env_dir.is_dir():
            raise ConfigDirectoryNotFoundError(env_dir)

        return AgentEnv(
            name="zagent-env",
            prompts=PromptFiles(
                system=self._optional_relative_file(env_dir, "prompts/system.md"),
                developer=self._optional_relative_file(env_dir, "prompts/developer.md"),
            ),
            rules=self._markdown_files(env_dir, "rules"),
            skills=self._markdown_files(env_dir, "skills"),
            mcp_servers_file=self._optional_relative_file(env_dir, "mcp/servers.yaml"),
            extra_context_files=self._regular_files(env_dir, "files"),
        )

    def _optional_relative_file(self, env_dir: Path, relative_path: str) -> str | None:
        path = env_dir / relative_path
        if path.is_file():
            return relative_path
        return None

    def _markdown_files(self, env_dir: Path, relative_dir: str) -> tuple[str, ...]:
        root = env_dir / relative_dir
        if not root.is_dir():
            return ()
        return tuple(self._relative_path(env_dir, path) for path in sorted(root.rglob("*.md")))

    def _regular_files(self, env_dir: Path, relative_dir: str) -> tuple[str, ...]:
        root = env_dir / relative_dir
        if not root.is_dir():
            return ()
        return tuple(
            self._relative_path(env_dir, path)
            for path in sorted(root.rglob("*"))
            if path.is_file()
        )

    def _relative_path(self, env_dir: Path, path: Path) -> str:
        return path.relative_to(env_dir).as_posix()


class YamlMcpServerLoader:
    def load(self, path: Path) -> McpServersConfig:
        return load_config_model(path, McpServersConfigDto).to_domain()
