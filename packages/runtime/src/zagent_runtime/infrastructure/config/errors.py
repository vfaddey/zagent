"""Configuration loading errors."""

from __future__ import annotations

from pathlib import Path


class ConfigError(Exception):
    """Base configuration error."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when a configuration file does not exist."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Configuration file not found: {path}")
        self.path = path


class ConfigParseError(ConfigError):
    """Raised when a configuration file cannot be parsed."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"Invalid configuration file {path}: {reason}")
        self.path = path
        self.reason = reason

