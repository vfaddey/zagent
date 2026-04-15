"""Model provider specification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelProvider(StrEnum):
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    provider: ModelProvider
    model: str
    api_key_env: str
    api_base: str | None = None

