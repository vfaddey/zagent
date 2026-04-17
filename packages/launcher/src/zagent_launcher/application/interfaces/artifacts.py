from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_launcher.application.dto import RunResultView, RunStateView, RunTraceView


class RuntimeArtifactReader(Protocol):
    def read_state(self, project_root: Path, run_id: str | None = None) -> RunStateView: ...
    def read_trace(self, project_root: Path, run_id: str | None = None) -> RunTraceView: ...
    def read_result(self, project_root: Path, run_id: str | None = None) -> RunResultView: ...
