"""Dishka providers for launcher dependencies."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from zagent_launcher.application import (
    CheckEnvironment,
    CollectRunResult,
    InitProject,
    PrepareRun,
    ReadRunState,
    ReadRunTrace,
    StartRun,
)
from zagent_launcher.application.interfaces import (
    ContainerRunner,
    HostEnvironment,
    ProjectTemplateProvider,
    ProjectWriter,
    RunSpecReader,
    RuntimeArtifactReader,
)
from zagent_launcher.infrastructure.artifacts import JsonRuntimeArtifactReader
from zagent_launcher.infrastructure.config.templates import BuiltinProjectTemplateProvider
from zagent_launcher.infrastructure.config.yaml_loader import YamlRunSpecReader
from zagent_launcher.infrastructure.containers import (
    DockerClientFactory,
    DockerRunConfigBuilder,
    DockerSdkRunner,
)
from zagent_launcher.infrastructure.filesystem.local_project_writer import LocalProjectWriter
from zagent_launcher.infrastructure.host.environment import OsHostEnvironment


class LauncherProvider(Provider):
    """Application-wide launcher dependency provider."""

    scope = Scope.APP

    template_provider = provide(
        BuiltinProjectTemplateProvider,
        provides=ProjectTemplateProvider,
    )
    project_writer = provide(LocalProjectWriter, provides=ProjectWriter)
    run_spec_reader = provide(YamlRunSpecReader, provides=RunSpecReader)
    host_environment = provide(OsHostEnvironment, provides=HostEnvironment)
    artifact_reader = provide(JsonRuntimeArtifactReader, provides=RuntimeArtifactReader)
    docker_client_factory = provide(DockerClientFactory)
    docker_run_config_builder = provide(DockerRunConfigBuilder)

    init_project = provide(InitProject)
    prepare_run = provide(PrepareRun)
    start_run = provide(StartRun)
    read_run_state = provide(ReadRunState)
    read_run_trace = provide(ReadRunTrace)
    collect_run_result = provide(CollectRunResult)
    check_environment = provide(CheckEnvironment)

    @provide
    def container_runner(
        self,
        run_config_builder: DockerRunConfigBuilder,
        client_factory: DockerClientFactory,
    ) -> ContainerRunner:
        return DockerSdkRunner(run_config_builder, client_factory)
