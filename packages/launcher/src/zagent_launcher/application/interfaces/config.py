from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_launcher.application.dto import LauncherRunSpec


class RunSpecReader(Protocol):
    def read(self, path: Path) -> LauncherRunSpec: ...
