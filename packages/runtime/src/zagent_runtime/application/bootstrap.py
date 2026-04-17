"""Runtime bootstrap use case."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from zagent_runtime.application.build_runtime_context import BuildRuntimeContext
from zagent_runtime.application.collect_result import CollectResult
from zagent_runtime.application.create_agent import CreateAgent
from zagent_runtime.application.execute_task import ExecuteTask
from zagent_runtime.application.observe_run import RunObserverPort
from zagent_runtime.application.runtime_context import RuntimeContext, RuntimePaths
from zagent_runtime.domain.observability import ChatMessage, ChatRole, RunEvent
from zagent_runtime.domain.run import ResultStatus, RunPhase, RunResult, RunState, RunStatus


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    exit_code: int
    result: RunResult


class BootstrapRun:
    def __init__(
        self,
        build_runtime_context: BuildRuntimeContext,
        create_agent: CreateAgent,
        execute_task: ExecuteTask,
        collect_result: CollectResult,
        observer: RunObserverPort,
    ) -> None:
        self._build_runtime_context = build_runtime_context
        self._create_agent = create_agent
        self._execute_task = execute_task
        self._collect_result = collect_result
        self._observer = observer

    def __call__(self, run_spec_file: Path, continue_msg: str | None = None) -> BootstrapResult:
        context = self._build_runtime_context(run_spec_file)
        started_at = self._now()
        self._start_run(context.paths, context.run_spec.run_id, started_at)

        try:
            session = self._create_agent(context)
            if continue_msg is None:
                self._write_initial_messages(
                    context.paths,
                    session.prompt.system_message,
                    session.prompt.task_message,
                )
            else:
                self._observer.on_message(
                    context.paths,
                    ChatMessage(ts=self._now(), role=ChatRole.USER, content=continue_msg),
                )
            self._change_phase(
                paths=context.paths,
                run_id=context.run_spec.run_id,
                phase=RunPhase.EXECUTING,
                started_at=started_at,
                event="task_started",
            )

            result = self._execute_task(context, session, continue_msg)
            result = self._complete_result(result)
            self._observer.on_message(
                context.paths,
                ChatMessage(
                    ts=self._now(),
                    role=ChatRole.ASSISTANT,
                    content=result.final_message,
                ),
            )
            self._change_phase(
                paths=context.paths,
                run_id=context.run_spec.run_id,
                phase=RunPhase.COLLECTING_RESULT,
                started_at=started_at,
                event="result_collecting",
            )
            self._collect_result(context, result)
            self._finish_run(
                paths=context.paths,
                run_id=context.run_spec.run_id,
                started_at=started_at,
                result=result,
            )
            return BootstrapResult(exit_code=self._exit_code(result), result=result)
        except Exception as error:
            result = self._failure_result(
                run_id=context.run_spec.run_id,
                final_marker=context.run_spec.runtime.final_marker,
                error=error,
            )
            self._try_collect_failure_result(context, result)
            self._finish_failed_run(
                paths=context.paths,
                run_id=context.run_spec.run_id,
                started_at=started_at,
                result=result,
            )
            return BootstrapResult(exit_code=1, result=result)

    def _start_run(self, paths: RuntimePaths, run_id: str, started_at: datetime) -> None:
        self._observer.on_run_started(
            paths=paths,
            state=self._state(
                run_id=run_id,
                status=RunStatus.RUNNING,
                phase=RunPhase.INITIALIZING_AGENT,
                started_at=started_at,
                artifacts=(),
            ),
            event=RunEvent(ts=started_at, event="run_started", payload={"run_id": run_id}),
        )

    def _write_initial_messages(
        self,
        paths: RuntimePaths,
        system_message: str,
        task_message: str,
    ) -> None:
        self._observer.on_message(
            paths,
            ChatMessage(ts=self._now(), role=ChatRole.SYSTEM, content=system_message),
        )
        self._observer.on_message(
            paths,
            ChatMessage(ts=self._now(), role=ChatRole.USER, content=task_message),
        )

    def _change_phase(
        self,
        paths: RuntimePaths,
        run_id: str,
        phase: RunPhase,
        started_at: datetime,
        event: str,
    ) -> None:
        self._observer.on_phase_changed(
            paths=paths,
            state=self._state(
                run_id=run_id,
                status=RunStatus.RUNNING,
                phase=phase,
                started_at=started_at,
                artifacts=(),
            ),
            event=RunEvent(ts=self._now(), event=event),
        )

    def _finish_run(
        self,
        paths: RuntimePaths,
        run_id: str,
        started_at: datetime,
        result: RunResult,
    ) -> None:
        self._observer.on_run_finished(
            paths=paths,
            state=self._state(
                run_id=run_id,
                status=self._run_status(result.status),
                phase=RunPhase.FINISHED,
                started_at=started_at,
                artifacts=result.artifacts,
            ),
            event=RunEvent(
                ts=self._now(),
                event="run_finished",
                payload={"status": result.status.value},
            ),
        )

    def _finish_failed_run(
        self,
        paths: RuntimePaths,
        run_id: str,
        started_at: datetime,
        result: RunResult,
    ) -> None:
        self._observer.on_run_finished(
            paths=paths,
            state=self._state(
                run_id=run_id,
                status=RunStatus.FAILED,
                phase=RunPhase.FINISHED,
                started_at=started_at,
                artifacts=result.artifacts,
            ),
            event=RunEvent(
                ts=self._now(),
                event="run_failed",
                payload={
                    "status": ResultStatus.FAILURE.value,
                    "error": result.error,
                },
            ),
        )

    def _state(
        self,
        run_id: str,
        status: RunStatus,
        phase: RunPhase,
        started_at: datetime,
        artifacts: tuple[str, ...],
    ) -> RunState:
        return RunState(
            run_id=run_id,
            status=status,
            phase=phase,
            started_at=started_at,
            updated_at=self._now(),
            artifacts=artifacts,
        )

    def _complete_result(self, result: RunResult) -> RunResult:
        if result.artifacts:
            return result
        return replace(result, artifacts=("result.json", "summary.md"))

    def _failure_result(self, run_id: str, final_marker: str, error: Exception) -> RunResult:
        error_message = str(error)
        return RunResult(
            run_id=run_id,
            status=ResultStatus.FAILURE,
            summary=error_message,
            final_message=f"Run failed: {error_message}\n\n{final_marker}",
            artifacts=("result.json", "summary.md"),
            error=error_message,
        )

    def _try_collect_failure_result(self, context: RuntimeContext, result: RunResult) -> None:
        try:
            self._collect_result(context, result)
        except Exception:
            return

    def _run_status(self, status: ResultStatus) -> RunStatus:
        if status is ResultStatus.SUCCESS:
            return RunStatus.SUCCEEDED
        if status is ResultStatus.CANCELED:
            return RunStatus.CANCELED
        return RunStatus.FAILED

    def _exit_code(self, result: RunResult) -> int:
        if result.status is ResultStatus.SUCCESS:
            return 0
        return 1

    def _now(self) -> datetime:
        return datetime.now(UTC)
