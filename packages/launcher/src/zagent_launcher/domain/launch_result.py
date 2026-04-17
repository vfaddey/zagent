from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LaunchResult:
    exit_code: int
    message: str
    run_id: str | None = None
