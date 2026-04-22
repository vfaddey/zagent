from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable

from zagent_launcher.application.errors import ProjectInitError
from zagent_launcher.application.interfaces import ProjectTemplateProvider


class BuiltinProjectTemplateProvider(ProjectTemplateProvider):
    def directories_for(self, template: str) -> tuple[str, ...]:
        template_root = self._template_root(template)
        return tuple(
            sorted(
                relative_path
                for relative_path, path in self._walk(template_root)
                if path.is_dir()
            )
        )

    def files_for(self, template: str) -> dict[str, str]:
        template_root = self._template_root(template)
        return {
            relative_path: path.read_text(encoding="utf-8")
            for relative_path, path in self._walk(template_root)
            if path.is_file() and not path.name.startswith(".")
        }

    def _template_root(self, template: str) -> Traversable:
        if template != "basic":
            raise ProjectInitError(f"Unknown project template: {template}")
        return files("zagent_launcher.infrastructure.config").joinpath(
            "template_files",
            template,
        )

    def _walk(
        self,
        root: Traversable,
        prefix: str = "",
    ) -> tuple[tuple[str, Traversable], ...]:
        items: list[tuple[str, Traversable]] = []
        for entry in sorted(root.iterdir(), key=lambda item: item.name):
            relative_path = f"{prefix}/{entry.name}" if prefix else entry.name
            items.append((relative_path, entry))
            if entry.is_dir():
                items.extend(self._walk(entry, relative_path))
        return tuple(items)
