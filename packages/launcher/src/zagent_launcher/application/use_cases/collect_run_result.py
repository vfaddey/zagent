from __future__ import annotations

from pathlib import Path

from zagent_launcher.application.dto import RunResultView
from zagent_launcher.application.interfaces import RuntimeArtifactReader


class CollectRunResult:
    def __init__(self, artifact_reader: RuntimeArtifactReader) -> None:
        self._artifact_reader = artifact_reader

    def __call__(self, project_root: Path, run_id: str | None = None) -> RunResultView:
        return self._artifact_reader.read_result(project_root=project_root, run_id=run_id)
