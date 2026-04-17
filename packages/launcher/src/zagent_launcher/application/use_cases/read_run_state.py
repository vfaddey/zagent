from __future__ import annotations

from pathlib import Path

from zagent_launcher.application.dto import RunStateView
from zagent_launcher.application.interfaces import RuntimeArtifactReader


class ReadRunState:
    def __init__(self, artifact_reader: RuntimeArtifactReader) -> None:
        self._artifact_reader = artifact_reader

    def __call__(self, project_root: Path, run_id: str | None = None) -> RunStateView:
        return self._artifact_reader.read_state(project_root=project_root, run_id=run_id)
