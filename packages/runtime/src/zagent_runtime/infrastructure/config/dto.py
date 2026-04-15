"""Pydantic DTOs for runtime configuration files."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from zagent_runtime.domain.agent_env import AgentEnv, AgentEnvRef, PromptFiles
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import NetworkPolicy, PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec


class StrictConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskConfig(StrictConfigModel):
    title: str
    description: str
    workspace: str

    def to_domain(self) -> TaskSpec:
        return TaskSpec(
            title=self.title,
            description=self.description,
            workspace=self.workspace,
        )


class ModelConfig(StrictConfigModel):
    provider: ModelProvider
    model: str
    api_key_env: str
    api_base: str | None = None

    def to_domain(self) -> ModelSpec:
        return ModelSpec(
            provider=self.provider,
            model=self.model,
            api_key_env=self.api_key_env,
            api_base=self.api_base,
        )


class AgentEnvRefConfig(StrictConfigModel):
    path: str

    def to_domain(self) -> AgentEnvRef:
        return AgentEnvRef(path=self.path)


class RuntimeConfig(StrictConfigModel):
    image: str
    workdir: str
    max_turns: int = Field(default=20, ge=1, le=100)
    final_marker: str = "ZAGENT_DONE"

    def to_domain(self) -> RuntimeSpec:
        return RuntimeSpec(
            image=self.image,
            workdir=self.workdir,
            max_turns=self.max_turns,
            final_marker=self.final_marker,
        )


class ToolsConfigDto(StrictConfigModel):
    builtin: list[str] = Field(default_factory=list)
    custom: list[str] = Field(default_factory=list)
    enable_mcp: bool = False

    def to_domain(self) -> ToolsConfig:
        return ToolsConfig(
            builtin=tuple(self.builtin),
            custom=tuple(self.custom),
            enable_mcp=self.enable_mcp,
        )


class PolicyConfig(StrictConfigModel):
    network: NetworkPolicy = NetworkPolicy.RESTRICTED
    git_push: bool = False
    writable_paths: list[str] = Field(default_factory=list)

    def to_domain(self) -> PolicySpec:
        return PolicySpec(
            network=self.network,
            git_push=self.git_push,
            writable_paths=tuple(self.writable_paths),
        )


class RunSpecConfig(StrictConfigModel):
    run_id: str
    mode: RunMode
    task: TaskConfig
    model: ModelConfig
    agent_env: AgentEnvRefConfig
    runtime: RuntimeConfig
    tools: ToolsConfigDto
    policy: PolicyConfig

    def to_domain(self) -> RunSpec:
        return RunSpec(
            run_id=self.run_id,
            mode=self.mode,
            task=self.task.to_domain(),
            model=self.model.to_domain(),
            agent_env=self.agent_env.to_domain(),
            runtime=self.runtime.to_domain(),
            tools=self.tools.to_domain(),
            policy=self.policy.to_domain(),
        )


class PromptFilesConfig(StrictConfigModel):
    system: str | None = None
    developer: str | None = None
    task: str | None = None

    def to_domain(self) -> PromptFiles:
        return PromptFiles(
            system=self.system,
            developer=self.developer,
            task=self.task,
        )


class McpConfig(StrictConfigModel):
    servers_file: str | None = None


class ExtraFilesConfig(StrictConfigModel):
    extra_context: list[str] = Field(default_factory=list)


class AgentEnvConfig(StrictConfigModel):
    name: str
    prompts: PromptFilesConfig = Field(default_factory=PromptFilesConfig)
    rules: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    mcp: McpConfig = Field(default_factory=McpConfig)
    files: ExtraFilesConfig = Field(default_factory=ExtraFilesConfig)

    def to_domain(self) -> AgentEnv:
        return AgentEnv(
            name=self.name,
            prompts=self.prompts.to_domain(),
            rules=tuple(self.rules),
            skills=tuple(self.skills),
            mcp_servers_file=self.mcp.servers_file,
            extra_context_files=tuple(self.files.extra_context),
        )
