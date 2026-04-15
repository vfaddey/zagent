"""JSONL writer for runtime traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from zagent_runtime.infrastructure.observability.json_serializer import JsonRecordSerializer
from zagent_runtime.infrastructure.observability.redactor import SecretRedactor


class JsonlWriter:

    def __init__(self, serializer: JsonRecordSerializer, redactor: SecretRedactor) -> None:
        self._serializer = serializer
        self._redactor = redactor

    def append(self, path: Path, record: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        jsonable = self._serializer.to_jsonable(record)
        if isinstance(jsonable, dict):
            jsonable = self._redactor.redact_mapping(jsonable)
        line = json.dumps(jsonable, ensure_ascii=False, sort_keys=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(line)
            file.write("\n")

