"""Runtime Dishka container factory."""

from __future__ import annotations

from dishka import Container, make_container

from zagent_runtime.infrastructure.di.providers import (
    Ag2RuntimeProvider,
    DryRunRuntimeProvider,
    RuntimeProvider,
)


class RuntimeContainerFactory:
    def create(self) -> Container:
        return make_container(RuntimeProvider(), Ag2RuntimeProvider())

    def create_dry_run(self) -> Container:
        return make_container(RuntimeProvider(), DryRunRuntimeProvider())
