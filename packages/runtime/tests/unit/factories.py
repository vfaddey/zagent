from pathlib import Path

from zagent_runtime.application.dto.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec
from zagent_runtime.infrastructure.config.loaders import DirectoryAgentEnvLoader


def create_context(workspace: Path, **kwargs) -> RuntimeContext:
    agent_env_dir = workspace / ".zagent"
    run_dir = agent_env_dir / "artifacts" / "run-1"

    task_kwargs = {
        "title": "Fix",
        "workspace": str(workspace),
        "prompt": "Fix bug.",
    }
    if "prompt" in kwargs:
        task_kwargs["prompt"] = kwargs.pop("prompt")
    if "prompt_file" in kwargs:
        task_kwargs["prompt_file"] = kwargs.pop("prompt_file")

    runtime_kwargs = {
        "image": "dummy-image:test",
        "workdir": str(workspace),
    }
    if "max_turns" in kwargs:
        runtime_kwargs["max_turns"] = kwargs.pop("max_turns")

    tools_kwargs = {
        "builtin": ("files",),
    }
    if "builtin_tools" in kwargs:
        tools_kwargs["builtin"] = kwargs.pop("builtin_tools")
    if "enable_mcp" in kwargs:
        tools_kwargs["enable_mcp"] = kwargs.pop("enable_mcp")

    spec_kwargs = dict(
        run_id="run-1",
        mode=RunMode.FIX,
        task=TaskSpec(**task_kwargs),
        model=ModelSpec(
            provider=ModelProvider.OPENAI_COMPATIBLE,
            model="gpt-5",
            api_key_env="OPENAI_API_KEY",
            timeout_seconds=120,
        ),
        agent_env=AgentEnvRef(path=str(agent_env_dir)),
        runtime=RuntimeSpec(**runtime_kwargs),
        tools=ToolsConfig(**tools_kwargs),
        policy=PolicySpec(writable_paths=(str(workspace),)),
    )
    spec_kwargs.update(kwargs)

    run_dir.mkdir(parents=True, exist_ok=True)

    run_spec = RunSpec(**spec_kwargs)
    paths = RuntimePaths(
        run_spec_file=agent_env_dir / "run.yaml",
        workspace=workspace,
        agent_env_dir=agent_env_dir,
        artifacts_root_dir=agent_env_dir / "artifacts",
        run_artifacts_dir=run_dir,
        state_file=run_dir / "state.json",
        chat_file=run_dir / "chat.jsonl",
        ag2_history_file=run_dir / "ag2_history.sqlite",
        events_file=run_dir / "events.jsonl",
        tools_file=run_dir / "tools.json",
        result_file=run_dir / "result.json",
        summary_file=run_dir / "summary.md",
    )
    try:
        agent_env = DirectoryAgentEnvLoader().load(agent_env_dir)
    except Exception:
        agent_env = AgentEnv(
            name="test",
            prompts=PromptFiles(),
        )

    return RuntimeContext(
        run_spec=run_spec,
        agent_env=agent_env,
        paths=paths,
    )
