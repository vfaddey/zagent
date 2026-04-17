from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MountSpec:
    host_path: Path
    container_path: str
    read_only: bool = False
