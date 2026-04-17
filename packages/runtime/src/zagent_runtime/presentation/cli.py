"""Runtime CLI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from zagent_runtime.application.bootstrap import BootstrapRun
from zagent_runtime.infrastructure.di.container import RuntimeContainerFactory

app = typer.Typer(help="Run ZAgent inside a runtime container.")


@app.callback()
def callback() -> None:
    """ZAgent runtime entrypoint."""


@app.command("run")
def run(
    run_spec: Annotated[
        Path,
        typer.Option(
            "--run-spec",
            "-f",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to run.yaml.",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Build context and artifacts without calling the LLM backend.",
        ),
    ] = False,
    continue_msg: Annotated[
        str | None,
        typer.Option(
            "--continue",
            "-c",
            help="Continue previous run with a new message.",
        ),
    ] = None,
) -> None:
    container_factory = RuntimeContainerFactory()
    container = container_factory.create_dry_run() if dry_run else container_factory.create()

    try:
        result = container.get(BootstrapRun)(run_spec, continue_msg)
    except Exception as error:
        typer.echo(f"Runtime bootstrap failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(result.result.final_message)
    raise typer.Exit(code=result.exit_code)


def main() -> None:
    """Run the runtime CLI."""
    app()


if __name__ == "__main__":
    main()
