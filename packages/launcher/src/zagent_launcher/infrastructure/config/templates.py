from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from zagent_launcher.application.errors import ProjectInitError
from zagent_launcher.application.interfaces import ProjectTemplateProvider


class BuiltinProjectTemplateProvider(ProjectTemplateProvider):
    def directories_for(self, template: str) -> tuple[str, ...]:
        template_root = self._template_root(template)
        return tuple(
            sorted(
                self._relative_path(template_root, path)
                for path in template_root.rglob("*")
                if path.is_dir()
            )
        )

    def files_for(self, template: str) -> dict[str, str]:
        template_root = self._template_root(template)
        return {
            self._relative_path(template_root, path): path.read_text(encoding="utf-8")
            for path in sorted(template_root.rglob("*"))
            if path.is_file() and not path.name.startswith(".")
        }

    def _template_root(self, template: str) -> Path:
        if template != "basic":
            raise ProjectInitError(f"Unknown project template: {template}")
        return Path(files("zagent_launcher.infrastructure.config")).joinpath(
            "template_files",
            template
        )

    def _relative_path(self, template_root: Path, path: Path) -> str:
        return path.relative_to(template_root).as_posix()
