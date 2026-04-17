"""JSON serialization for runtime trace records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class JsonRecordSerializer:
    """Convert domain objects to JSON-compatible values."""

    def to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            return self.to_jsonable(asdict(value))

        if isinstance(value, datetime):
            normalized = value
            if normalized.tzinfo is None:
                normalized = normalized.replace(tzinfo=UTC)
            return normalized.astimezone(UTC).isoformat().replace("+00:00", "Z")

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, Path):
            return str(value)

        if isinstance(value, dict):
            return {str(key): self.to_jsonable(item) for key, item in value.items()}

        if isinstance(value, tuple | list):
            return [self.to_jsonable(item) for item in value]

        return value
