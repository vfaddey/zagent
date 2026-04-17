"""Runtime policy specification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class NetworkPolicy(StrEnum):
    """Network access policy for a run."""

    RESTRICTED = "restricted"
    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class PolicySpec:
    """Policy settings from run.yaml."""

    network: NetworkPolicy = NetworkPolicy.RESTRICTED
    git_push: bool = False
    writable_paths: tuple[str, ...] = field(default_factory=tuple)
