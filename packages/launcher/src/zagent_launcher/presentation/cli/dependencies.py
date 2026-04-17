from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from dishka import Container

from zagent_launcher.infrastructure.di import LauncherContainerFactory


@contextmanager
def launcher_container() -> Iterator[Container]:
    container = LauncherContainerFactory().create()
    try:
        yield container
    finally:
        container.close()
