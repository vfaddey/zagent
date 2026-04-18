from __future__ import annotations

from zagent_runtime.domain.agent_env import AgentEnvRef
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.domain.tools import ToolKind, ToolSpec


def test_runtime_run_spec_entity_can_be_composed() -> None:
    spec = RunSpec(
        run_id="fix-123",
        mode=RunMode.FIX,
        task=TaskSpec(
            title="Fix pagination",
            workspace="/workspace",
            prompt="Fix pagination on reports page.",
        ),
        model=ModelSpec(
            provider=ModelProvider.OPENAI_COMPATIBLE,
            model="gpt-5",
            api_key_env="OPENAI_API_KEY",
            api_base="https://api.openai.com/v1",
        ),
        agent_env=AgentEnvRef(path="/workspace/.zagent"),
        runtime=RuntimeSpec(image="ghcr.io/vfaddey/zagent-runtime:latest", workdir="/workspace"),
        tools=ToolsConfig(builtin=("shell", "files", "apply_patch")),
        policy=PolicySpec(writable_paths=("/workspace",)),
    )

    assert spec.run_id == "fix-123"
    assert spec.tools.builtin == ("shell", "files", "apply_patch")


def test_tool_spec_is_independent_from_ag2() -> None:
    spec = ToolSpec(
        name="shell",
        kind=ToolKind.BUILTIN,
        description="Run a policy-checked shell command.",
    )

    assert spec.kind is ToolKind.BUILTIN
