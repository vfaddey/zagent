from __future__ import annotations

from zagent_launcher.application.errors import FeatureNotImplementedError


class CheckEnvironment:
    def __call__(self) -> None:
        raise FeatureNotImplementedError("doctor")
