from __future__ import annotations

import pytest
from zagent_runtime.application.register_tools import RegisterTools
from zagent_runtime.domain.agent_env import AgentEnvRef
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.domain.tools import ToolKind
from zagent_runtime.infrastructure.tools.base import ToolBackend
from zagent_runtime.infrastructure.tools.builtin.catalog import BuiltinToolCatalog
from zagent_runtime.infrastructure.tools.errors import DuplicateToolError, UnknownToolError
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


def test_builtin_catalog_maps_runtime_names_to_ag2_native_names() -> None:
    catalog = BuiltinToolCatalog()

    assert catalog.ag2_native_names(("shell", "apply_patch", "web_search")) == (
        "apply_patch",
        "web_search",
    )
    assert catalog.ag2_native_names(("patch",)) == ("apply_patch",)


def test_builtin_catalog_keeps_runtime_native_tools_out_of_ag2_list() -> None:
    catalog = BuiltinToolCatalog()

    assert catalog.ag2_native_names(("files", "shell")) == ()


def test_builtin_catalog_rejects_unknown_tool() -> None:
    with pytest.raises(UnknownToolError):
        BuiltinToolCatalog().resolve("unknown")


def test_register_tools_use_case_registers_enabled_builtin_specs() -> None:
    registry = ToolRegistry(BuiltinToolCatalog())
    registered = RegisterTools(registry)(_run_spec_with_tools(("shell", "patch", "files")))

    assert [spec.name for spec in registered.specs] == ["shell", "apply_patch", "files"]
    assert all(spec.kind is ToolKind.BUILTIN for spec in registered.specs)
    assert registry.backend_names(ToolBackend.AG2_NATIVE) == ("apply_patch",)
    assert registry.backend_names(ToolBackend.RUNTIME_NATIVE) == ("shell", "files")


def test_tool_registry_rejects_duplicate_registration() -> None:
    registry = ToolRegistry(BuiltinToolCatalog())
    registry.register_builtin_tools(("shell",))

    with pytest.raises(DuplicateToolError):
        registry.register_builtin_tools(("shell",))


def _run_spec_with_tools(names: tuple[str, ...]) -> RunSpec:
    return RunSpec(
        run_id="run-1",
        mode=RunMode.FIX,
        task=TaskSpec(
            title="Fix",
            workspace="/workspace",
            prompt="Fix",
        ),
        model=ModelSpec(
            provider=ModelProvider.OPENAI_COMPATIBLE,
            model="gpt-5",
            api_key_env="OPENAI_API_KEY",
        ),
        agent_env=AgentEnvRef(path="/workspace/.zagent"),
        runtime=RuntimeSpec(image="zagent-runtime:local", workdir="/workspace"),
        tools=ToolsConfig(builtin=names),
        policy=PolicySpec(),
    )
