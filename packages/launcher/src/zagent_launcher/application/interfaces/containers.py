from __future__ import annotations

from typing import Protocol

from zagent_launcher.domain import ContainerSpec, LaunchResult


class ContainerRunner(Protocol):
    def run(self, spec: ContainerSpec) -> LaunchResult: ...
