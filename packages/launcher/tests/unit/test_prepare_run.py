from __future__ import annotations

from pathlib import Path

import pytest
from zagent_launcher.application.dto import LauncherRunSpec, LauncherRuntimeEnvVar
from zagent_launcher.application.errors import (
    MissingEnvironmentVariableError,
    RunSpecOutsideProjectError,
)
from zagent_launcher.application.interfaces import HostEnvironment, RunSpecReader
from zagent_launcher.application.use_cases import PrepareRun
from zagent_launcher.domain import RunRequest

from .factories import create_launcher_run_spec


class StubRunSpecReader(RunSpecReader):
    def __init__(self, run_spec: LauncherRunSpec) -> None:
        self.run_spec = run_spec
        self.path: Path | None = None

    def read(self, path: Path) -> LauncherRunSpec:
        self.path = path
        return self.run_spec


class StubHostEnvironment(HostEnvironment):
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def has(self, name: str) -> bool:
        return name in self.values

    def get(self, name: str) -> str | None:
        return self.values.get(name)


def test_prepare_run_builds_runtime_container_spec(tmp_path: Path) -> None:
    reader = StubRunSpecReader(
        create_launcher_run_spec()
    )
    use_case = PrepareRun(reader, StubHostEnvironment({"OPENAI_API_KEY": "secret"}))

    spec = use_case(
        RunRequest(
            project_root=tmp_path,
            run_spec=Path(".zagent/run.yaml"),
            dry_run=True,
            continue_message="keep going",
        )
    )

    assert reader.path == (tmp_path / ".zagent/run.yaml").resolve(strict=False)
    assert spec.image == "dummy-image:test"
    assert spec.workdir == "/workspace"
    assert spec.command == (
        "run",
        "--run-spec",
        "/workspace/.zagent/run.yaml",
        "--dry-run",
        "--continue",
        "keep going",
    )
    assert spec.mounts[0].host_path == tmp_path.resolve(strict=False)
    assert spec.mounts[0].container_path == "/workspace"
    assert spec.env == {"OPENAI_API_KEY": "secret"}
    assert spec.network is None


def test_prepare_run_allows_image_override(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec()
        ),
        StubHostEnvironment({"OPENAI_API_KEY": "secret"}),
    )

    spec = use_case(
        RunRequest(
            project_root=tmp_path,
            run_spec=Path(".zagent/run.yaml"),
            image_override="custom-runtime:dev",
        )
    )

    assert spec.image == "custom-runtime:dev"


def test_prepare_run_requires_host_api_key_env(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec()
        ),
        StubHostEnvironment({}),
    )

    with pytest.raises(MissingEnvironmentVariableError):
        use_case(RunRequest(project_root=tmp_path, run_spec=Path(".zagent/run.yaml")))


def test_prepare_run_does_not_require_host_api_key_env_for_dry_run(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec()
        ),
        StubHostEnvironment({}),
    )

    spec = use_case(
        RunRequest(project_root=tmp_path, run_spec=Path(".zagent/run.yaml"), dry_run=True)
    )

    assert spec.command == ("run", "--run-spec", "/workspace/.zagent/run.yaml", "--dry-run")
    assert spec.env == {}


def test_prepare_run_rejects_run_spec_outside_project(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-run.yaml"
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec()
        ),
        StubHostEnvironment({"OPENAI_API_KEY": "secret"}),
    )

    with pytest.raises(RunSpecOutsideProjectError):
        use_case(RunRequest(project_root=tmp_path, run_spec=outside))


def test_prepare_run_maps_disabled_network_to_docker_none(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec(policy_network="disabled")
        ),
        StubHostEnvironment({"OPENAI_API_KEY": "secret"}),
    )

    spec = use_case(RunRequest(project_root=tmp_path, run_spec=Path(".zagent/run.yaml")))

    assert spec.network == "none"


def test_prepare_run_resolves_runtime_env_from_host_or_default(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec(
                runtime_env=(
                    LauncherRuntimeEnvVar("API_BASE"),
                ),
            )
        ),
        StubHostEnvironment(
            {
                "API_BASE": "http://host-llm",
                "OPENAI_API_KEY": "secret",
            }
        ),
    )

    spec = use_case(RunRequest(project_root=tmp_path, run_spec=Path(".zagent/run.yaml")))

    assert spec.env == {
        "API_BASE": "http://host-llm",
        "OPENAI_API_KEY": "secret",
    }


def test_prepare_run_uses_declared_runtime_env_defaults(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec(
                runtime_env=(
                    LauncherRuntimeEnvVar("API_BASE", "http://llm"),
                )
            )
        ),
        StubHostEnvironment({"OPENAI_API_KEY": "secret"}),
    )

    spec = use_case(RunRequest(project_root=tmp_path, run_spec=Path(".zagent/run.yaml")))

    assert spec.env == {
        "API_BASE": "http://llm",
        "OPENAI_API_KEY": "secret",
    }


def test_prepare_run_requires_declared_runtime_env_without_default(tmp_path: Path) -> None:
    use_case = PrepareRun(
        StubRunSpecReader(
            create_launcher_run_spec(runtime_env=(LauncherRuntimeEnvVar("API_BASE"),))
        ),
        StubHostEnvironment({"OPENAI_API_KEY": "secret"}),
    )

    with pytest.raises(MissingEnvironmentVariableError, match="API_BASE"):
        use_case(RunRequest(project_root=tmp_path, run_spec=Path(".zagent/run.yaml")))
