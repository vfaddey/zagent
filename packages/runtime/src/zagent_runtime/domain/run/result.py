"""Run result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ResultStatus(StrEnum):
    """Final result status."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELED = "canceled"


@dataclass(frozen=True, slots=True)
class RunResult:
    """Final run output."""

    run_id: str
    status: ResultStatus
    summary: str
    final_message: str
    artifacts: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
