"""Launcher application errors."""

from __future__ import annotations


class LauncherError(Exception):
    """Base launcher application error."""


class FeatureNotImplementedError(LauncherError):
    """Raised by scaffolded use cases that are not implemented yet."""

    def __init__(self, command: str) -> None:
        super().__init__(f"`zagent {command}` is not implemented yet.")
        self.command = command


class ProjectInitError(LauncherError):
    """Raised when project initialization cannot be completed."""


class RunPreparationError(LauncherError):
    """Raised when a runtime container cannot be prepared."""


class RunSpecNotFoundError(RunPreparationError):
    """Raised when run.yaml cannot be found."""

    def __init__(self, path: object) -> None:
        super().__init__(f"Run spec not found: {path}")
        self.path = path


class RunSpecParseError(RunPreparationError):
    """Raised when run.yaml cannot be parsed."""

    def __init__(self, path: object, reason: str) -> None:
        super().__init__(f"Invalid run spec {path}: {reason}")
        self.path = path
        self.reason = reason


class MissingEnvironmentVariableError(RunPreparationError):
    """Raised when a required host environment variable is missing."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Required environment variable is not set: {name}")
        self.name = name


class RunSpecOutsideProjectError(RunPreparationError):
    """Raised when run spec cannot be addressed through the workspace mount."""

    def __init__(self, run_spec: object, project_root: object) -> None:
        super().__init__(f"Run spec {run_spec} is outside project root {project_root}")
        self.run_spec = run_spec
        self.project_root = project_root


class ContainerExecutionError(LauncherError):
    """Raised when a container runner cannot start a container."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Container execution failed: {reason}")
        self.reason = reason


class ArtifactNotFoundError(LauncherError):
    """Raised when runtime artifacts cannot be found."""

    def __init__(self, path: object) -> None:
        super().__init__(f"Runtime artifact not found: {path}")
        self.path = path


class ArtifactParseError(LauncherError):
    """Raised when a runtime artifact cannot be parsed."""

    def __init__(self, path: object, reason: str) -> None:
        super().__init__(f"Invalid runtime artifact {path}: {reason}")
        self.path = path
        self.reason = reason


class ArtifactPathError(LauncherError):
    """Raised when a runtime artifact path cannot be mapped to the host project."""

    def __init__(self, path: object) -> None:
        super().__init__(f"Runtime artifact path is outside the mounted workspace: {path}")
        self.path = path
