from __future__ import annotations

from zagent_runtime.application.bootstrap import BootstrapRun
from zagent_runtime.application.build_prompt_context import BuildPromptContext
from zagent_runtime.application.build_runtime_context import BuildRuntimeContext
from zagent_runtime.application.collect_result import CollectResult, RunResultWriter
from zagent_runtime.application.create_agent import CreateAgent
from zagent_runtime.application.execute_task import ExecuteTask
from zagent_runtime.application.load_agent_env import LoadAgentEnv
from zagent_runtime.application.load_run_spec import LoadRunSpec
from zagent_runtime.application.observe_run import RunObserverPort
from zagent_runtime.application.register_tools import RegisterTools
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentFactory
from zagent_runtime.infrastructure.ag2.model_adapter import Ag2ModelConfigBuilder
from zagent_runtime.infrastructure.ag2.run_executor import Ag2RunExecutor
from zagent_runtime.infrastructure.ag2.tool_adapter import Ag2RuntimeToolAdapter
from zagent_runtime.infrastructure.di.container import RuntimeContainerFactory
from zagent_runtime.infrastructure.mcp.adapters import Ag2McpToolAdapter
from zagent_runtime.infrastructure.mcp.client_factory import Ag2McpToolkitFactory
from zagent_runtime.infrastructure.observability.run_observer import RunObserver
from zagent_runtime.infrastructure.prompts.prompt_builder import RuntimePromptBuilder
from zagent_runtime.infrastructure.runtime.dry_run import DryRunAgentFactory, DryRunExecutor
from zagent_runtime.infrastructure.runtime.result_writer import JsonRunResultWriter


def test_runtime_container_resolves_ag2_application_services() -> None:
    container = RuntimeContainerFactory().create()

    assert container.get(BootstrapRun)
    assert container.get(LoadRunSpec)
    assert container.get(LoadAgentEnv)
    assert container.get(BuildPromptContext)
    assert container.get(BuildRuntimeContext)
    assert container.get(CreateAgent)
    assert container.get(ExecuteTask)
    assert container.get(RegisterTools)
    assert container.get(CollectResult)
    assert container.get(RunResultWriter)
    assert container.get(JsonRunResultWriter)
    assert container.get(RuntimePromptBuilder)
    assert container.get(Ag2AgentFactory)
    assert container.get(Ag2ModelConfigBuilder)
    assert container.get(Ag2RunExecutor)
    assert container.get(Ag2RuntimeToolAdapter)
    assert container.get(Ag2McpToolkitFactory)
    assert container.get(Ag2McpToolAdapter)
    assert container.get(RunObserver)
    assert container.get(RunObserverPort)


def test_runtime_container_resolves_dry_run_replacements() -> None:
    container = RuntimeContainerFactory().create_dry_run()

    assert container.get(BootstrapRun)
    assert container.get(DryRunAgentFactory)
    assert container.get(DryRunExecutor)
