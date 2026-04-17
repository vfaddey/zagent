"""Runtime tool registry."""

from __future__ import annotations

from zagent_runtime.application.use_cases.register_tools import RegisteredTools
from zagent_runtime.domain.tools import ToolSpec
from zagent_runtime.infrastructure.tools.base import ToolBackend, ToolDefinition
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.errors import DuplicateToolError, UnknownToolError


class ToolRegistry:
    def __init__(self, builtin_tools: BuiltinToolCatalog) -> None:
        self._builtin_tools = builtin_tools
        self._definitions: dict[str, ToolDefinition] = {}

    def register_builtin_tools(self, names: tuple[str, ...]) -> RegisteredTools:
        for definition in self._builtin_tools.resolve_many(names):
            self.register(definition)
        return RegisteredTools(specs=self.list_specs())

    def register(self, definition: ToolDefinition) -> None:
        name = definition.spec.name
        if name in self._definitions:
            raise DuplicateToolError(name)
        self._definitions[name] = definition

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._definitions[name]
        except KeyError as error:
            raise UnknownToolError(name) from error

    def list_specs(self) -> tuple[ToolSpec, ...]:
        return tuple(definition.spec for definition in self._definitions.values())

    def backend_names(self, backend: ToolBackend) -> tuple[str, ...]:
        return tuple(
            definition.backend_name
            for definition in self._definitions.values()
            if definition.backend is backend
        )
