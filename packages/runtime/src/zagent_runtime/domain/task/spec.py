"""Task specification model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """User-facing task definition for one run."""

    title: str
    workspace: str
    prompt: str | None = None
    prompt_file: str | None = None
