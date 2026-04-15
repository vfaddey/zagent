"""Task specification model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """User-facing task definition for one run."""

    title: str
    description: str
    workspace: str

