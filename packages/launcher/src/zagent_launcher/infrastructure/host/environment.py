"""Host environment reader."""

from __future__ import annotations

import os

from zagent_launcher.application.interfaces import HostEnvironment


class OsHostEnvironment(HostEnvironment):
    def has(self, name: str) -> bool:
        return bool(os.environ.get(name))
