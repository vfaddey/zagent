from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LauncherRunSpec:
    run_id: str
    runtime_image: str
    runtime_workdir: str
    model_api_key_env: str
    policy_network: str
    agent_env_path: str = "/workspace/.zagent"
