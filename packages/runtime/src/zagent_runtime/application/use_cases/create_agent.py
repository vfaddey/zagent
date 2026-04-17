"""Create runtime agent use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.application.use_cases.register_tools import RegisteredTools, RegisterTools


class PromptBuilder(Protocol):
    def build(self, context: RuntimeContext) -> PromptContext: ...


class AgentFactory(Protocol):
    def create(self, context: RuntimeContext, prompt: PromptContext) -> object: ...


@dataclass(frozen=True, slots=True)
class AgentSession:
    prompt: PromptContext
    registered_tools: RegisteredTools
    backend: object


class CreateAgent:
    def __init__(
        self,
        register_tools: RegisterTools,
        prompt_builder: PromptBuilder,
        agent_factory: AgentFactory,
    ) -> None:
        self._register_tools = register_tools
        self._prompt_builder = prompt_builder
        self._agent_factory = agent_factory

    def __call__(self, context: RuntimeContext) -> AgentSession:
        registered_tools = self._register_tools(context.run_spec)
        prompt = self._prompt_builder.build(context)
        backend = self._agent_factory.create(context, prompt)

        return AgentSession(
            prompt=prompt,
            registered_tools=registered_tools,
            backend=backend,
        )
