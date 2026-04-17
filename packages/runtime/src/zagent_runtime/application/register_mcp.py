"""MCP application ports."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_runtime.domain.mcp import McpServersConfig


class McpServerLoader(Protocol):
    def load(self, path: Path) -> McpServersConfig: ...
