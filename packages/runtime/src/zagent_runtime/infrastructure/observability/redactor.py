"""Secret redaction support."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SecretRedactor:
    _sensitive_key_parts = (
        "api_key",
        "apikey",
        "authorization",
        "credential",
        "password",
        "secret",
        "token",
    )

    def __init__(self, secret_values: tuple[str, ...] = ()) -> None:
        self._secret_values = tuple(value for value in secret_values if value)

    def redact_text(self, value: str) -> str:
        redacted = value
        for secret in self._secret_values:
            redacted = redacted.replace(secret, "[REDACTED]")
        return redacted

    def redact_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        return {key: self._redact_value(key=key, value=value) for key, value in data.items()}

    def _redact_value(self, key: str, value: Any) -> Any:
        if self._is_sensitive_key(key):
            return "[REDACTED]"

        if isinstance(value, str):
            return self.redact_text(value)

        if isinstance(value, Mapping):
            return self.redact_mapping(value)

        if isinstance(value, tuple | list):
            return [self._redact_value(key=key, value=item) for item in value]

        return value

    def _is_sensitive_key(self, key: str) -> bool:
        normalized = key.lower()
        return any(part in normalized for part in self._sensitive_key_parts)
