"""Run event model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RunEvent:
    """High-level runtime event."""

    ts: datetime
    event: str
    payload: dict[str, Any] = field(default_factory=dict)
