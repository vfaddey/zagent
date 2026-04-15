"""Tool specification model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToolKind(StrEnum):
    BUILTIN = "builtin"
    CUSTOM = "custom"
    MCP = "mcp"


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Runtime tool descriptor independent of AG2."""

    name: str
    kind: ToolKind
    description: str
    parameters_schema: dict[str, Any] = field(default_factory=dict)
