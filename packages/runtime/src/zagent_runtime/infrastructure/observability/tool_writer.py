"""Tool trace JSONL writer."""

from __future__ import annotations

from zagent_runtime.application.runtime_context import RuntimePaths
from zagent_runtime.domain.tools import ToolEvent
from zagent_runtime.infrastructure.observability.jsonl_writer import JsonlWriter


class ToolTraceWriter:
    def __init__(self, writer: JsonlWriter) -> None:
        self._writer = writer

    def write(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self._writer.append(paths.tools_file, event)
