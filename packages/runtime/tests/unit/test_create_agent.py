from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.application.use_cases.create_agent import CreateAgent
from zagent_runtime.application.use_cases.register_tools import RegisterTools
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.registry import ToolRegistry

from .factories import create_context


def test_create_agent_registers_tools_and_builds_backend(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    registry = ToolRegistry(BuiltinToolCatalog())
    prompt_builder = FakePromptBuilder()
    agent_factory = FakeAgentFactory()

    session = CreateAgent(
        register_tools=RegisterTools(registry),
        prompt_builder=prompt_builder,
        agent_factory=agent_factory,
    )(context)

    assert [tool.name for tool in session.registered_tools.specs] == ["files"]
    assert session.prompt.system_message == "system"
    assert session.backend == {"run_id": "run-1", "system": "system"}


@dataclass(slots=True)
class FakePromptBuilder:
    def build(self, context: RuntimeContext) -> PromptContext:
        return PromptContext(
            system_message="system",
            task_message=context.run_spec.task.prompt or "",
            rules=(),
            skills=(),
        )


@dataclass(slots=True)
class FakeAgentFactory:
    def create(self, context: RuntimeContext, prompt: PromptContext) -> object:
        return {
            "run_id": context.run_spec.run_id,
            "system": prompt.system_message,
        }


