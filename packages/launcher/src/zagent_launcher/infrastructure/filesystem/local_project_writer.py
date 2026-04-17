"""Local filesystem writer for project initialization."""

from __future__ import annotations

from pathlib import Path

from zagent_launcher.application.dto import WriteFileResult, WriteStatus
from zagent_launcher.application.interfaces import ProjectWriter


class LocalProjectWriter(ProjectWriter):
    def ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def write_file(self, path: Path, content: str, force: bool) -> WriteFileResult:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            return WriteFileResult(path=path, status="skipped")

        status: WriteStatus = "overwritten" if path.exists() else "created"
        path.write_text(content, encoding="utf-8")
        return WriteFileResult(path=path, status=status)
