"""Built-in .zagent project templates."""

from __future__ import annotations

from importlib.resources import files

from zagent_launcher.application.errors import ProjectInitError
from zagent_launcher.application.interfaces import ProjectTemplateProvider

_TEMPLATE_FILES = {
    "run.yaml": "run.yaml",
    "prompts/system.md": "prompts/system.md",
    "prompts/task.md": "prompts/task.md",
    "rules/global.md": "rules/global.md",
}


class BuiltinProjectTemplateProvider(ProjectTemplateProvider):
    """Template provider for launcher init."""

    def files_for(self, template: str) -> dict[str, str]:
        if template != "basic":
            raise ProjectInitError(f"Unknown project template: {template}")
        return {
            target_path: self._read_template(template, source_path)
            for target_path, source_path in _TEMPLATE_FILES.items()
        }

    def _read_template(self, template: str, source_path: str) -> str:
        return (
            files("zagent_launcher.infrastructure.config")
            .joinpath("template_files", template, source_path)
            .read_text(encoding="utf-8")
        )
