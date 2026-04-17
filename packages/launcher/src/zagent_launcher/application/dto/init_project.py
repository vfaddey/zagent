from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from zagent_launcher.domain import ProjectLayout

WriteStatus = Literal["created", "overwritten", "skipped"]


@dataclass(frozen=True, slots=True)
class InitProjectRequest:
    project_root: Path
    template: str = "basic"
    force: bool = False


@dataclass(frozen=True, slots=True)
class InitProjectResult:
    layout: ProjectLayout
    created: tuple[Path, ...]
    overwritten: tuple[Path, ...]
    skipped: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class WriteFileResult:
    path: Path
    status: WriteStatus
