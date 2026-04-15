"""Tool registry errors."""

from __future__ import annotations


class ToolError(Exception):
    """Base tool error."""


class UnknownToolError(ToolError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown tool: {name}")
        self.name = name


class DuplicateToolError(ToolError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Duplicate tool registration: {name}")
        self.name = name

