"""Run async infrastructure from the synchronous runtime."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Coroutine
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class _AsyncJob:
    factory: Callable[[], Coroutine[Any, Any, Any]]
    future: Future[Any]


class AsyncBridge:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[_AsyncJob] | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._ready = threading.Event()

    def run(self, factory: Callable[[], Coroutine[Any, Any, T]]) -> T:
        loop, queue = self._ensure_worker()
        future: Future[T] = Future()

        def submit() -> None:
            queue.put_nowait(_AsyncJob(factory=factory, future=future))

        loop.call_soon_threadsafe(submit)
        return future.result()

    def _ensure_worker(self) -> tuple[asyncio.AbstractEventLoop, asyncio.Queue[_AsyncJob]]:
        with self._lock:
            if self._loop is not None and self._queue is not None:
                return self._loop, self._queue

            thread = threading.Thread(
                target=self._run_loop,
                name="zagent-async-bridge",
                daemon=True,
            )
            thread.start()
            self._thread = thread
        self._ready.wait()

        if self._loop is None or self._queue is None:
            raise RuntimeError("Async bridge worker failed to start")
        return self._loop, self._queue

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        queue: asyncio.Queue[_AsyncJob] = asyncio.Queue()

        with self._lock:
            self._loop = loop
            self._queue = queue
            self._ready.set()

        loop.create_task(self._worker(queue))
        loop.run_forever()

    async def _worker(self, queue: asyncio.Queue[_AsyncJob]) -> None:
        while True:
            job = await queue.get()
            if not job.future.set_running_or_notify_cancel():
                continue

            try:
                result = await job.factory()
            except Exception as error:
                job.future.set_exception(error)
            else:
                job.future.set_result(result)
