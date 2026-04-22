"""Docker SDK container runner adapter."""

from __future__ import annotations

import sys
from typing import Any, BinaryIO

from docker.errors import DockerException  # type: ignore[import-not-found]

from docker import from_env  # type: ignore[attr-defined]
from zagent_launcher.application.errors import ContainerExecutionError
from zagent_launcher.application.interfaces import ContainerRunner
from zagent_launcher.domain import ContainerSpec, LaunchResult
from zagent_launcher.infrastructure.containers.run_config_builder import DockerRunConfigBuilder


class DockerClientFactory:
    def create(self) -> Any:
        return from_env()


class DockerSdkRunner(ContainerRunner):

    def __init__(
        self,
        run_config_builder: DockerRunConfigBuilder,
        client_factory: DockerClientFactory,
        output: BinaryIO | None = None,
    ) -> None:
        self._run_config_builder = run_config_builder
        self._client_factory = client_factory
        self._output = output or sys.stdout.buffer

    def run(self, spec: ContainerSpec) -> LaunchResult:
        run_config = self._run_config_builder.build(spec)
        client = self._client_factory.create()
        container: Any | None = None
        try:
            container = client.containers.run(
                image=run_config.image,
                command=list(run_config.command),
                working_dir=run_config.working_dir,
                volumes=run_config.volumes,
                environment=run_config.environment,
                network=run_config.network,
                tty=run_config.tty,
                detach=True,
            )
            for chunk in container.logs(stream=True, follow=True):
                self._output.write(chunk)
                self._output.flush()

            wait_result = container.wait()
            exit_code = int(wait_result.get("StatusCode", 1))
        except (DockerException, OSError) as error:
            raise ContainerExecutionError(str(error)) from error
        finally:
            if container is not None and spec.remove:
                try:
                    container.remove(force=True)
                except DockerException:
                    pass
            close = getattr(client, "close", None)
            if close is not None:
                close()

        return LaunchResult(exit_code=exit_code, message=f"Docker exited with code {exit_code}.")
