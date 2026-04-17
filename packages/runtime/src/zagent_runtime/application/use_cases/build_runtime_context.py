"""Build runtime context use case."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_runtime.application.dto.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.application.use_cases.load_agent_env import AgentEnvLoader
from zagent_runtime.application.use_cases.load_run_spec import RunSpecLoader
from zagent_runtime.domain.run import RunSpec


class RuntimePathResolver(Protocol):
    def resolve(self, run_spec_file: Path, run_spec: RunSpec) -> RuntimePaths: ...


class BuildRuntimeContext:
    def __init__(
        self,
        run_spec_loader: RunSpecLoader,
        agent_env_loader: AgentEnvLoader,
        path_resolver: RuntimePathResolver,
    ) -> None:
        self._run_spec_loader = run_spec_loader
        self._agent_env_loader = agent_env_loader
        self._path_resolver = path_resolver

    def __call__(self, run_spec_file: Path) -> RuntimeContext:
        run_spec = self._run_spec_loader.load(run_spec_file)
        paths = self._path_resolver.resolve(run_spec_file, run_spec)
        agent_env = self._agent_env_loader.load(paths.agent_env_dir)

        return RuntimeContext(
            run_spec=run_spec,
            agent_env=agent_env,
            paths=paths,
        )
