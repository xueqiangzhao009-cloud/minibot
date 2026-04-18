"""Heartbeat service - periodic agent wake-up to check for tasks."""

import asyncio
from pathlib import Path
from typing import Callable, Coroutine, Any

from minibot.providers.base import LLMProvider


class HeartbeatService:
    """
    Periodic heartbeat service that wakes the agent to check for tasks.

    Reads HEARTBEAT.md and decides whether there are active tasks.
    If tasks are found, executes them through the provided callback.
    """

    def __init__(
        self,
        workspace: Path,
        provider: LLMProvider,
        model: str,
        on_execute: Callable[[str], Coroutine[Any, Any, str]] | None = None,
        on_notify: Callable[[str], Coroutine[Any, Any, None]] | None = None,
        interval_s: int = 30 * 60,
        enabled: bool = True,
        timezone: str | None = None,
    ):
        self.workspace = workspace
        self.provider = provider
        self.model = model
        self.on_execute = on_execute
        self.on_notify = on_notify
        self.interval_s = interval_s
        self.enabled = enabled
        self.timezone = timezone
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def heartbeat_file(self) -> Path:
        return self.workspace / "HEARTBEAT.md"

    def _read_heartbeat_file(self) -> str | None:
        if self.heartbeat_file.exists():
            try:
                return self.heartbeat_file.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    async def _decide(self, content: str) -> tuple[str, str]:
        """Decide whether to run tasks based on HEARTBEAT.md content.

        Returns (action, tasks) where action is 'skip' or 'run'.
        """
        # Simple implementation: if content is not empty, run tasks
        # For production, use LLM to make the decision
        if content.strip():
            return "run", content
        return "skip", ""

    async def start(self) -> None:
        """Start the heartbeat service."""
        if not self.enabled:
            return
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self) -> None:
        """Stop the heartbeat service."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_s)
                if self._running:
                    await self._tick()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _tick(self) -> None:
        """Execute a single heartbeat tick."""
        content = self._read_heartbeat_file()
        if not content:
            return

        try:
            action, tasks = await self._decide(content)

            if action != "run":
                return

            if self.on_execute:
                response = await self.on_execute(tasks)

                if response and self.on_notify:
                    await self.on_notify(response)
        except Exception:
            pass

    async def trigger_now(self) -> str | None:
        """Manually trigger a heartbeat."""
        content = self._read_heartbeat_file()
        if not content:
            return None
        action, tasks = await self._decide(content)
        if action != "run" or not self.on_execute:
            return None
        return await self.on_execute(tasks)
