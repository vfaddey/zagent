"""Collect run result use case."""

from __future__ import annotations

from typing import Protocol

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.domain.run import RunResult


class RunResultWriter(Protocol):
    def write(self, context: RuntimeContext, result: RunResult) -> None: ...


class CollectResult:
    def __init__(self, writer: RunResultWriter) -> None:
        self._writer = writer

    def __call__(self, context: RuntimeContext, result: RunResult) -> RunResult:
        self._writer.write(context, result)
        return result
