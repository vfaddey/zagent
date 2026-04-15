"""Event JSONL writer."""

from __future__ import annotations

from zagent_runtime.application.runtime_context import RuntimePaths
from zagent_runtime.domain.observability import RunEvent
from zagent_runtime.infrastructure.observability.jsonl_writer import JsonlWriter


class EventWriter:
    """Write runtime events to events.jsonl."""

    def __init__(self, writer: JsonlWriter) -> None:
        self._writer = writer

    def write(self, paths: RuntimePaths, event: RunEvent) -> None:
        self._writer.append(paths.events_file, event)
