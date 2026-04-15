"""Build prompt context use case."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from zagent_runtime.application.prompt_context import PromptContext, PromptDocumentRef
from zagent_runtime.application.runtime_context import RuntimeContext


class PromptDocumentLoader(Protocol):
    def read_text(self, path: Path) -> str: ...
    def title_for(self, path: Path) -> str: ...
    def display_path(self, path: Path, context: RuntimeContext) -> str: ...


class BuildPromptContext:
    def __init__(self, loader: PromptDocumentLoader) -> None:
        self._loader = loader

    def __call__(self, context: RuntimeContext) -> PromptContext:
        rules = self._document_refs(context, context.agent_env.rules)
        skills = self._document_refs(context, context.agent_env.skills)

        system_parts = self._system_parts(context)
        system_parts.append(self._index_section("Available Rules", rules))
        system_parts.append(self._index_section("Available Skills", skills))

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
            context.run_spec.task.description,
            f"Workspace: {context.run_spec.task.workspace}",
        ]
        if context.agent_env.prompts.task:
            parts.append(self._read_agent_env_file(context, context.agent_env.prompts.task))
        return "\n\n".join(parts)

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
                )
            )
        return tuple(refs)

    def _read_agent_env_file(self, context: RuntimeContext, relative_path: str) -> str:
        return self._loader.read_text(context.paths.agent_env_dir / relative_path)

    def _index_section(self, title: str, refs: tuple[PromptDocumentRef, ...]) -> str:
        if not refs:
            return f"# {title}\n\nNo documents configured."
        lines = [f"# {title}", ""]
        lines.extend(f"- {ref.title}: `{ref.path}`" for ref in refs)
        return "\n".join(lines)
