"""Runtime context assembled before agent execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zagent_runtime.domain.agent_env import AgentEnv
from zagent_runtime.domain.run import RunSpec


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    run_spec_file: Path
    workspace: Path
    agent_env_dir: Path
    agent_env_config_file: Path
    artifacts_root_dir: Path
    run_artifacts_dir: Path
    state_file: Path
    chat_file: Path
    events_file: Path
    tools_file: Path
    result_file: Path
    summary_file: Path


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    run_spec: RunSpec
    agent_env: AgentEnv
    paths: RuntimePaths

