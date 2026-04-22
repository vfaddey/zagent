from __future__ import annotations

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
    def build(self, spec: ContainerSpec) -> DockerRunConfig:
        return DockerRunConfig(
            image=spec.image,
            command=spec.command,
            working_dir=spec.workdir,
            volumes=self._volumes(spec.mounts),
            environment=dict(spec.env),
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
