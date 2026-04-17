from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectLayout:
    root: Path
    agent_dir: Path
    run_spec_file: Path
    artifacts_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> ProjectLayout:
        resolved_root = root.expanduser().resolve(strict=False)
        agent_dir = resolved_root / ".zagent"
        return cls(
            root=resolved_root,
            agent_dir=agent_dir,
            run_spec_file=agent_dir / "run.yaml",
            artifacts_dir=agent_dir / "artifacts",
        )
