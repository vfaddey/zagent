"""Register runtime tools use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from zagent_runtime.domain.run import RunSpec
from zagent_runtime.domain.tools import ToolSpec


@dataclass(frozen=True, slots=True)
class RegisteredTools:
    specs: tuple[ToolSpec, ...]


class RuntimeToolRegistry(Protocol):
    def register_builtin_tools(self, names: tuple[str, ...]) -> RegisteredTools: ...


class RegisterTools:
    def __init__(self, registry: RuntimeToolRegistry) -> None:
        self._registry = registry

    def __call__(self, run_spec: RunSpec) -> RegisteredTools:
        return self._registry.register_builtin_tools(run_spec.tools.builtin)
