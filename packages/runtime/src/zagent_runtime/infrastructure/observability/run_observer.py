"""Runtime observer facade."""

from __future__ import annotations

from zagent_runtime.application.runtime_context import RuntimePaths
from zagent_runtime.domain.observability import ChatMessage, RunEvent
from zagent_runtime.domain.run import RunState
from zagent_runtime.domain.tools import ToolEvent
from zagent_runtime.infrastructure.observability.chat_writer import ChatWriter
from zagent_runtime.infrastructure.observability.event_writer import EventWriter
from zagent_runtime.infrastructure.observability.state_store import StateStore
from zagent_runtime.infrastructure.observability.tool_writer import ToolTraceWriter


class RunObserver:
    def __init__(
        self,
        chat_writer: ChatWriter,
        event_writer: EventWriter,
        tool_writer: ToolTraceWriter,
        state_store: StateStore,
    ) -> None:
        self._chat_writer = chat_writer
        self._event_writer = event_writer
        self._tool_writer = tool_writer
        self._state_store = state_store

    def on_run_started(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        self._state_store.save(paths, state)
        self._event_writer.write(paths, event)

    def on_event(self, paths: RuntimePaths, event: RunEvent) -> None:
        self._event_writer.write(paths, event)

    def on_message(self, paths: RuntimePaths, message: ChatMessage) -> None:
        self._chat_writer.write(paths, message)

    def on_tool_started(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self._tool_writer.write(paths, event)

    def on_tool_finished(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self._tool_writer.write(paths, event)

    def on_phase_changed(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        self._state_store.save(paths, state)
        self._event_writer.write(paths, event)

    def on_run_finished(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        self._state_store.save(paths, state)
        self._event_writer.write(paths, event)
