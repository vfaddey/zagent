"""Launcher CLI entrypoint."""

from __future__ import annotations

import typer

app = typer.Typer(help="Launch and inspect ZAgent runtime containers.")


@app.callback()
def callback() -> None:
    """ZAgent launcher entrypoint."""


def main() -> None:
    """Run the launcher CLI."""
    app()


if __name__ == "__main__":
    main()
