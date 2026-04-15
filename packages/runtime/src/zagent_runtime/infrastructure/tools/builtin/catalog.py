"""Built-in runtime tool catalog."""

from __future__ import annotations

from zagent_runtime.domain.tools import ToolKind, ToolSpec
from zagent_runtime.infrastructure.tools.base import ToolBackend, ToolDefinition
from zagent_runtime.infrastructure.tools.errors import UnknownToolError


class BuiltinToolCatalog:
    """Resolve configured built-in tool names to infrastructure definitions."""

    def __init__(self) -> None:
        self._definitions = self._build_definitions()
        self._index = self._build_index(self._definitions)

    def resolve(self, name: str) -> ToolDefinition:
        try:
            return self._index[name]
        except KeyError as error:
            raise UnknownToolError(name) from error

    def resolve_many(self, names: tuple[str, ...]) -> tuple[ToolDefinition, ...]:
        return tuple(self.resolve(name) for name in names)

    def list_specs(self) -> tuple[ToolSpec, ...]:
        return tuple(definition.spec for definition in self._definitions)

    def ag2_native_names(self, names: tuple[str, ...]) -> tuple[str, ...]:
        resolved = self.resolve_many(names)
        return tuple(
            definition.backend_name
            for definition in resolved
            if definition.backend is ToolBackend.AG2_NATIVE
        )

    def _build_definitions(self) -> tuple[ToolDefinition, ...]:
        return (
            ToolDefinition(
                spec=ToolSpec(
                    name="shell",
                    kind=ToolKind.BUILTIN,
                    description="Run shell commands through runtime-controlled tooling.",
                ),
                backend=ToolBackend.RUNTIME_NATIVE,
                backend_name="shell",
            ),
            ToolDefinition(
                spec=ToolSpec(
                    name="apply_patch",
                    kind=ToolKind.BUILTIN,
                    description="Apply structured file edits through the AG2 native patch tool.",
                ),
                backend=ToolBackend.AG2_NATIVE,
                backend_name="apply_patch",
                aliases=("patch",),
            ),
            ToolDefinition(
                spec=ToolSpec(
                    name="web_search",
                    kind=ToolKind.BUILTIN,
                    description="Search the web through the AG2 native web search tool.",
                ),
                backend=ToolBackend.AG2_NATIVE,
                backend_name="web_search",
            ),
            ToolDefinition(
                spec=ToolSpec(
                    name="image_generation",
                    kind=ToolKind.BUILTIN,
                    description="Generate images through the AG2 native image generation tool.",
                ),
                backend=ToolBackend.AG2_NATIVE,
                backend_name="image_generation",
            ),
            ToolDefinition(
                spec=ToolSpec(
                    name="git",
                    kind=ToolKind.BUILTIN,
                    description="Run git operations through runtime-controlled tooling.",
                ),
                backend=ToolBackend.RUNTIME_NATIVE,
                backend_name="git",
            ),
            ToolDefinition(
                spec=ToolSpec(
                    name="files",
                    kind=ToolKind.BUILTIN,
                    description="Read and write files through runtime-controlled tooling.",
                ),
                backend=ToolBackend.RUNTIME_NATIVE,
                backend_name="files",
            ),
        )

    def _build_index(
        self,
        definitions: tuple[ToolDefinition, ...],
    ) -> dict[str, ToolDefinition]:
        index: dict[str, ToolDefinition] = {}
        for definition in definitions:
            index[definition.spec.name] = definition
            for alias in definition.aliases:
                index[alias] = definition
        return index
