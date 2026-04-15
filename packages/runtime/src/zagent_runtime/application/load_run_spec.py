"""Load run specification use case."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_runtime.domain.run import RunSpec


class RunSpecLoader(Protocol):
    def load(self, path: Path) -> RunSpec: ...


class LoadRunSpec:
    def __init__(self, loader: RunSpecLoader) -> None:
        self._loader = loader

    def __call__(self, path: Path) -> RunSpec:
        return self._loader.load(path)
