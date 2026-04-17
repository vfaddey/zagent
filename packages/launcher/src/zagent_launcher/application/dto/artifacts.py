from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunStateView:
    run_id: str
    status: str
    phase: str
    started_at: str | None
    updated_at: str | None
    last_message_index: int | None
    last_tool_call: str | None
    artifacts: tuple[str, ...]
    path: Path


@dataclass(frozen=True, slots=True)
class RunTraceLine:
    source: str
    content: str
    ts: str | None = None


@dataclass(frozen=True, slots=True)
class RunTraceView:
    run_id: str
    run_dir: Path
    lines: tuple[RunTraceLine, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RunResultView:
    run_id: str
    status: str
    summary: str
    final_message: str
    artifacts: tuple[str, ...]
    error: str | None
    path: Path
    summary_path: Path
    raw: dict[str, object]
