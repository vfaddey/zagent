from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from zagent_launcher.domain import ContainerSpec, MountSpec


@dataclass(frozen=True, slots=True)
class DockerRunConfig:
    image: str
    command: tuple[str, ...]
    working_dir: str
    volumes: dict[str, dict[str, str]]
    environment: dict[str, str]
    network: str | None
    tty: bool


class DockerRunConfigBuilder:
    """Build Docker SDK run config from a ContainerSpec."""

    def build(self, spec: ContainerSpec, host_env: Mapping[str, str]) -> DockerRunConfig:
        return DockerRunConfig(
            image=spec.image,
            command=spec.command,
            working_dir=spec.workdir,
            volumes=self._volumes(spec.mounts),
            environment=self._environment(spec.env, host_env),
            network=spec.network,
            tty=spec.tty,
        )

    def _volumes(self, mounts: tuple[MountSpec, ...]) -> dict[str, dict[str, str]]:
        return {
            str(mount.host_path): {
                "bind": mount.container_path,
                "mode": "ro" if mount.read_only else "rw",
            }
            for mount in mounts
        }

    def _environment(
        self,
        env_names: tuple[str, ...],
        host_env: Mapping[str, str],
    ) -> dict[str, str]:
        return {name: host_env[name] for name in env_names if name in host_env}
