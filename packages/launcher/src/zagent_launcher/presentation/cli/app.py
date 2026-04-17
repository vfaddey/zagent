from __future__ import annotations

import typer

from zagent_launcher.presentation.cli.commands.artifacts import logs, result, status
from zagent_launcher.presentation.cli.commands.doctor import doctor
from zagent_launcher.presentation.cli.commands.init import init_project
from zagent_launcher.presentation.cli.commands.run import run

app = typer.Typer(help="Launch and inspect ZAgent runtime containers.")


@app.callback()
def callback() -> None:
    """ZAgent launcher entrypoint."""


app.command("init")(init_project)
app.command("run")(run)
app.command("status")(status)
app.command("logs")(logs)
app.command("result")(result)
app.command("doctor")(doctor)


def main() -> None:
    app()
