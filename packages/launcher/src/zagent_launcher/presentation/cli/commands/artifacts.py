from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from zagent_launcher.application import (
    CollectRunResult,
    FeatureNotImplementedError,
    LauncherError,
    ReadRunState,
    ReadRunTrace,
)
from zagent_launcher.presentation.cli.dependencies import launcher_container
from zagent_launcher.presentation.cli.output import console, fail, not_implemented

_PROJECT_ROOT_OPTION = typer.Option(
    "--project-root",
    "-C",
    file_okay=False,
    dir_okay=True,
    help="Project root that contains .zagent.",
)


def status(
    project_root: Annotated[Path, _PROJECT_ROOT_OPTION] = Path("."),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Run id. Defaults to the run_id in .zagent/run.yaml."),
    ] = None,
) -> None:
    with launcher_container() as container:
        use_case = container.get(ReadRunState)
        try:
            state = use_case(project_root=project_root, run_id=run_id)
        except FeatureNotImplementedError as error:
            not_implemented(error)
        except LauncherError as error:
            fail(error)

    console.print(f"run_id: [bold]{state.run_id}[/bold]")
    console.print(f"status: {state.status}")
    console.print(f"phase: {state.phase}")
    if state.updated_at is not None:
        console.print(f"updated_at: {state.updated_at}")
    if state.artifacts:
        console.print("artifacts:")
        for artifact in state.artifacts:
            console.print(f"  {artifact}")


def logs(
    project_root: Annotated[Path, _PROJECT_ROOT_OPTION] = Path("."),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Run id. Defaults to the run_id in .zagent/run.yaml."),
    ] = None,
    follow: Annotated[
        bool,
        typer.Option("--follow", "-f", help="Follow runtime JSONL trace files."),
    ] = False,
) -> None:
    with launcher_container() as container:
        use_case = container.get(ReadRunTrace)
        try:
            trace = use_case(project_root=project_root, run_id=run_id, follow=follow)
        except FeatureNotImplementedError as error:
            not_implemented(error)
        except LauncherError as error:
            fail(error)

    for line in trace.lines:
        console.print(f"{line.source} {line.content}")


def result(
    project_root: Annotated[Path, _PROJECT_ROOT_OPTION] = Path("."),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Run id. Defaults to the run_id in .zagent/run.yaml."),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print result.json instead of a human summary."),
    ] = False,
) -> None:
    with launcher_container() as container:
        use_case = container.get(CollectRunResult)
        try:
            run_result = use_case(project_root=project_root, run_id=run_id)
        except FeatureNotImplementedError as error:
            not_implemented(error)
        except LauncherError as error:
            fail(error)

    if as_json:
        console.print(json.dumps(run_result.raw, ensure_ascii=False, indent=2, sort_keys=True))
        return

    console.print(f"run_id: [bold]{run_result.run_id}[/bold]")
    console.print(f"status: {run_result.status}")
    if run_result.error is not None:
        console.print(f"error: {run_result.error}")
    console.print(run_result.summary)
    if run_result.artifacts:
        console.print("artifacts:")
        for artifact in run_result.artifacts:
            console.print(f"  {artifact}")
