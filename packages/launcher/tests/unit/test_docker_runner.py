from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest
from docker.errors import DockerException
from zagent_launcher.application.errors import ContainerExecutionError
from zagent_launcher.domain import ContainerSpec
from zagent_launcher.infrastructure.containers import (
    DockerClientFactory,
    DockerRunConfigBuilder,
    DockerSdkRunner,
)


class FakeContainer:
    def __init__(self, status_code: int = 0) -> None:
        self.status_code = status_code
        self.removed = False

    def logs(self, stream: bool, follow: bool) -> list[bytes]:
        assert stream is True
        assert follow is True
        return [b"hello\n"]

    def wait(self) -> dict[str, int]:
        return {"StatusCode": self.status_code}

    def remove(self, force: bool) -> None:
        assert force is True
        self.removed = True


class FakeContainers:
    def __init__(self, container: FakeContainer) -> None:
        self.container = container
        self.kwargs: dict[str, Any] | None = None

    def run(self, **kwargs: Any) -> FakeContainer:
        self.kwargs = kwargs
        return self.container


class FakeDockerClient:
    def __init__(self, container: FakeContainer) -> None:
        self.containers = FakeContainers(container)
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeDockerClientFactory(DockerClientFactory):
    def __init__(self, client: FakeDockerClient) -> None:
        self.client = client

    def create(self) -> FakeDockerClient:
        return self.client


def test_docker_sdk_runner_runs_container_and_streams_logs(
) -> None:
    container = FakeContainer(status_code=7)
    client = FakeDockerClient(container)
    output = BytesIO()
    runner = DockerSdkRunner(
        DockerRunConfigBuilder(),
        FakeDockerClientFactory(client),
        output=output,
    )

    result = runner.run(
        ContainerSpec(
            image="image",
            command=("run", "--run-spec", "/workspace/.zagent/run.yaml"),
            env={"OPENAI_API_KEY": "secret"},
        )
    )

    assert result.exit_code == 7
    assert output.getvalue() == b"hello\n"
    assert container.removed is True
    assert client.closed is True
    assert client.containers.kwargs == {
        "image": "image",
        "command": ["run", "--run-spec", "/workspace/.zagent/run.yaml"],
        "working_dir": "/workspace",
        "volumes": {},
        "environment": {"OPENAI_API_KEY": "secret"},
        "network": None,
        "tty": False,
        "detach": True,
    }


def test_docker_sdk_runner_wraps_docker_errors() -> None:
    class FailingContainers:
        def run(self, **kwargs: Any) -> FakeContainer:
            raise DockerException("boom")

    class FailingClient:
        containers = FailingContainers()

        def close(self) -> None:
            pass

    class FailingFactory(DockerClientFactory):
        def create(self) -> FailingClient:
            return FailingClient()

    with pytest.raises(ContainerExecutionError):
        DockerSdkRunner(DockerRunConfigBuilder(), FailingFactory()).run(
            ContainerSpec(image="image", command=())
        )
