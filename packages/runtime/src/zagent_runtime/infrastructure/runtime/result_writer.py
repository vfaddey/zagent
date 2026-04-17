"""Runtime result artifact writer."""

from __future__ import annotations

import json

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.domain.run import RunResult
from zagent_runtime.infrastructure.observability.json_serializer import JsonRecordSerializer
from zagent_runtime.infrastructure.observability.redactor import SecretRedactor


class JsonRunResultWriter:
    def __init__(self, serializer: JsonRecordSerializer, redactor: SecretRedactor) -> None:
        self._serializer = serializer
        self._redactor = redactor

    def write(self, context: RuntimeContext, result: RunResult) -> None:
        context.paths.run_artifacts_dir.mkdir(parents=True, exist_ok=True)
        jsonable = self._serializer.to_jsonable(result)
        if isinstance(jsonable, dict):
            jsonable = self._redactor.redact_mapping(jsonable)

        context.paths.result_file.write_text(
            json.dumps(jsonable, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        context.paths.summary_file.write_text(result.summary, encoding="utf-8")
