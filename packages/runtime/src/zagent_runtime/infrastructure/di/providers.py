"""Dishka providers for runtime dependencies."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from zagent_runtime.application.bootstrap import BootstrapRun
from zagent_runtime.application.build_prompt_context import BuildPromptContext, PromptDocumentLoader
from zagent_runtime.application.build_runtime_context import (
    BuildRuntimeContext,
    RuntimePathResolver,
)
from zagent_runtime.application.collect_result import CollectResult, RunResultWriter
from zagent_runtime.application.create_agent import AgentFactory, CreateAgent, PromptBuilder
from zagent_runtime.application.execute_task import AgentBackendRunner, ExecuteTask
from zagent_runtime.application.load_agent_env import AgentEnvLoader, LoadAgentEnv
from zagent_runtime.application.load_run_spec import LoadRunSpec, RunSpecLoader
from zagent_runtime.application.observe_run import RunObserverPort
from zagent_runtime.application.register_mcp import McpServerLoader
from zagent_runtime.application.register_tools import RegisterTools, RuntimeToolRegistry
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentFactory
from zagent_runtime.infrastructure.ag2.model_adapter import Ag2ModelConfigBuilder
from zagent_runtime.infrastructure.ag2.run_executor import Ag2RunExecutor
from zagent_runtime.infrastructure.ag2.tool_adapter import Ag2RuntimeToolAdapter
from zagent_runtime.infrastructure.async_bridge import AsyncBridge
from zagent_runtime.infrastructure.config.loaders import (
    DirectoryAgentEnvLoader,
    YamlMcpServerLoader,
    YamlRunSpecLoader,
)
from zagent_runtime.infrastructure.config.path_resolver import DefaultRuntimePathResolver
from zagent_runtime.infrastructure.mcp.adapters import Ag2McpToolAdapter
from zagent_runtime.infrastructure.mcp.client_factory import Ag2McpToolkitFactory
from zagent_runtime.infrastructure.observability.chat_writer import ChatWriter
from zagent_runtime.infrastructure.observability.event_writer import EventWriter
from zagent_runtime.infrastructure.observability.json_serializer import JsonRecordSerializer
from zagent_runtime.infrastructure.observability.jsonl_writer import JsonlWriter
from zagent_runtime.infrastructure.observability.redactor import SecretRedactor
from zagent_runtime.infrastructure.observability.run_observer import RunObserver
from zagent_runtime.infrastructure.observability.state_store import StateStore
from zagent_runtime.infrastructure.observability.tool_writer import ToolTraceWriter
from zagent_runtime.infrastructure.prompts.loader import MarkdownPromptDocumentLoader
from zagent_runtime.infrastructure.prompts.prompt_builder import RuntimePromptBuilder
from zagent_runtime.infrastructure.runtime.dry_run import DryRunAgentFactory, DryRunExecutor
from zagent_runtime.infrastructure.runtime.result_writer import JsonRunResultWriter
from zagent_runtime.infrastructure.security.policies import FileSystemPolicy
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.builtin.files import FilesTool
from zagent_runtime.infrastructure.tools.builtin.shell import ShellTool
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


class RuntimeProvider(Provider):
    scope = Scope.APP

    run_spec_loader = provide(YamlRunSpecLoader, provides=RunSpecLoader)
    agent_env_loader = provide(DirectoryAgentEnvLoader, provides=AgentEnvLoader)
    mcp_server_loader = provide(YamlMcpServerLoader, provides=McpServerLoader)
    path_resolver = provide(DefaultRuntimePathResolver, provides=RuntimePathResolver)
    prompt_document_loader = provide(MarkdownPromptDocumentLoader, provides=PromptDocumentLoader)
    runtime_prompt_builder = provide(RuntimePromptBuilder)
    builtin_tool_catalog = provide(BuiltinToolCatalog)
    tool_registry = provide(ToolRegistry)
    filesystem_policy = provide(FileSystemPolicy)
    files_tool = provide(FilesTool)
    shell_tool = provide(ShellTool)
    async_bridge = provide(AsyncBridge)

    load_run_spec = provide(LoadRunSpec)
    load_agent_env = provide(LoadAgentEnv)
    build_prompt_context = provide(BuildPromptContext)
    build_runtime_context = provide(BuildRuntimeContext)
    create_agent = provide(CreateAgent)
    execute_task = provide(ExecuteTask)
    register_tools = provide(RegisterTools)
    collect_result = provide(CollectResult)
    bootstrap_run = provide(BootstrapRun)

    json_serializer = provide(JsonRecordSerializer)
    jsonl_writer = provide(JsonlWriter)
    chat_writer = provide(ChatWriter)
    event_writer = provide(EventWriter)
    tool_trace_writer = provide(ToolTraceWriter)
    state_store = provide(StateStore)
    run_observer = provide(RunObserver)
    run_result_writer = provide(JsonRunResultWriter)

    @provide
    def secret_redactor(self) -> SecretRedactor:
        return SecretRedactor()

    @provide
    def runtime_tool_registry(self, tool_registry: ToolRegistry) -> RuntimeToolRegistry:
        return tool_registry

    @provide
    def run_observer_port(self, run_observer: RunObserver) -> RunObserverPort:
        return run_observer

    @provide
    def result_writer(self, writer: JsonRunResultWriter) -> RunResultWriter:
        return writer

    @provide
    def prompt_builder(self, runtime_prompt_builder: RuntimePromptBuilder) -> PromptBuilder:
        return runtime_prompt_builder


class Ag2RuntimeProvider(Provider):
    scope = Scope.APP

    ag2_agent_factory = provide(Ag2AgentFactory)
    ag2_model_config_builder = provide(Ag2ModelConfigBuilder)
    ag2_run_executor = provide(Ag2RunExecutor)
    ag2_runtime_tool_adapter = provide(Ag2RuntimeToolAdapter)
    ag2_mcp_toolkit_factory = provide(Ag2McpToolkitFactory)
    ag2_mcp_tool_adapter = provide(Ag2McpToolAdapter)

    @provide
    def agent_factory(self, ag2_agent_factory: Ag2AgentFactory) -> AgentFactory:
        return ag2_agent_factory

    @provide
    def agent_backend_runner(self, ag2_run_executor: Ag2RunExecutor) -> AgentBackendRunner:
        return ag2_run_executor


class DryRunRuntimeProvider(Provider):
    scope = Scope.APP

    dry_run_agent_factory = provide(DryRunAgentFactory)
    dry_run_executor = provide(DryRunExecutor)

    @provide
    def agent_factory(self, factory: DryRunAgentFactory) -> AgentFactory:
        return factory

    @provide
    def agent_backend_runner(self, executor: DryRunExecutor) -> AgentBackendRunner:
        return executor
