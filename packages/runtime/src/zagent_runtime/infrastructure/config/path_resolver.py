"""Configuration path resolver."""

from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.dto.runtime_context import RuntimePaths
from zagent_runtime.domain.run import RunSpec


class PathResolutionError(Exception):
    """Raised when runtime paths cannot be resolved."""


class DefaultRuntimePathResolver:
    """Resolve runtime filesystem paths from a run specification."""

    def resolve(self, run_spec_file: Path, run_spec: RunSpec) -> RuntimePaths:
        """Resolve runtime paths for one run."""
        normalized_run_spec_file = run_spec_file.expanduser().resolve()
        workspace = self._resolve_path(
            base=normalized_run_spec_file.parent,
            value=run_spec.task.workspace,
        )
        agent_env_dir = self._resolve_path(
            base=workspace,
            value=run_spec.agent_env.path,
        )

        artifacts_root_dir = agent_env_dir / "artifacts"
        run_artifacts_dir = artifacts_root_dir / run_spec.run_id

        return RuntimePaths(
            run_spec_file=normalized_run_spec_file,
            workspace=workspace,
            agent_env_dir=agent_env_dir,
            artifacts_root_dir=artifacts_root_dir,
            run_artifacts_dir=run_artifacts_dir,
            state_file=run_artifacts_dir / "state.json",
            chat_file=run_artifacts_dir / "chat.jsonl",
            ag2_history_file=run_artifacts_dir / "ag2_history.json",
            events_file=run_artifacts_dir / "events.jsonl",
            tools_file=run_artifacts_dir / "tools.jsonl",
            result_file=run_artifacts_dir / "result.json",
            summary_file=run_artifacts_dir / "summary.md",
        )

    @staticmethod
    def _resolve_path(base: Path, value: str) -> Path:
        raw_path = Path(value).expanduser()
        if raw_path.is_absolute():
            return raw_path.resolve(strict=False)
        return (base / raw_path).resolve(strict=False)
