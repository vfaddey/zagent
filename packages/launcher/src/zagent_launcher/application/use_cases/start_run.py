from __future__ import annotations

from zagent_launcher.application.interfaces import ContainerRunner
from zagent_launcher.domain import ContainerSpec, LaunchResult


class StartRun:
    def __init__(self, runner: ContainerRunner) -> None:
        self._runner = runner

    def __call__(self, spec: ContainerSpec) -> LaunchResult:
        return self._runner.run(spec)
