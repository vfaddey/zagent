from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from zagent_launcher.domain.mount_spec import MountSpec


@dataclass(frozen=True, slots=True)
class ContainerSpec:
    image: str
    command: tuple[str, ...]
    workdir: str = "/workspace"
    mounts: tuple[MountSpec, ...] = field(default_factory=tuple)
    env: Mapping[str, str] = field(default_factory=dict)
    remove: bool = True
    tty: bool = False
    network: str | None = None
