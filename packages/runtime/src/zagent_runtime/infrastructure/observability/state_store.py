"""Run state store."""

from __future__ import annotations

import json
from pathlib import Path

from zagent_runtime.application.runtime_context import RuntimePaths
from zagent_runtime.domain.run import RunState
from zagent_runtime.infrastructure.observability.json_serializer import JsonRecordSerializer
from zagent_runtime.infrastructure.observability.redactor import SecretRedactor


class StateStore:

    def __init__(self, serializer: JsonRecordSerializer, redactor: SecretRedactor) -> None:
        self._serializer = serializer
        self._redactor = redactor

    def save(self, paths: RuntimePaths, state: RunState) -> None:
        paths.state_file.parent.mkdir(parents=True, exist_ok=True)
        jsonable = self._serializer.to_jsonable(state)
        if isinstance(jsonable, dict):
            jsonable = self._redactor.redact_mapping(jsonable)

        temp_file = self._temp_file_for(paths.state_file)
        temp_file.write_text(
            json.dumps(jsonable, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_file.replace(paths.state_file)

    def _temp_file_for(self, path: Path) -> Path:
        return path.with_name(f".{path.name}.tmp")
