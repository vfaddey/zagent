"""Runtime artifact reader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from zagent_launcher.application.dto import RunResultView, RunStateView, RunTraceLine, RunTraceView
from zagent_launcher.application.errors import (
    ArtifactNotFoundError,
    ArtifactParseError,
    ArtifactPathError,
)
from zagent_launcher.application.interfaces import RunSpecReader, RuntimeArtifactReader


class JsonRuntimeArtifactReader(RuntimeArtifactReader):
    _WORKSPACE_MOUNT = Path("/workspace")
    _DEFAULT_RUN_SPEC = Path(".zagent/run.yaml")
    _STATE_FILE = "state.json"
    _RESULT_FILE = "result.json"
    _SUMMARY_FILE = "summary.md"
    _TRACE_FILES = ("events.jsonl", "tools.jsonl", "chat.jsonl")

    def __init__(self, run_spec_reader: RunSpecReader) -> None:
        self._run_spec_reader = run_spec_reader

    def read_state(self, project_root: Path, run_id: str | None = None) -> RunStateView:
        run_dir, resolved_run_id = self._run_dir(project_root, run_id)
        state_file = run_dir / self._STATE_FILE
        state = self._read_json_object(state_file)

        return RunStateView(
            run_id=self._string(state, "run_id", default=resolved_run_id),
            status=self._string(state, "status"),
            phase=self._string(state, "phase"),
            started_at=self._optional_string(state, "started_at"),
            updated_at=self._optional_string(state, "updated_at"),
            last_message_index=self._optional_int(state, "last_message_index"),
            last_tool_call=self._optional_string(state, "last_tool_call"),
            artifacts=self._string_tuple(state.get("artifacts")),
            path=state_file,
        )

    def read_trace(self, project_root: Path, run_id: str | None = None) -> RunTraceView:
        run_dir, resolved_run_id = self._run_dir(project_root, run_id)
        if not run_dir.is_dir():
            raise ArtifactNotFoundError(run_dir)

        lines: list[RunTraceLine] = []
        for trace_file_name in self._TRACE_FILES:
            trace_file = run_dir / trace_file_name
            if not trace_file.exists():
                continue
            lines.extend(self._read_trace_file(trace_file))

        if not lines:
            raise ArtifactNotFoundError(run_dir)

        return RunTraceView(
            run_id=resolved_run_id,
            run_dir=run_dir,
            lines=tuple(sorted(lines, key=self._trace_sort_key)),
        )

    def read_result(self, project_root: Path, run_id: str | None = None) -> RunResultView:
        run_dir, resolved_run_id = self._run_dir(project_root, run_id)
        result_file = run_dir / self._RESULT_FILE
        summary_file = run_dir / self._SUMMARY_FILE
        result = self._read_json_object(result_file)

        return RunResultView(
            run_id=self._string(result, "run_id", default=resolved_run_id),
            status=self._string(result, "status"),
            summary=self._string(result, "summary"),
            final_message=self._string(result, "final_message"),
            artifacts=self._string_tuple(result.get("artifacts")),
            error=self._optional_string(result, "error"),
            path=result_file,
            summary_path=summary_file,
            raw=result,
        )

    def _run_dir(self, project_root: Path, run_id: str | None) -> tuple[Path, str]:
        normalized_project_root = project_root.expanduser().resolve(strict=False)
        run_spec = self._run_spec_reader.read(normalized_project_root / self._DEFAULT_RUN_SPEC)
        resolved_run_id = run_id or run_spec.run_id
        agent_env_dir = self._host_agent_env_dir(normalized_project_root, run_spec.agent_env_path)
        return agent_env_dir / "artifacts" / resolved_run_id, resolved_run_id

    def _host_agent_env_dir(self, project_root: Path, agent_env_path: str) -> Path:
        path = Path(agent_env_path).expanduser()
        if not path.is_absolute():
            return (project_root / path).resolve(strict=False)
        try:
            relative_path = path.relative_to(self._WORKSPACE_MOUNT)
        except ValueError as error:
            raise ArtifactPathError(path) from error
        return (project_root / relative_path).resolve(strict=False)

    def _read_json_object(self, path: Path) -> dict[str, object]:
        if not path.is_file():
            raise ArtifactNotFoundError(path)
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ArtifactParseError(path, str(error)) from error
        except OSError as error:
            raise ArtifactParseError(path, str(error)) from error

        if not isinstance(loaded, dict):
            raise ArtifactParseError(path, "top-level JSON value must be an object")

        return cast(dict[str, object], loaded)

    def _read_trace_file(self, path: Path) -> tuple[RunTraceLine, ...]:
        try:
            raw_lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise ArtifactParseError(path, str(error)) from error

        lines: list[RunTraceLine] = []
        for raw_line in raw_lines:
            line = raw_line.strip()
            if not line:
                continue
            lines.append(self._trace_line(path.name, line))
        return tuple(lines)

    def _trace_line(self, source: str, line: str) -> RunTraceLine:
        try:
            loaded = json.loads(line)
        except json.JSONDecodeError:
            return RunTraceLine(source=source, content=line)

        if not isinstance(loaded, dict):
            return RunTraceLine(source=source, content=line)

        record = cast(dict[str, Any], loaded)
        ts = self._optional_string(record, "ts")
        compact_json = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return RunTraceLine(source=source, content=compact_json, ts=ts)

    def _trace_sort_key(self, line: RunTraceLine) -> tuple[str, int]:
        try:
            source_index = self._TRACE_FILES.index(line.source)
        except ValueError:
            source_index = len(self._TRACE_FILES)
        return line.ts or "", source_index

    def _string(self, mapping: dict[str, object], key: str, default: str | None = None) -> str:
        value = mapping.get(key, default)
        if isinstance(value, str):
            return value
        raise ArtifactParseError(key, "expected string")

    def _optional_string(self, mapping: dict[str, object], key: str) -> str | None:
        value = mapping.get(key)
        if value is None or isinstance(value, str):
            return value
        raise ArtifactParseError(key, "expected string or null")

    def _optional_int(self, mapping: dict[str, object], key: str) -> int | None:
        value = mapping.get(key)
        if value is None or isinstance(value, int):
            return value
        raise ArtifactParseError(key, "expected integer or null")

    def _string_tuple(self, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(value)
        raise ArtifactParseError("artifacts", "expected list of strings")
