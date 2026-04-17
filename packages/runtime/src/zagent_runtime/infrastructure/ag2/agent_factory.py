"""AG2 agent factory adapter."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from autogen import ConversableAgent, LLMConfig, register_function  # type: ignore[import-untyped]

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.infrastructure.ag2.model_adapter import Ag2ModelConfigBuilder
from zagent_runtime.infrastructure.ag2.tool_adapter import Ag2FunctionTool, Ag2RuntimeToolAdapter
from zagent_runtime.infrastructure.mcp.adapters import Ag2McpToolAdapter
from zagent_runtime.infrastructure.mcp.client_factory import Ag2McpToolkitHandle
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class Ag2AgentBundle:
    assistant: ConversableAgent
    executor: ConversableAgent
    llm_config: LLMConfig
    runtime_tools: tuple[Ag2FunctionTool, ...]
    mcp_toolkits: tuple[Ag2McpToolkitHandle, ...]


class Ag2AgentFactory:
    """Create AG2 agents from runtime context."""

    def __init__(
        self,
        model_config_builder: Ag2ModelConfigBuilder,
        runtime_tool_adapter: Ag2RuntimeToolAdapter,
        mcp_tool_adapter: Ag2McpToolAdapter,
        tool_registry: ToolRegistry,
    ) -> None:
        self._model_config_builder = model_config_builder
        self._runtime_tool_adapter = runtime_tool_adapter
        self._mcp_tool_adapter = mcp_tool_adapter
        self._tool_registry = tool_registry

    def create(
        self,
        context: RuntimeContext,
        prompt: PromptContext,
    ) -> Ag2AgentBundle:
        config_spec = self._model_config_builder.build(context, self._tool_registry)
        llm_config = LLMConfig(config_spec.config_list)
        runtime_tools = self._runtime_tool_adapter.build_tools(context, self._tool_registry)

        assistant = ConversableAgent(
            name="zagent_assistant",
            system_message=prompt.system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
            code_execution_config=False,
        )
        executor = ConversableAgent(
            name="zagent_runtime_executor",
            llm_config=False,
            human_input_mode="NEVER",
            code_execution_config=False,
            is_termination_msg=self._termination_check(context.run_spec.runtime.final_marker),
        )

        self._register_runtime_tools(
            assistant=assistant,
            executor=executor,
            runtime_tools=runtime_tools,
        )
        mcp_toolkits = self._mcp_tool_adapter.register(
            context=context,
            assistant=assistant,
            executor=executor,
        )

        return Ag2AgentBundle(
            assistant=assistant,
            executor=executor,
            llm_config=llm_config,
            runtime_tools=runtime_tools,
            mcp_toolkits=mcp_toolkits,
        )

    def _register_runtime_tools(
        self,
        assistant: ConversableAgent,
        executor: ConversableAgent,
        runtime_tools: tuple[Ag2FunctionTool, ...],
    ) -> None:
        for tool in runtime_tools:
            register_function(
                self._typed_function(tool),
                caller=assistant,
                executor=executor,
                name=tool.name,
                description=tool.description,
            )

    def _typed_function(self, tool: Ag2FunctionTool) -> Any:
        return tool.function

    def _termination_check(self, final_marker: str) -> Any:
        def is_termination_msg(message: object) -> bool:
            content = self._message_content(message)
            return final_marker in content

        return is_termination_msg

    def _message_content(self, message: object) -> str:
        if isinstance(message, Mapping):
            content = message.get("content")
            return self._stringify_content(content)

        content = getattr(message, "content", None)
        return self._stringify_content(content)

    def _stringify_content(self, content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(self._stringify_content(item) for item in content)
        if isinstance(content, Mapping):
            return "\n".join(self._stringify_content(value) for value in content.values())
        if content is None:
            return ""
        return str(content)
