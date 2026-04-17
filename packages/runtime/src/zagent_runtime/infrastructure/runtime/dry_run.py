"""Dry-run runtime backend."""

from __future__ import annotations

from dataclasses import dataclass

from zagent_runtime.application.create_agent import AgentSession
from zagent_runtime.application.prompt_context import PromptContext
from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.run import ResultStatus, RunResult


@dataclass(frozen=True, slots=True)
class DryRunAgentBundle:
    prompt: PromptContext


class DryRunAgentFactory:
    def create(self, context: RuntimeContext, prompt: PromptContext) -> DryRunAgentBundle:
        return DryRunAgentBundle(prompt=prompt)


class DryRunExecutor:
    def run(
        self, context: RuntimeContext, session: AgentSession, continue_msg: str | None = None
    ) -> RunResult:
        final_message = (
            "Dry run completed. Runtime configuration, prompt building, and tool "
            f"registration succeeded.\n\n{context.run_spec.runtime.final_marker}"
        )
        return RunResult(
            run_id=context.run_spec.run_id,
            status=ResultStatus.SUCCESS,
            summary="Dry run completed.",
            final_message=final_message,
        )
