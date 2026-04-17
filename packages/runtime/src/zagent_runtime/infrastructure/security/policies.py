"""Runtime policy enforcement."""

from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.infrastructure.security.errors import PolicyViolationError


class FileSystemPolicy:
    """Filesystem policy checks for runtime-native tools."""

    def resolve_workspace_path(self, context: RuntimeContext, value: str) -> Path:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path.resolve(strict=False)
        return (context.paths.workspace / path).resolve(strict=False)

    def ensure_read_allowed(self, context: RuntimeContext, path: Path) -> None:
        resolved = path.resolve(strict=False)
        if self._is_inside(resolved, context.paths.workspace):
            return
        if self._is_inside(resolved, context.paths.agent_env_dir):
            return
        raise PolicyViolationError(f"Read path is outside allowed roots: {resolved}")

    def ensure_write_allowed(self, context: RuntimeContext, path: Path) -> None:
        resolved = path.resolve(strict=False)
        allowed_roots = self._writable_roots(context)
        if any(self._is_inside(resolved, root) for root in allowed_roots):
            return
        raise PolicyViolationError(f"Write path is outside writable roots: {resolved}")

    def _writable_roots(self, context: RuntimeContext) -> tuple[Path, ...]:
        return tuple(
            self.resolve_workspace_path(context, value)
            for value in context.run_spec.policy.writable_paths
        )

    def _is_inside(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root.resolve(strict=False))
        except ValueError:
            return False
        return True
