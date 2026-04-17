"""`zagent init` command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from zagent_launcher.application import InitProject, InitProjectRequest, LauncherError
from zagent_launcher.presentation.cli.dependencies import launcher_container
from zagent_launcher.presentation.cli.output import console, fail, print_paths


def init_project(
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            "-C",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Project root where .zagent will be created.",
        ),
    ] = Path("."),
    template: Annotated[
        str,
        typer.Option(
            "--template",
            help="Built-in project template name.",
        ),
    ] = "basic",
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing template files.",
        ),
    ] = False,
) -> None:
    with launcher_container() as container:
        use_case = container.get(InitProject)
        try:
            result = use_case(
                InitProjectRequest(project_root=project_root, template=template, force=force)
            )
        except LauncherError as error:
            fail(error)

    console.print(f"Initialized [bold].zagent[/bold] at {result.layout.agent_dir}")
    print_paths("created", result.created)
    print_paths("overwritten", result.overwritten)
    print_paths("skipped", result.skipped)
