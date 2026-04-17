from __future__ import annotations

from zagent_launcher.application import (
    CheckEnvironment,
    CollectRunResult,
    InitProject,
    PrepareRun,
    ReadRunState,
    ReadRunTrace,
    StartRun,
)
from zagent_launcher.infrastructure.di import LauncherContainerFactory


def test_launcher_dishka_container_resolves_core_use_cases() -> None:
    container = LauncherContainerFactory().create()
    try:
        assert container.get(InitProject)
        assert container.get(PrepareRun)
        assert container.get(StartRun)
        assert container.get(ReadRunState)
        assert container.get(ReadRunTrace)
        assert container.get(CollectRunResult)
        assert container.get(CheckEnvironment)
    finally:
        container.close()
