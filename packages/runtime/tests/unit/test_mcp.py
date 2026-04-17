from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from autogen.tools import Tool
from zagent_runtime.application.dto.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.mcp import McpServerSpec, McpTransport
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.observability import ChatMessage, RunEvent
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RunState, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.domain.tools import ToolCallStatus, ToolEvent
from zagent_runtime.infrastructure.async_bridge import AsyncBridge
from zagent_runtime.infrastructure.config.loaders import YamlMcpServerLoader
from zagent_runtime.infrastructure.mcp.adapters import Ag2McpToolAdapter
from zagent_runtime.infrastructure.mcp.client_factory import (
    Ag2McpToolkitFactory,
    StreamableHttpSessionConfig,
)
from zagent_runtime.infrastructure.mcp.server_spec import resolve_env_mapping


def test_yaml_mcp_server_loader_parses_supported_transports(tmp_path: Path) -> None:
    config_file = tmp_path / "servers.yaml"
    config_file.write_text(
        """
servers:
  - name: filesystem
    transport: stdio
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - /workspace
  - name: docs
    transport: streamable-http
    url: http://mcp-docs:8080/mcp
    headers_env:
      Authorization: MCP_AUTH_HEADER
  - name: legacy-docs
    enabled: false
    transport: sse
    url: http://mcp-docs:8080/sse
""",
        encoding="utf-8",
    )

    config = YamlMcpServerLoader().load(config_file)

    assert [server.name for server in config.servers] == [
        "filesystem",
        "docs",
        "legacy-docs",
    ]
    assert config.servers[0].transport is McpTransport.STDIO
    assert config.servers[0].command == "npx"
    assert config.servers[1].transport is McpTransport.STREAMABLE_HTTP
    assert config.enabled_servers()[2 - 1].name == "docs"


def test_ag2_mcp_tool_adapter_registers_enabled_servers(tmp_path: Path) -> None:
    agent_env_dir = tmp_path / ".zagent"
    mcp_dir = agent_env_dir / "mcp"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "servers.yaml").write_text(
        """
servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
  - name: disabled
    enabled: false
    transport: sse
    url: http://example.test/sse
""",
        encoding="utf-8",
    )
    factory = FakeToolkitFactory()
    adapter = Ag2McpToolAdapter(
        server_loader=YamlMcpServerLoader(),
        toolkit_factory=factory,
        async_bridge=AsyncBridge(),
        observer=TraceObserver(),
    )
    assistant = object()
    executor = object()

    handles = adapter.register(
        context=_context(tmp_path),
        assistant=assistant,
        executor=executor,
    )

    assert [server.name for server in factory.created] == ["filesystem"]
    assert len(handles) == 1
    assert handles[0].registered == [(assistant, executor)]
    assert [tool.name for tool in handles[0].toolkit.tools] == ["lookup"]
    assert handles[0].toolkit.tools[0]._func_schema["function"]["parameters"] == {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }


def test_ag2_mcp_tool_adapter_skips_when_mcp_disabled(tmp_path: Path) -> None:
    factory = FakeToolkitFactory()
    adapter = Ag2McpToolAdapter(
        server_loader=YamlMcpServerLoader(),
        toolkit_factory=factory,
        async_bridge=AsyncBridge(),
        observer=TraceObserver(),
    )

    handles = adapter.register(
        context=_context(tmp_path, enable_mcp=False),
        assistant=object(),
        executor=object(),
    )

    assert handles == ()
    assert factory.created == []


def test_ag2_mcp_tool_adapter_traces_mcp_tool_calls(tmp_path: Path) -> None:
    agent_env_dir = tmp_path / ".zagent"
    mcp_dir = agent_env_dir / "mcp"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "servers.yaml").write_text(
        """
servers:
  - name: filesystem
    transport: stdio
    command: npx
""",
        encoding="utf-8",
    )
    observer = TraceObserver()
    adapter = Ag2McpToolAdapter(
        server_loader=YamlMcpServerLoader(),
        toolkit_factory=FakeToolkitFactory(),
        async_bridge=AsyncBridge(),
        observer=observer,
    )

    handles = adapter.register(
        context=_context(tmp_path),
        assistant=object(),
        executor=object(),
    )
    result = handles[0].toolkit.tools[0].func(query="books")

    assert result == "found books"
    assert [event.status for event in observer.tool_events] == [
        ToolCallStatus.STARTED,
        ToolCallStatus.FINISHED,
    ]
    assert observer.tool_events[0].tool == "mcp:filesystem.lookup"
    assert observer.tool_events[0].args == {"query": "books"}
    assert observer.tool_events[1].stdout == "found books"
    assert [event.event for event in observer.run_events] == [
        "mcp_server_connecting",
        "mcp_server_connected",
    ]


def test_streamable_http_session_config_is_built_from_domain_spec() -> None:
    config = Ag2McpToolkitFactory()._session_config(
        McpServerSpec(
            name="docs",
            transport=McpTransport.STREAMABLE_HTTP,
            url="http://example.test/mcp",
            timeout_seconds=2,
            read_timeout_seconds=10,
        )
    )

    assert isinstance(config, StreamableHttpSessionConfig)
    assert config.url == "http://example.test/mcp"
    assert config.timeout_seconds == 2
    assert config.read_timeout_seconds == 10


def test_resolve_env_mapping_reads_values_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "secret")

    resolved = resolve_env_mapping(
        direct={"X-Static": "value"},
        from_env={"Authorization": "MCP_TOKEN"},
    )

    assert resolved == {
        "X-Static": "value",
        "Authorization": "secret",
    }


@dataclass(slots=True)
class FakeHandle:
    server_name: str
    toolkit: Any
    registered: list[tuple[Any, Any]] = field(default_factory=list)
    closed: bool = False

    def register(self, assistant: Any, executor: Any) -> None:
        self.registered.append((assistant, executor))

    async def aclose(self) -> None:
        self.closed = True


@dataclass(slots=True)
class FakeToolkitFactory(Ag2McpToolkitFactory):
    created: list[McpServerSpec] = field(default_factory=list)

    async def create(self, server: McpServerSpec, context: RuntimeContext) -> FakeHandle:
        self.created.append(server)
        return FakeHandle(
            server_name=server.name,
            toolkit=FakeToolkit(),
        )


class FakeToolkit:
    def __init__(self) -> None:
        async def lookup(**arguments: Any) -> str:
            return f"found {arguments['query']}"

        self.toolkit: dict[str, Any] = {
            "lookup": Tool(
                name="lookup",
                description="Lookup data.",
                func_or_tool=lookup,
                parameters_json_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            )
        }

    @property
    def tools(self) -> list[Any]:
        return list(self.toolkit.values())

    def set_tool(self, tool: Any) -> None:
        self.toolkit[tool.name] = tool


@dataclass(slots=True)
class TraceObserver:
    tool_events: list[ToolEvent] = field(default_factory=list)
    run_events: list[RunEvent] = field(default_factory=list)

    def on_run_started(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_event(self, paths: RuntimePaths, event: RunEvent) -> None:
        self.run_events.append(event)

    def on_message(self, paths: RuntimePaths, message: ChatMessage) -> None:
        return None

    def on_tool_started(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self.tool_events.append(event)

    def on_tool_finished(self, paths: RuntimePaths, event: ToolEvent) -> None:
        self.tool_events.append(event)

    def on_phase_changed(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None

    def on_run_finished(self, paths: RuntimePaths, state: RunState, event: RunEvent) -> None:
        return None


def _context(workspace: Path, enable_mcp: bool = True) -> RuntimeContext:
    agent_env_dir = workspace / ".zagent"
    run_dir = agent_env_dir / "artifacts" / "run-1"
    return RuntimeContext(
        run_spec=RunSpec(
            run_id="run-1",
            mode=RunMode.TASK,
            task=TaskSpec(
                title="Task",
                workspace=str(workspace),
                prompt="Do work.",
            ),
            model=ModelSpec(
                provider=ModelProvider.OPENAI_COMPATIBLE,
                model="gpt-5",
                api_key_env="OPENAI_API_KEY",
            ),
            agent_env=AgentEnvRef(path=str(agent_env_dir)),
            runtime=RuntimeSpec(image="zagent-runtime:local", workdir=str(workspace)),
            tools=ToolsConfig(enable_mcp=enable_mcp),
            policy=PolicySpec(writable_paths=(str(workspace),)),
        ),
        agent_env=AgentEnv(
            name="test",
            prompts=PromptFiles(),
            mcp_servers_file="mcp/servers.yaml",
        ),
        paths=RuntimePaths(
            run_spec_file=workspace / "run.yaml",
            workspace=workspace,
            agent_env_dir=agent_env_dir,
            artifacts_root_dir=agent_env_dir / "artifacts",
            run_artifacts_dir=run_dir,
            state_file=run_dir / "state.json",
            chat_file=run_dir / "chat.jsonl",
            ag2_history_file=run_dir / "ag2_history.json",
            events_file=run_dir / "events.jsonl",
            tools_file=run_dir / "tools.jsonl",
            result_file=run_dir / "result.json",
            summary_file=run_dir / "summary.md",
        ),
    )
