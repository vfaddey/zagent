from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console

from zagent_launcher.application import FeatureNotImplementedError, LauncherError

console = Console()
error_console = Console(stderr=True)


def print_paths(label: str, paths: tuple[Path, ...]) -> None:
    if not paths:
        return
    console.print(f"{label}:")
    for path in paths:
        console.print(f"  {path}")


def not_implemented(error: FeatureNotImplementedError) -> NoReturn:
    console.print(f"[yellow]{error}[/yellow]")
    raise typer.Exit(code=2) from error


def fail(error: LauncherError) -> NoReturn:
    error_console.print(f"[red]{error}[/red]")
    raise typer.Exit(code=1) from error
