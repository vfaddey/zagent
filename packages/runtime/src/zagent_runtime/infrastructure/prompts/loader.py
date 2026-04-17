"""Prompt fragment loader."""

from __future__ import annotations

from pathlib import Path

from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.infrastructure.config.errors import ConfigFileNotFoundError, ConfigParseError


class MarkdownPromptDocumentLoader:
    """Load prompt files and extract short titles from rules and skills."""

    def read_text(self, path: Path) -> str:
        if not path.is_file():
            raise ConfigFileNotFoundError(path)
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise ConfigParseError(path, str(error)) from error

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

    def description_for(self, path: Path) -> str:
        text = self.read_text(path)
        for paragraph in self._paragraphs_without_title_lines(text):
            return self._shorten(paragraph)
        return "No description provided."

    def display_path(self, path: Path, context: RuntimeContext) -> str:
        resolved = path.resolve(strict=False)
        try:
            return str(resolved.relative_to(context.paths.workspace.resolve(strict=False)))
        except ValueError:
            return str(resolved)

    def _paragraphs_without_title_lines(self, text: str) -> tuple[str, ...]:
        paragraphs: list[str] = []
        current: list[str] = []
        seen_title = False

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
                continue

            if stripped.lower().startswith("title:"):
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
                description = stripped.split(":", maxsplit=1)[1].strip()
                if description:
                    paragraphs.append(description)
                seen_title = True
                continue

            if not seen_title and (
                stripped.startswith("#")
            ):
                seen_title = True
                continue

            current.append(stripped)

        if current:
            paragraphs.append(" ".join(current))

        return tuple(paragraphs)

    def _shorten(self, value: str, max_chars: int = 180) -> str:
        if len(value) <= max_chars:
            return value
        return f"{value[: max_chars - 3].rstrip()}..."
