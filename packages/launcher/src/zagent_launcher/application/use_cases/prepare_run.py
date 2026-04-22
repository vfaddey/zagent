from __future__ import annotations

from pathlib import Path

from zagent_launcher.application.dto import LauncherRunSpec
from zagent_launcher.application.errors import (
    MissingEnvironmentVariableError,
    RunSpecOutsideProjectError,
)
from zagent_launcher.application.interfaces import HostEnvironment, RunSpecReader
from zagent_launcher.domain import ContainerSpec, MountSpec, RunRequest


class PrepareRun:
    _WORKSPACE_MOUNT = "/workspace"

    def __init__(self, run_spec_reader: RunSpecReader, host_environment: HostEnvironment) -> None:
        self._run_spec_reader = run_spec_reader
        self._host_environment = host_environment

    def __call__(self, request: RunRequest) -> ContainerSpec:
        project_root = request.project_root.expanduser().resolve(strict=False)
        run_spec_path = self._resolve_run_spec_path(project_root, request.run_spec)
        run_spec = self._run_spec_reader.read(run_spec_path)

        command = [
            "run",
            "--run-spec",
            self._container_path(project_root, run_spec_path),
        ]
        if request.dry_run:
            command.append("--dry-run")
        if request.continue_message is not None:
            command.extend(("--continue", request.continue_message))

        host_workspace_path = self._host_environment.get("ZAGENT_HOST_WORKSPACE_PATH")
        if host_workspace_path:
            mount_host_path = Path(host_workspace_path).expanduser().resolve(strict=False)
        else:
            mount_host_path = project_root

        return ContainerSpec(
            image=request.image_override or run_spec.runtime_image,
            command=tuple(command),
            workdir=run_spec.runtime_workdir,
            mounts=(MountSpec(host_path=mount_host_path, container_path=self._WORKSPACE_MOUNT),),
            env=self._container_env(run_spec, request.dry_run),
            network=self._docker_network(run_spec.policy_network),
        )

    def _resolve_run_spec_path(self, project_root: Path, run_spec: Path) -> Path:
        expanded = run_spec.expanduser()
        if expanded.is_absolute():
            return expanded.resolve(strict=False)
        return (project_root / expanded).resolve(strict=False)

    def _container_path(self, project_root: Path, run_spec_path: Path) -> str:
        try:
            relative_path = run_spec_path.relative_to(project_root)
        except ValueError as error:
            raise RunSpecOutsideProjectError(run_spec_path, project_root) from error
        return f"{self._WORKSPACE_MOUNT}/{relative_path.as_posix()}"

    def _docker_network(self, policy_network: str) -> str | None:
        if policy_network == "disabled":
            return "none"
        return None

    def _container_env(self, run_spec: LauncherRunSpec, dry_run: bool) -> dict[str, str]:
        env = {
            spec.name: self._required_env(spec.name, default=spec.default)
            for spec in run_spec.runtime_env
        }
        model_api_key = run_spec.model_api_key_env
        if model_api_key in env:
            return env
        if dry_run:
            model_value = self._host_environment.get(model_api_key)
            if model_value is not None:
                env[model_api_key] = model_value
            return env
        env[model_api_key] = self._required_env(model_api_key)
        return env

    def _required_env(self, name: str, default: str | None = None) -> str:
        value = self._host_environment.get(name)
        if value is not None:
            return value
        if default is not None:
            return default
        raise MissingEnvironmentVariableError(name)
