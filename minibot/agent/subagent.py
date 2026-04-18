"""Subagent manager for background task execution."""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Awaitable

from loguru import logger


@dataclass
class SubagentStatus:
    """Real-time status of a running subagent."""

    task_id: str
    label: str
    task_description: str
    started_at: float
    phase: str = "initializing"
    iteration: int = 0
    tool_events: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    stop_reason: str | None = None
    error: str | None = None


class _SubagentHook:
    """Hook for subagent execution."""

    def __init__(self, task_id: str, status: SubagentStatus | None = None) -> None:
        self._task_id = task_id
        self._status = status

    async def before_execute_tools(self, context: Any) -> None:
        for tool_call in context.tool_calls:
            args_str = json.dumps(tool_call.arguments, ensure_ascii=False)
            logger.debug(
                "Subagent [{}] executing: {} with arguments: {}",
                self._task_id, tool_call.name, args_str,
            )

    async def after_iteration(self, context: Any) -> None:
        if self._status is None:
            return
        self._status.iteration = context.iteration
        self._status.tool_events = list(context.tool_events)
        self._status.usage = dict(context.usage)
        if context.error:
            self._status.error = str(context.error)


class SubagentManager:
    """Manages background subagent execution."""

    def __init__(
        self,
        agent_loop: Any,
        workspace: Path,
        max_tool_result_chars: int = 4000,
        restrict_to_workspace: bool = False,
        disabled_skills: list[str] | None = None,
    ):
        self.agent_loop = agent_loop
        self.workspace = workspace
        self.max_tool_result_chars = max_tool_result_chars
        self.restrict_to_workspace = restrict_to_workspace
        self.disabled_skills = set(disabled_skills or [])
        self._running_tasks: dict[str, asyncio.Task[None]] = {}
        self._task_statuses: dict[str, SubagentStatus] = {}
        self._session_tasks: dict[str, set[str]] = {}

    async def spawn(
        self,
        task: str,
        label: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
        session_key: str | None = None,
        on_result: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        """Spawn a subagent to execute a task in the background."""
        task_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")

        status = SubagentStatus(
            task_id=task_id,
            label=display_label,
            task_description=task,
            started_at=time.monotonic(),
        )
        self._task_statuses[task_id] = status

        bg_task = asyncio.create_task(
            self._run_subagent(
                task_id, task, display_label, origin_channel, origin_chat_id, status, on_result
            )
        )
        self._running_tasks[task_id] = bg_task
        if session_key:
            self._session_tasks.setdefault(session_key, set()).add(task_id)

        def _cleanup(_: asyncio.Task) -> None:
            self._running_tasks.pop(task_id, None)
            self._task_statuses.pop(task_id, None)
            if session_key and (ids := self._session_tasks.get(session_key)):
                ids.discard(task_id)
                if not ids:
                    del self._session_tasks[session_key]

        bg_task.add_done_callback(_cleanup)

        logger.info("Spawned subagent [{}]: {}", task_id, display_label)
        return f"Subagent [{display_label}] started (id: {task_id}). I'll notify you when it completes."

    async def _run_subagent(
        self,
        task_id: str,
        task: str,
        label: str,
        origin_channel: str,
        origin_chat_id: str,
        status: SubagentStatus,
        on_result: Callable[[str], Awaitable[None]] | None,
    ) -> None:
        """Execute the subagent task and announce the result."""
        logger.info("Subagent [{}] starting task: {}", task_id, label)

        try:
            result_content = await self.agent_loop.run_task(
                task,
                session_key=f"subagent:{task_id}",
            )

            status.phase = "done"
            status.stop_reason = "completed"

            if on_result:
                await on_result(result_content)
            else:
                result_msg = f"[Subagent {label}] completed:\n{result_content}"
                logger.info("Subagent [{}] completed successfully", task_id)

        except Exception as e:
            status.phase = "error"
            status.error = str(e)
            logger.error("Subagent [{}] failed: {}", task_id, e)

            error_msg = f"[Subagent {label}] failed: {e}"
            if on_result:
                await on_result(error_msg)

    async def cancel_by_session(self, session_key: str) -> int:
        """Cancel all subagents for the given session. Returns count cancelled."""
        tasks = [
            self._running_tasks[tid]
            for tid in self._session_tasks.get(session_key, [])
            if tid in self._running_tasks and not self._running_tasks[tid].done()
        ]
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        return len(tasks)

    def get_running_count(self) -> int:
        """Return the number of currently running subagents."""
        return len(self._running_tasks)

    def get_running_count_by_session(self, session_key: str) -> int:
        """Return the number of currently running subagents for a session."""
        tids = self._session_tasks.get(session_key, set())
        return sum(
            1 for tid in tids
            if tid in self._running_tasks and not self._running_tasks[tid].done()
        )

    def get_status(self, task_id: str) -> SubagentStatus | None:
        """Get the status of a subagent task."""
        return self._task_statuses.get(task_id)

    def get_all_statuses(self) -> dict[str, SubagentStatus]:
        """Get all subagent statuses."""
        return dict(self._task_statuses)
