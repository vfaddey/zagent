from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_launcher.application.dto import WriteFileResult


class ProjectTemplateProvider(Protocol):
    """Provides template directories and files relative to .zagent."""

    def directories_for(self, template: str) -> tuple[str, ...]: ...

    def files_for(self, template: str) -> dict[str, str]: ...


class ProjectWriter(Protocol):
    """Filesystem writer port for project initialization."""

    def ensure_dir(self, path: Path) -> None: ...

    def write_file(self, path: Path, content: str, force: bool) -> WriteFileResult: ...
