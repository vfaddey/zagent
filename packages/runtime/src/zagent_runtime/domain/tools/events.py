"""Tool trace event model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ToolCallStatus(StrEnum):
    """Tool call lifecycle status."""

    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ToolEvent:
    """Tool trace event."""

    ts: datetime
    tool: str
    status: ToolCallStatus
    args: dict[str, Any] = field(default_factory=dict)
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None

