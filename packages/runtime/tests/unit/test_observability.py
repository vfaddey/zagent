from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from zagent_runtime.application.dto.runtime_context import RuntimePaths
from zagent_runtime.domain.observability import ChatMessage, ChatRole, RunEvent
from zagent_runtime.domain.run import RunPhase, RunState, RunStatus
from zagent_runtime.domain.tools import ToolCallStatus, ToolEvent
from zagent_runtime.infrastructure.observability.chat_writer import ChatWriter
from zagent_runtime.infrastructure.observability.event_writer import EventWriter
from zagent_runtime.infrastructure.observability.json_serializer import JsonRecordSerializer
from zagent_runtime.infrastructure.observability.jsonl_writer import JsonlWriter
from zagent_runtime.infrastructure.observability.redactor import SecretRedactor
from zagent_runtime.infrastructure.observability.run_observer import RunObserver
from zagent_runtime.infrastructure.observability.state_store import StateStore
from zagent_runtime.infrastructure.observability.tool_writer import ToolTraceWriter


def test_run_observer_writes_state_events_chat_and_tools(tmp_path: Path) -> None:
    paths = _runtime_paths(tmp_path)
    observer = _observer(secret_values=("topsecret",))
    now = datetime(2026, 4, 15, 10, 0, tzinfo=UTC)

    state = RunState(
        run_id="run-1",
        status=RunStatus.RUNNING,
        phase=RunPhase.CREATED,
        started_at=now,
        updated_at=now,
    )
    observer.on_run_started(
        paths=paths,
        state=state,
        event=RunEvent(ts=now, event="run_started", payload={"run_id": "run-1"}),
    )
    observer.on_message(
        paths=paths,
        message=ChatMessage(
            ts=now,
            role=ChatRole.ASSISTANT,
            content="Token value topsecret must not leak.",
        ),
    )
    observer.on_tool_started(
        paths=paths,
        event=ToolEvent(
            ts=now,
            tool="shell",
            status=ToolCallStatus.STARTED,
            args={"command": "echo topsecret", "api_key": "topsecret"},
        ),
    )

    assert json.loads(paths.state_file.read_text(encoding="utf-8"))["status"] == "running"
    assert _jsonl(paths.events_file)[0]["event"] == "run_started"
    assert _jsonl(paths.chat_file)[0]["content"] == "Token value [REDACTED] must not leak."
    assert _jsonl(paths.tools_file)[0]["args"]["api_key"] == "[REDACTED]"
    assert _jsonl(paths.tools_file)[0]["args"]["command"] == "echo [REDACTED]"


def test_state_store_replaces_previous_state(tmp_path: Path) -> None:
    paths = _runtime_paths(tmp_path)
    store = StateStore(JsonRecordSerializer(), SecretRedactor())
    now = datetime(2026, 4, 15, 10, 0, tzinfo=UTC)

    store.save(
        paths,
        RunState(
            run_id="run-1",
            status=RunStatus.RUNNING,
            phase=RunPhase.EXECUTING,
            started_at=now,
            updated_at=now,
        ),
    )
    store.save(
        paths,
        RunState(
            run_id="run-1",
            status=RunStatus.SUCCEEDED,
            phase=RunPhase.FINISHED,
            started_at=now,
            updated_at=now,
            artifacts=("result.json",),
        ),
    )

    state = json.loads(paths.state_file.read_text(encoding="utf-8"))

    assert state["status"] == "succeeded"
    assert state["artifacts"] == ["result.json"]


def _observer(secret_values: tuple[str, ...] = ()) -> RunObserver:
    redactor = SecretRedactor(secret_values=secret_values)
    serializer = JsonRecordSerializer()
    jsonl_writer = JsonlWriter(serializer=serializer, redactor=redactor)
    return RunObserver(
        chat_writer=ChatWriter(jsonl_writer),
        event_writer=EventWriter(jsonl_writer),
        tool_writer=ToolTraceWriter(jsonl_writer),
        state_store=StateStore(serializer=serializer, redactor=redactor),
    )


def _runtime_paths(root: Path) -> RuntimePaths:
    run_dir = root / ".zagent" / "artifacts" / "run-1"
    return RuntimePaths(
        run_spec_file=root / "run.yaml",
        workspace=root,
        agent_env_dir=root / ".zagent",
        artifacts_root_dir=root / ".zagent" / "artifacts",
        run_artifacts_dir=run_dir,
        state_file=run_dir / "state.json",
        chat_file=run_dir / "chat.jsonl",
        ag2_history_file=run_dir / "ag2_history.json",
        events_file=run_dir / "events.jsonl",
        tools_file=run_dir / "tools.jsonl",
        result_file=run_dir / "result.json",
        summary_file=run_dir / "summary.md",
    )


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
