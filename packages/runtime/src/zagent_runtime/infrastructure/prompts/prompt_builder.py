"""Runtime prompt builder adapter."""

from __future__ import annotations

from zagent_runtime.application.build_prompt_context import BuildPromptContext
from zagent_runtime.application.prompt_context import PromptContext
from zagent_runtime.application.runtime_context import RuntimeContext


class RuntimePromptBuilder:
    def __init__(self, build_prompt_context: BuildPromptContext) -> None:
        self._build_prompt_context = build_prompt_context

    def build(self, context: RuntimeContext) -> PromptContext:
        return self._build_prompt_context(context)
