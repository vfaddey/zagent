"""AG2 run executor."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from zagent_runtime.application.create_agent import AgentSession
from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.run import ResultStatus, RunResult
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentBundle


class Ag2RunExecutor:
    """Execute an AG2 agent session with bounded turns."""

    def run(self, context: RuntimeContext, session: AgentSession) -> RunResult:
        bundle = self._bundle(session)
        response = bundle.executor.run(
            recipient=bundle.assistant,
            message=self._task_message(session, context.run_spec.runtime.final_marker),
            max_turns=context.run_spec.runtime.max_turns,
            summary_method="last_msg",
            user_input=False,
        )
        response.process()

        final_message = self._final_message(response)
        final_message = self._ensure_final_marker(
            final_message,
            context.run_spec.runtime.final_marker,
        )

        return RunResult(
            run_id=context.run_spec.run_id,
            status=ResultStatus.SUCCESS,
            summary=self._summary(response, final_message),
            final_message=final_message,
        )

    def _bundle(self, session: AgentSession) -> Ag2AgentBundle:
        backend = session.backend
        if not isinstance(backend, Ag2AgentBundle):
            raise TypeError(f"Unsupported AG2 backend: {type(backend)}")
        return backend

    def _task_message(self, session: AgentSession, final_marker: str) -> str:
        return "\n\n".join(
            (
                session.prompt.task_message,
                "When the task is complete, finish your final response with "
                f"`{final_marker}` and include a concise summary of what you did.",
            )
        )

    def _summary(self, response: object, final_message: str) -> str:
        summary = getattr(response, "summary", None)
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        return final_message

    def _final_message(self, response: object) -> str:
        messages = getattr(response, "messages", None)
        if isinstance(messages, Sequence):
            for message in reversed(messages):
                content = self._message_content(message)
                if content:
                    return content

        summary = getattr(response, "summary", None)
        if isinstance(summary, str) and summary.strip():
            return summary.strip()

        return "Run finished."

    def _message_content(self, message: object) -> str | None:
        if isinstance(message, Mapping):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()

        return None

    def _ensure_final_marker(self, message: str, final_marker: str) -> str:
        stripped = message.strip()
        if final_marker in stripped:
            return stripped
        return f"{stripped}\n\n{final_marker}"
