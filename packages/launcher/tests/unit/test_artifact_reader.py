from __future__ import annotations

import json
from pathlib import Path

import pytest
from zagent_launcher.application.errors import ArtifactNotFoundError, ArtifactPathError
from zagent_launcher.infrastructure.artifacts import JsonRuntimeArtifactReader
from zagent_launcher.infrastructure.config import YamlRunSpecReader


def test_artifact_reader_reads_state_from_default_run_id(tmp_path: Path) -> None:
    _write_run_spec(tmp_path, run_id="run-1")
    run_dir = tmp_path / ".zagent/artifacts/run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "status": "running",
                "phase": "executing",
                "started_at": "2026-04-17T10:00:00Z",
                "updated_at": "2026-04-17T10:00:01Z",
                "last_message_index": 3,
                "last_tool_call": "shell",
                "artifacts": ["result.json"],
            }
        ),
        encoding="utf-8",
    )

    state = JsonRuntimeArtifactReader(YamlRunSpecReader()).read_state(tmp_path)

    assert state.run_id == "run-1"
    assert state.status == "running"
    assert state.phase == "executing"
    assert state.last_message_index == 3
    assert state.last_tool_call == "shell"
    assert state.artifacts == ("result.json",)


def test_artifact_reader_reads_result_by_explicit_run_id(tmp_path: Path) -> None:
    _write_run_spec(tmp_path, run_id="run-1")
    run_dir = tmp_path / ".zagent/artifacts/run-2"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "run_id": "run-2",
                "status": "success",
                "summary": "done",
                "final_message": "done\n\nZAGENT_DONE",
                "artifacts": ["result.json", "summary.md"],
                "error": None,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text("done", encoding="utf-8")

    result = JsonRuntimeArtifactReader(YamlRunSpecReader()).read_result(tmp_path, "run-2")

    assert result.run_id == "run-2"
    assert result.status == "success"
    assert result.summary == "done"
    assert result.final_message == "done\n\nZAGENT_DONE"
    assert result.artifacts == ("result.json", "summary.md")
    assert result.error is None


def test_artifact_reader_reads_and_sorts_trace_lines(tmp_path: Path) -> None:
    _write_run_spec(tmp_path, run_id="run-1")
    run_dir = tmp_path / ".zagent/artifacts/run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        '{"ts":"2026-04-17T10:00:02Z","event":"run_finished"}\n',
        encoding="utf-8",
    )
    (run_dir / "chat.jsonl").write_text(
        '{"ts":"2026-04-17T10:00:01Z","role":"assistant","content":"hello"}\n',
        encoding="utf-8",
    )

    trace = JsonRuntimeArtifactReader(YamlRunSpecReader()).read_trace(tmp_path)

    assert [line.source for line in trace.lines] == ["chat.jsonl", "events.jsonl"]
    assert '"role":"assistant"' in trace.lines[0].content
    assert '"event":"run_finished"' in trace.lines[1].content


def test_artifact_reader_uses_agent_env_path_from_run_spec(tmp_path: Path) -> None:
    _write_run_spec(tmp_path, run_id="run-1", agent_env_path="/workspace/custom-agent")
    run_dir = tmp_path / "custom-agent/artifacts/run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "state.json").write_text(
        json.dumps({"run_id": "run-1", "status": "succeeded", "phase": "finished"}),
        encoding="utf-8",
    )

    state = JsonRuntimeArtifactReader(YamlRunSpecReader()).read_state(tmp_path)

    assert state.path == run_dir / "state.json"


def test_artifact_reader_rejects_agent_env_path_outside_workspace(tmp_path: Path) -> None:
    _write_run_spec(tmp_path, run_id="run-1", agent_env_path="/tmp/.zagent")

    with pytest.raises(ArtifactPathError):
        JsonRuntimeArtifactReader(YamlRunSpecReader()).read_state(tmp_path)


def test_artifact_reader_reports_missing_artifact(tmp_path: Path) -> None:
    _write_run_spec(tmp_path, run_id="run-1")

    with pytest.raises(ArtifactNotFoundError):
        JsonRuntimeArtifactReader(YamlRunSpecReader()).read_state(tmp_path)


def _write_run_spec(
    project_root: Path,
    *,
    run_id: str,
    agent_env_path: str = "/workspace/.zagent",
) -> None:
    run_spec = project_root / ".zagent/run.yaml"
    run_spec.parent.mkdir(parents=True, exist_ok=True)
    run_spec.write_text(
        f"""
run_id: {run_id}
agent_env:
  path: {agent_env_path}
model:
  api_key_env: OPENAI_API_KEY
runtime:
  image: dummy-image:test
  workdir: /workspace
policy:
  network: restricted
""".lstrip(),
        encoding="utf-8",
    )
