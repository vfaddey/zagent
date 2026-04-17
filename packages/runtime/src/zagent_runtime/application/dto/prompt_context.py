from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptDocumentRef:
    title: str
    path: str
    description: str


@dataclass(frozen=True, slots=True)
class PromptContext:
    system_message: str
    task_message: str
    rules: tuple[PromptDocumentRef, ...]
    skills: tuple[PromptDocumentRef, ...]
