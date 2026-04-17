"""AG2 run executor."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from zagent_runtime.application.create_agent import AgentSession
from zagent_runtime.application.observe_run import RunObserverPort
from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.observability import RunEvent
from zagent_runtime.domain.run import ResultStatus, RunResult
from zagent_runtime.infrastructure.ag2.agent_factory import Ag2AgentBundle
from zagent_runtime.infrastructure.async_bridge import AsyncBridge


class Ag2RunExecutor:
    def __init__(self, async_bridge: AsyncBridge, observer: RunObserverPort) -> None:
        self._async_bridge = async_bridge
        self._observer = observer

    def run(
        self, context: RuntimeContext, session: AgentSession, continue_msg: str | None = None
    ) -> RunResult:
        bundle = self._bundle(session)
        history_file = context.paths.ag2_history_file

        try:
            if continue_msg is not None:
                self._load_state(bundle, history_file)
                message = continue_msg
                clear_history = False
            else:
                bundle.assistant.update_system_message(
                    bundle.assistant.system_message
                    + "\n\n"
                    + self._completion_protocol(context.run_spec.runtime.final_marker)
                )
                message = session.prompt.task_message
                clear_history = True

            response = bundle.executor.run(
                recipient=bundle.assistant,
                message=message,
                clear_history=clear_history,
                max_turns=context.run_spec.runtime.max_turns,
                summary_method="last_msg",
                user_input=False,
            )
            if hasattr(response, "process"):
                response.process()

            self._save_state(bundle, history_file)

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
        finally:
            self._close_mcp_toolkits(context, bundle)

    def _bundle(self, session: AgentSession) -> Ag2AgentBundle:
        backend = session.backend
        if not isinstance(backend, Ag2AgentBundle):
            raise TypeError(f"Unsupported AG2 backend: {type(backend)}")
        return backend

    def _completion_protocol(self, final_marker: str) -> str:
        return "\n".join(
            (
                "# Completion Protocol",
                "",
                f"When you are done, your final response must end with `{final_marker}`.",
                "If you do not have enough context, permissions, tools, or data to complete "
                "the task, do not keep trying blindly. Explain what is missing, provide the "
                "best useful answer you can, and end that response with "
                f"`{final_marker}`.",
                "A text-only answer is a valid final result only when it ends with "
                f"`{final_marker}`.",
                "There is no human user in this chat. Do not ask questions or wait for responses.",
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

    def _close_mcp_toolkits(self, context: RuntimeContext, bundle: Ag2AgentBundle) -> None:
        for toolkit in reversed(bundle.mcp_toolkits):
            self._emit_event(context, "mcp_server_disconnecting", {"server": toolkit.server_name})
            try:
                self._async_bridge.run(toolkit.aclose)
            except Exception as error:
                self._emit_event(
                    context,
                    "mcp_server_disconnect_failed",
                    {"server": toolkit.server_name, "error": str(error)},
                )
                raise

            self._emit_event(context, "mcp_server_disconnected", {"server": toolkit.server_name})

    def _emit_event(self, context: RuntimeContext, event: str, payload: dict[str, object]) -> None:
        self._observer.on_event(
            context.paths,
            RunEvent(
                ts=datetime.now(UTC),
                event=event,
                payload=payload,
            ),
        )

    def _save_state(self, bundle: Ag2AgentBundle, history_file: Path) -> None:
        state = {
            "assistant_messages": bundle.assistant.chat_messages.get(bundle.executor, []),
            "executor_messages": bundle.executor.chat_messages.get(bundle.assistant, []),
        }
        with history_file.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _load_state(self, bundle: Ag2AgentBundle, history_file: Path) -> None:
        if not history_file.exists():
            return
        with history_file.open("r", encoding="utf-8") as f:
            state = json.load(f)

        bundle.assistant.chat_messages[bundle.executor] = state.get("assistant_messages", [])
        bundle.executor.chat_messages[bundle.assistant] = state.get("executor_messages", [])
