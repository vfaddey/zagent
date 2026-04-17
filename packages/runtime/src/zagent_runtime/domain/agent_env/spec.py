"""Agent environment specification."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AgentEnvRef:
    path: str


@dataclass(frozen=True, slots=True)
class PromptFiles:
    system: str | None = None
    developer: str | None = None


@dataclass(frozen=True, slots=True)
class AgentEnv:
    """Resolved agent environment configuration."""

    name: str
    prompts: PromptFiles
    rules: tuple[str, ...] = field(default_factory=tuple)
    skills: tuple[str, ...] = field(default_factory=tuple)
    mcp_servers_file: str | None = None
    extra_context_files: tuple[str, ...] = field(default_factory=tuple)
