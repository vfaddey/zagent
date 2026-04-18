from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimePaths
from zagent_runtime.application.use_cases.create_agent import AgentSession
from zagent_runtime.application.use_cases.register_tools import RegisteredTools
from zagent_runtime.domain.observability import ChatMessage, RunEvent
from zagent_runtime.domain.run import (
    ResultStatus,
    RunState,
)
from zagent_runtime.domain.tools import ToolEvent
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentBundle
from zagent_runtime.infrastructure.ag2.run_executor import Ag2RunExecutor
from zagent_runtime.infrastructure.async_bridge import AsyncBridge

from .factories import create_context


def test_ag2_run_executor_passes_max_turns_and_adds_final_marker(tmp_path: Path) -> None:
    executor = FakeExecutor(
        response=FakeResponse(
            messages=[{"role": "assistant", "content": "I changed the file."}],
            summary="I changed the file.",
        )
    )
    session = _session(executor=executor)
    context = create_context(tmp_path, max_turns=7)

    result = Ag2RunExecutor(AsyncBridge(), NullObserver()).run(context, session)

    bundle = session.backend
    assert executor.calls[0]["max_turns"] == 7
    assert "final response must end with `ZAGENT_DONE`" in bundle.assistant.system_message
    assert "If you do not have enough context" in bundle.assistant.system_message
    assert (
        "A text-only answer is a valid final result only when it ends"
        in bundle.assistant.system_message
    )
    assert result.status is ResultStatus.SUCCESS
    assert result.summary == "I changed the file."
    assert result.final_message == "I changed the file.\n\nZAGENT_DONE"


def test_ag2_run_executor_preserves_existing_final_marker(tmp_path: Path) -> None:
    executor = FakeExecutor(
        response=FakeResponse(
            messages=[{"role": "assistant", "content": "Summary\n\nZAGENT_DONE"}],
            summary="Summary",
        )
    )
    session = _session(executor=executor)
    context = create_context(tmp_path, max_turns=3)

    result = Ag2RunExecutor(AsyncBridge(), NullObserver()).run(context, session)

    assert result.final_message == "Summary\n\nZAGENT_DONE"


def test_ag2_run_executor_closes_mcp_toolkits_and_emits_events(tmp_path: Path) -> None:
    mcp_toolkit = FakeMcpToolkit(server_name="filesystem")
    executor = FakeExecutor(
        response=FakeResponse(
            messages=[{"role": "assistant", "content": "Done"}],
            summary="Done",
        )
    )
    observer = NullObserver()
    session = _session(executor=executor, mcp_toolkits=(mcp_toolkit,))
    context = create_context(tmp_path, max_turns=3)

    Ag2RunExecutor(AsyncBridge(), observer).run(context, session)

    assert mcp_toolkit.closed is True
    assert [event.event for event in observer.run_events] == [
        "mcp_server_disconnecting",
        "mcp_server_disconnected",
    ]


@dataclass(slots=True)
class FakeResponse:
    messages: list[dict[str, str]]
    summary: str
    processed: bool = False

    def process(self) -> None:
        self.processed = True


@dataclass(slots=True, eq=False)
class FakeExecutor:
    response: FakeResponse
    calls: list[dict[str, Any]] = field(default_factory=list)
    chat_messages: dict[Any, list[dict[str, str]]] = field(default_factory=dict)

    def run(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self.response


@dataclass(slots=True, eq=False)
class FakeAssistant:
    system_message: str = "system"
    chat_messages: dict[Any, list[dict[str, str]]] = field(default_factory=dict)

    def update_system_message(self, message: str) -> None:
        self.system_message = message


@dataclass(slots=True)
class FakeMcpToolkit:
    server_name: str
    closed: bool = False

    async def aclose(self) -> None:
        self.closed = True


@dataclass(slots=True)
class NullObserver:
    run_events: list[RunEvent] = field(default_factory=list)

    def on_run_started(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_event(self, paths: RuntimePaths, event: RunEvent) -> None:
        self.run_events.append(event)

    def on_message(self, paths: RuntimePaths, message: ChatMessage) -> None:
        return None

    def on_tool_started(self, paths: RuntimePaths, event: ToolEvent) -> None:
        return None

    def on_tool_finished(self, paths: RuntimePaths, event: ToolEvent) -> None:
        return None

    def on_phase_changed(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_run_finished(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None


def _session(
    executor: FakeExecutor,
    mcp_toolkits: tuple[Any, ...] = (),
) -> AgentSession:
    return AgentSession(
        prompt=PromptContext(
            system_message="system",
            task_message="Do the task.",
            rules=(),
            skills=(),
        ),
        registered_tools=RegisteredTools(specs=()),
        backend=Ag2AgentBundle(
            assistant=FakeAssistant(),
            executor=executor,
            llm_config=object(),
            runtime_tools=(),
            mcp_toolkits=mcp_toolkits,
        ),
    )


