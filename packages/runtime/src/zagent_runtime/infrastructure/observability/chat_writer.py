"""Chat JSONL writer."""

from __future__ import annotations

from zagent_runtime.application.runtime_context import RuntimePaths
from zagent_runtime.domain.observability import ChatMessage
from zagent_runtime.infrastructure.observability.jsonl_writer import JsonlWriter


class ChatWriter:
    """Write chat messages to chat.jsonl."""

    def __init__(self, writer: JsonlWriter) -> None:
        self._writer = writer

    def write(self, paths: RuntimePaths, message: ChatMessage) -> None:
        self._writer.append(paths.chat_file, message)
