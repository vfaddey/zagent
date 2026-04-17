"""Runtime prompt builder adapter."""

from __future__ import annotations

from zagent_runtime.application.dto.prompt_context import PromptContext
from zagent_runtime.application.dto.runtime_context import RuntimeContext
from zagent_runtime.application.use_cases.build_prompt_context import BuildPromptContext


class RuntimePromptBuilder:
    def __init__(self, build_prompt_context: BuildPromptContext) -> None:
        self._build_prompt_context = build_prompt_context

    def build(self, context: RuntimeContext) -> PromptContext:
        return self._build_prompt_context(context)
