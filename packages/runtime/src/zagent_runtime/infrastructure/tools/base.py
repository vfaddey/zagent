"""Base runtime tool contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from zagent_runtime.domain.tools import ToolSpec


class ToolBackend(StrEnum):
    """Infrastructure execution backend for a runtime tool."""

    AG2_NATIVE = "ag2_native"
    RUNTIME_NATIVE = "runtime_native"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Infrastructure tool definition."""

    spec: ToolSpec
    backend: ToolBackend
    backend_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolExecutionResult:
    """Result returned by runtime-native tools."""

    tool: str
    ok: bool
    output: str = ""
    data: dict[str, Any] | None = None
    exit_code: int | None = None
    error: str | None = None
