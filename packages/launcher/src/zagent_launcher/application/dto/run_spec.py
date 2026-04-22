from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LauncherRuntimeEnvVar:
    name: str
    default: str | None = None


@dataclass(frozen=True, slots=True)
class LauncherRunSpec:
    run_id: str
    runtime_image: str
    runtime_workdir: str
    model_api_key_env: str
    policy_network: str
    agent_env_path: str = "/workspace/.zagent"
    runtime_env: tuple[LauncherRuntimeEnvVar, ...] = field(default_factory=tuple)
