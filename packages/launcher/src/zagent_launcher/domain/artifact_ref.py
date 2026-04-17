from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    name: str
    path: Path
    media_type: str = "application/octet-stream"
