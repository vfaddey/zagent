"""`zagent doctor` command."""

from __future__ import annotations

from zagent_launcher.application import (
    CheckEnvironment,
    FeatureNotImplementedError,
    LauncherError,
)
from zagent_launcher.presentation.cli.dependencies import launcher_container
from zagent_launcher.presentation.cli.output import fail, not_implemented


def doctor() -> None:
    with launcher_container() as container:
        use_case = container.get(CheckEnvironment)
        try:
            use_case()
        except FeatureNotImplementedError as error:
            not_implemented(error)
        except LauncherError as error:
            fail(error)
