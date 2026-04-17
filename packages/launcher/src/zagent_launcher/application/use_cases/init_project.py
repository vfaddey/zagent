from __future__ import annotations

from pathlib import Path

from zagent_launcher.application.dto import InitProjectRequest, InitProjectResult
from zagent_launcher.application.interfaces import ProjectTemplateProvider, ProjectWriter
from zagent_launcher.domain import ProjectLayout


class InitProject:
    _DIRECTORIES = (
        "prompts",
        "rules",
        "skills",
        "mcp",
        "files",
    )

    def __init__(
        self,
        template_provider: ProjectTemplateProvider,
        writer: ProjectWriter,
    ) -> None:
        self._template_provider = template_provider
        self._writer = writer

    def __call__(self, request: InitProjectRequest) -> InitProjectResult:
        layout = ProjectLayout.from_root(request.project_root)
        self._writer.ensure_dir(layout.agent_dir)
        for relative_dir in self._DIRECTORIES:
            self._writer.ensure_dir(layout.agent_dir / relative_dir)

        created: list[Path] = []
        overwritten: list[Path] = []
        skipped: list[Path] = []

        for relative_path, content in self._template_provider.files_for(request.template).items():
            result = self._writer.write_file(
                path=layout.agent_dir / relative_path,
                content=content,
                force=request.force,
            )
            match result.status:
                case "created":
                    created.append(result.path)
                case "overwritten":
                    overwritten.append(result.path)
                case "skipped":
                    skipped.append(result.path)

        return InitProjectResult(
            layout=layout,
            created=tuple(created),
            overwritten=tuple(overwritten),
            skipped=tuple(skipped),
        )
