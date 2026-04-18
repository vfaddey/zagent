from __future__ import annotations

from typing import Protocol


class HostEnvironment(Protocol):
    def has(self, name: str) -> bool: ...
    def get(self, name: str) -> str | None: ...
