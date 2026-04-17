"""MCP server specifications."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class McpTransport(StrEnum):
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


@dataclass(frozen=True, slots=True)
class McpServerSpec:
    name: str
    transport: McpTransport
    enabled: bool = True
    command: str | None = None
    args: tuple[str, ...] = field(default_factory=tuple)
    url: str | None = None
    environment: Mapping[str, str] = field(default_factory=dict)
    environment_env: Mapping[str, str] = field(default_factory=dict)
    working_dir: str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    headers_env: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: float | None = None
    read_timeout_seconds: float | None = None
    use_tools: bool = True
    use_resources: bool = False


@dataclass(frozen=True, slots=True)
class McpServersConfig:
    servers: tuple[McpServerSpec, ...] = field(default_factory=tuple)

    def enabled_servers(self) -> tuple[McpServerSpec, ...]:
        return tuple(server for server in self.servers if server.enabled)
