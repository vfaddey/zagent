from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunRequest:
    project_root: Path
    run_spec: Path
    image_override: str | None = None
    dry_run: bool = False
    continue_message: str | None = None
