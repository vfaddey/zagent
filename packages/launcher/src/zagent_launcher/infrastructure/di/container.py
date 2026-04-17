from __future__ import annotations

from dishka import Container, make_container

from zagent_launcher.infrastructure.di.providers import LauncherProvider


class LauncherContainerFactory:
    def create(self) -> Container:
        return make_container(LauncherProvider())
