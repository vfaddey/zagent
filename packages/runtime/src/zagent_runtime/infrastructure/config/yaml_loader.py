"""YAML configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from zagent_runtime.infrastructure.config.errors import (
    ConfigFileNotFoundError,
    ConfigParseError,
)


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigFileNotFoundError(path)

    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ConfigParseError(path, str(error)) from error

    if loaded is None:
        return {}

    if not isinstance(loaded, dict):
        raise ConfigParseError(path, "top-level YAML value must be a mapping")

    return loaded


def load_config_model[T: BaseModel](path: Path, model: type[T]) -> T:
    data = load_yaml_mapping(path)
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise ConfigParseError(path, str(error)) from error
