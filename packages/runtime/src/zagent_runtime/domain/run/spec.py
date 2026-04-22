"""Run specification aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from zagent_runtime.domain.agent_env.spec import AgentEnvRef
from zagent_runtime.domain.model.spec import ModelSpec
from zagent_runtime.domain.policy.spec import PolicySpec
from zagent_runtime.domain.task.spec import TaskSpec

FINAL_MARKER = "ZAGENT_DONE"


class RunMode(StrEnum):
    FIX = "fix"
    RESEARCH = "research"
    TASK = "task"


@dataclass(frozen=True, slots=True)
class RuntimeSpec:
    """Runtime container settings from run.yaml."""

    image: str
    workdir: str
    max_turns: int = 20
    env: tuple[RuntimeEnvVar, ...] = field(default_factory=tuple)

    @property
    def final_marker(self) -> str:
        return FINAL_MARKER


@dataclass(frozen=True, slots=True)
class RuntimeEnvVar:
    name: str
    default: str | None = None


@dataclass(frozen=True, slots=True)
class ToolsConfig:
    """Tool enablement settings for one run."""

    builtin: tuple[str, ...] = field(default_factory=tuple)
    custom: tuple[str, ...] = field(default_factory=tuple)
    enable_mcp: bool = False


@dataclass(frozen=True, slots=True)
class RunSpec:
    run_id: str
    mode: RunMode
    task: TaskSpec
    model: ModelSpec
    agent_env: AgentEnvRef
    runtime: RuntimeSpec
    tools: ToolsConfig
    policy: PolicySpec
