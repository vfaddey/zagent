"""Prompt fragment loader."""

from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.runtime_context import RuntimeContext


class MarkdownPromptDocumentLoader:
    """Load prompt files and extract short titles from rules and skills."""

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()

    def title_for(self, path: Path) -> str:
        text = self.read_text(path)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
            if stripped.lower().startswith("title:"):
                return stripped.split(":", maxsplit=1)[1].strip()
            return stripped
        return path.stem.replace("_", " ").replace("-", " ").title()

    def display_path(self, path: Path, context: RuntimeContext) -> str:
        resolved = path.resolve(strict=False)
        try:
            return str(resolved.relative_to(context.paths.workspace.resolve(strict=False)))
        except ValueError:
            return str(resolved)
