"""Build prompt context use case."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_runtime.application.prompt_context import PromptContext, PromptDocumentRef
from zagent_runtime.application.runtime_context import RuntimeContext


class PromptDocumentLoader(Protocol):
    def read_text(self, path: Path) -> str: ...
    def title_for(self, path: Path) -> str: ...
    def description_for(self, path: Path) -> str: ...
    def display_path(self, path: Path, context: RuntimeContext) -> str: ...


class BuildPromptContext:
    def __init__(self, loader: PromptDocumentLoader) -> None:
        self._loader = loader

    def __call__(self, context: RuntimeContext) -> PromptContext:
        rules = self._document_refs(context, context.agent_env.rules)
        skills = self._document_refs(context, context.agent_env.skills)

        system_parts = self._system_parts(context)
        system_parts.append(
            self._catalog_section(
                heading="You have rules:",
                refs=rules,
                empty_message="No rule files configured.",
                instruction=(
                    "Use these rule files as additional guidance. Read a rule file before "
                    "applying it when it is relevant to the task."
                ),
            )
        )
        system_parts.append(
            self._catalog_section(
                heading="You have skills:",
                refs=skills,
                empty_message="No skill files configured.",
                instruction=(
                    "Skills are task-specific workflows. Read a skill file before using "
                    "that workflow."
                ),
            )
        )

        return PromptContext(
            system_message="\n\n".join(part for part in system_parts if part),
            task_message=self._task_message(context),
            rules=rules,
            skills=skills,
        )

    def _system_parts(self, context: RuntimeContext) -> list[str]:
        parts: list[str] = []
        prompts = context.agent_env.prompts
        if prompts.system:
            parts.append(self._read_agent_env_file(context, prompts.system))
        if prompts.developer:
            parts.append(self._read_agent_env_file(context, prompts.developer))
        return parts

    def _task_message(self, context: RuntimeContext) -> str:
        parts = [
            f"# Task: {context.run_spec.task.title}",
            self._task_prompt(context),
            f"Workspace: {context.run_spec.task.workspace}",
        ]
        return "\n\n".join(parts)

    def _task_prompt(self, context: RuntimeContext) -> str:
        if context.run_spec.task.prompt is not None:
            return context.run_spec.task.prompt
        if context.run_spec.task.prompt_file is not None:
            path = Path(context.run_spec.task.prompt_file).expanduser()
            if not path.is_absolute():
                path = context.paths.run_spec_file.parent / path
            return self._loader.read_text(path)
        raise ValueError("Task must define prompt or prompt_file.")

    def _document_refs(
        self,
        context: RuntimeContext,
        relative_paths: tuple[str, ...],
    ) -> tuple[PromptDocumentRef, ...]:
        refs: list[PromptDocumentRef] = []
        for relative_path in relative_paths:
            path = context.paths.agent_env_dir / relative_path
            refs.append(
                PromptDocumentRef(
                    title=self._loader.title_for(path),
                    path=self._loader.display_path(path, context),
                    description=self._loader.description_for(path),
                )
            )
        return tuple(refs)

    def _read_agent_env_file(self, context: RuntimeContext, relative_path: str) -> str:
        return self._loader.read_text(context.paths.agent_env_dir / relative_path)

    def _catalog_section(
        self,
        heading: str,
        refs: tuple[PromptDocumentRef, ...],
        empty_message: str,
        instruction: str,
    ) -> str:
        if not refs:
            return f"# {heading}\n\n{empty_message}"

        lines = [f"# {heading}", "", instruction, ""]
        lines.extend(
            f"- `{ref.path}` - {ref.title}: {ref.description}"
            for ref in refs
        )
        return "\n".join(lines)
