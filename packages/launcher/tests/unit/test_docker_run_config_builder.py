from __future__ import annotations

from pathlib import Path

from zagent_launcher.domain import ContainerSpec, MountSpec
from zagent_launcher.infrastructure.containers import DockerRunConfigBuilder


def test_docker_run_config_builder_builds_sdk_config(tmp_path: Path) -> None:
    spec = ContainerSpec(
        image="dummy-image:test",
        command=("run", "--run-spec", "/workspace/.zagent/run.yaml", "--dry-run"),
        workdir="/workspace",
        mounts=(MountSpec(host_path=tmp_path, container_path="/workspace"),),
        env=("OPENAI_API_KEY",),
        network="none",
    )

    config = DockerRunConfigBuilder().build(spec, {"OPENAI_API_KEY": "secret"})

    assert config.image == "dummy-image:test"
    assert config.command == ("run", "--run-spec", "/workspace/.zagent/run.yaml", "--dry-run")
    assert config.working_dir == "/workspace"
    assert config.volumes == {
        str(tmp_path): {
            "bind": "/workspace",
            "mode": "rw",
        }
    }
    assert config.environment == {"OPENAI_API_KEY": "secret"}
    assert config.network == "none"


def test_docker_run_config_builder_marks_read_only_mounts(tmp_path: Path) -> None:
    spec = ContainerSpec(
        image="image",
        command=("run",),
        mounts=(MountSpec(host_path=tmp_path, container_path="/workspace", read_only=True),),
    )

    config = DockerRunConfigBuilder().build(spec, {})

    assert config.volumes[str(tmp_path)]["mode"] == "ro"
