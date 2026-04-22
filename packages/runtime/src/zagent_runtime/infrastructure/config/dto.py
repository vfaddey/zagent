"""Pydantic DTOs for runtime configuration files."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from zagent_runtime.domain.agent_env import AgentEnvRef
from zagent_runtime.domain.mcp import McpServersConfig, McpServerSpec, McpTransport
from zagent_runtime.domain.model import ModelProvider, ModelSpec
from zagent_runtime.domain.policy import NetworkPolicy, PolicySpec
from zagent_runtime.domain.run import RunMode, RunSpec, RuntimeEnvVar, RuntimeSpec, ToolsConfig
from zagent_runtime.domain.task import TaskSpec


class StrictConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskConfig(StrictConfigModel):
    title: str = Field(min_length=1)
    workspace: str = Field(min_length=1)
    prompt: str | None = Field(default=None, min_length=1)
    prompt_file: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_prompt_source(self) -> TaskConfig:
        prompt_sources = (self.prompt is not None, self.prompt_file is not None)
        if prompt_sources.count(True) != 1:
            raise ValueError("task requires exactly one of prompt or prompt_file")
        return self

    def to_domain(self) -> TaskSpec:
        return TaskSpec(
            title=self.title,
            workspace=self.workspace,
            prompt=self.prompt,
            prompt_file=self.prompt_file,
        )


class ModelConfig(StrictConfigModel):
    provider: ModelProvider
    model: str
    api_key_env: str
    api_base: str | None = None
    timeout_seconds: float | None = Field(default=None, gt=0)
    reasoning_effort: str | None = None

    def to_domain(self) -> ModelSpec:
        return ModelSpec(
            provider=self.provider,
            model=self.model,
            api_key_env=self.api_key_env,
            api_base=self.api_base,
            timeout_seconds=self.timeout_seconds,
            reasoning_effort=self.reasoning_effort,
        )


class AgentEnvRefConfig(StrictConfigModel):
    path: str = ".zagent"

    def to_domain(self) -> AgentEnvRef:
        return AgentEnvRef(path=self.path)


class RuntimeEnvVarConfig(StrictConfigModel):
    default: str | None = None


class RuntimeConfig(StrictConfigModel):
    image: str
    workdir: str
    max_turns: int = Field(default=20, ge=1, le=100)
    env: dict[str, RuntimeEnvVarConfig] = Field(default_factory=dict)

    def to_domain(self) -> RuntimeSpec:
        return RuntimeSpec(
            image=self.image,
            workdir=self.workdir,
            max_turns=self.max_turns,
            env=tuple(
                RuntimeEnvVar(name=name, default=config.default)
                for name, config in self.env.items()
            ),
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
    agent_env: AgentEnvRefConfig = Field(default_factory=AgentEnvRefConfig)
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


class McpServerConfig(StrictConfigModel):
    name: str
    transport: McpTransport
    enabled: bool = True
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    environment_env: dict[str, str] = Field(default_factory=dict)
    working_dir: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    headers_env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float | None = Field(default=None, gt=0)
    read_timeout_seconds: float | None = Field(default=None, gt=0)
    use_tools: bool = True
    use_resources: bool = False

    @field_validator("transport", mode="before")
    @classmethod
    def normalize_transport(cls, value: object) -> object:
        if isinstance(value, str):
            return value.replace("-", "_")
        return value

    @model_validator(mode="after")
    def validate_transport_fields(self) -> McpServerConfig:
        if self.transport is McpTransport.STDIO and not self.command:
            raise ValueError("stdio MCP server requires command")
        if self.transport in {McpTransport.SSE, McpTransport.STREAMABLE_HTTP} and not self.url:
            raise ValueError(f"{self.transport.value} MCP server requires url")
        return self

    def to_domain(self) -> McpServerSpec:
        return McpServerSpec(
            name=self.name,
            transport=self.transport,
            enabled=self.enabled,
            command=self.command,
            args=tuple(self.args),
            url=self.url,
            environment=self.environment,
            environment_env=self.environment_env,
            working_dir=self.working_dir,
            headers=self.headers,
            headers_env=self.headers_env,
            timeout_seconds=self.timeout_seconds,
            read_timeout_seconds=self.read_timeout_seconds,
            use_tools=self.use_tools,
            use_resources=self.use_resources,
        )


class McpServersConfigDto(StrictConfigModel):
    servers: list[McpServerConfig] = Field(default_factory=list)

    def to_domain(self) -> McpServersConfig:
        return McpServersConfig(
            servers=tuple(server.to_domain() for server in self.servers),
        )
