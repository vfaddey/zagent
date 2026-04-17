"""`zagent run` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from zagent_launcher.application import (
    FeatureNotImplementedError,
    LauncherError,
    PrepareRun,
    StartRun,
)
from zagent_launcher.domain import RunRequest
from zagent_launcher.presentation.cli.dependencies import launcher_container
from zagent_launcher.presentation.cli.output import console, fail, not_implemented


def run(
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            "-C",
            file_okay=False,
            dir_okay=True,
            help="Project root mounted as /workspace.",
        ),
    ] = Path("."),
    run_spec: Annotated[
        Path,
        typer.Option(
            "--run-spec",
            "-f",
            help="Run spec path, relative to project root unless absolute.",
        ),
    ] = Path(".zagent/run.yaml"),
    image: Annotated[
        str | None,
        typer.Option(
            "--image",
            help="Override runtime image from run.yaml.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Ask runtime to build context without calling the LLM backend.",
        ),
    ] = False,
    continue_message: Annotated[
        str | None,
        typer.Option(
            "--continue",
            "-c",
            help="Continue a previous run with a new user message.",
        ),
    ] = None,
) -> None:
    """Start a runtime container for one run."""
    request = RunRequest(
        project_root=project_root,
        run_spec=run_spec,
        image_override=image,
        dry_run=dry_run,
        continue_message=continue_message,
    )

    with launcher_container() as container:
        prepare_run = container.get(PrepareRun)
        start_run = container.get(StartRun)
        try:
            container_spec = prepare_run(request)
            result = start_run(container_spec)
        except FeatureNotImplementedError as error:
            not_implemented(error)
        except LauncherError as error:
            fail(error)

    console.print(result.message)
    raise typer.Exit(code=result.exit_code)
