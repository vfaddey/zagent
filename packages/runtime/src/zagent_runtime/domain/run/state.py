"""Run state model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class RunStatus(StrEnum):
    """Lifecycle status of a runtime run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class RunPhase(StrEnum):
    """Coarse runtime phase for live state."""

    CREATED = "created"
    LOADING_CONFIG = "loading_config"
    INITIALIZING_AGENT = "initializing_agent"
    EXECUTING = "executing"
    COLLECTING_RESULT = "collecting_result"
    FINISHED = "finished"


@dataclass(frozen=True, slots=True)
class RunState:
    """Serializable run state snapshot."""

    run_id: str
    status: RunStatus
    phase: RunPhase
    started_at: datetime
    updated_at: datetime
    last_message_index: int | None = None
    last_tool_call: str | None = None
    artifacts: tuple[str, ...] = field(default_factory=tuple)

