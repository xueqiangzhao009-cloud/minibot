"""Cron service for minibot."""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Optional, Callable

from minibot.cron.types import CronJob, CronStore


class CronService:
    """Cron service for scheduling and executing tasks."""

    def __init__(self, store_path: Path):
        """
        Initialize the cron service.

        Args:
            store_path: Path to the cron store file.
        """
        self.store_path = store_path
        self.store = self._load_store()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self.on_job: Optional[Callable[[CronJob], None]] = None

    def _load_store(self) -> CronStore:
        """Load the cron store from file."""
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return CronStore(
                    version=data.get("version", 1),
                    jobs=[CronJob.from_dict(job) for job in data.get("jobs", [])]
                )
            except Exception:
                pass
        return CronStore()

    def _save_store(self) -> None:
        """Save the cron store to file."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.store.version,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "enabled": job.enabled,
                    "schedule": {
                        "kind": job.schedule.kind,
                        "at_ms": job.schedule.at_ms,
                        "every_ms": job.schedule.every_ms,
                        "expr": job.schedule.expr,
                        "tz": job.schedule.tz
                    },
                    "payload": {
                        "kind": job.payload.kind,
                        "message": job.payload.message,
                        "deliver": job.payload.deliver,
                        "channel": job.payload.channel,
                        "to": job.payload.to
                    },
                    "state": {
                        "next_run_at_ms": job.state.next_run_at_ms,
                        "last_run_at_ms": job.state.last_run_at_ms,
                        "last_status": job.state.last_status,
                        "last_error": job.state.last_error,
                        "run_history": [
                            {
                                "run_at_ms": record.run_at_ms,
                                "status": record.status,
                                "duration_ms": record.duration_ms,
                                "error": record.error
                            }
                            for record in job.state.run_history
                        ]
                    },
                    "created_at_ms": job.created_at_ms,
                    "updated_at_ms": job.updated_at_ms,
                    "delete_after_run": job.delete_after_run
                }
                for job in self.store.jobs
            ]
        }
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def register_job(self, job: CronJob) -> None:
        """Register a new cron job."""
        # Check if job already exists
        existing_job = next((j for j in self.store.jobs if j.id == job.id), None)
        if existing_job:
            # Update existing job
            existing_job.name = job.name
            existing_job.enabled = job.enabled
            existing_job.schedule = job.schedule
            existing_job.payload = job.payload
            existing_job.updated_at_ms = int(time.time() * 1000)
        else:
            # Add new job
            job.created_at_ms = int(time.time() * 1000)
            job.updated_at_ms = job.created_at_ms
            self.store.jobs.append(job)
        self._save_store()

    def register_system_job(self, job: CronJob) -> None:
        """Register a system job (always enabled)."""
        job.enabled = True
        self.register_job(job)

    def unregister_job(self, job_id: str) -> None:
        """Unregister a cron job."""
        self.store.jobs = [job for job in self.store.jobs if job.id != job_id]
        self._save_store()

    def list_jobs(self) -> List[CronJob]:
        """List all cron jobs."""
        return self.store.jobs

    def status(self) -> dict:
        """Get the status of the cron service."""
        return {
            "jobs": len(self.store.jobs),
            "enabled_jobs": len([job for job in self.store.jobs if job.enabled])
        }

    async def start(self) -> None:
        """Start the cron service."""
        self._running = True
        self._tasks.append(asyncio.create_task(self._run()))

    async def stop(self) -> None:
        """Stop the cron service."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _run(self) -> None:
        """Main cron loop."""
        while self._running:
            try:
                await self._check_jobs()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _check_jobs(self) -> None:
        """Check and execute jobs that are due."""
        now_ms = int(time.time() * 1000)
        for job in self.store.jobs:
            if not job.enabled:
                continue
            if self._should_run(job, now_ms):
                await self._execute_job(job, now_ms)

    def _should_run(self, job: CronJob, now_ms: int) -> bool:
        """Check if a job should run."""
        if job.state.next_run_at_ms is None:
            # Calculate next run time
            job.state.next_run_at_ms = self._calculate_next_run(job, now_ms)
        return now_ms >= job.state.next_run_at_ms

    def _calculate_next_run(self, job: CronJob, now_ms: int) -> int:
        """Calculate the next run time for a job."""
        if job.schedule.kind == "at":
            return job.schedule.at_ms or now_ms
        elif job.schedule.kind == "every":
            return now_ms + (job.schedule.every_ms or 60000)  # Default 1 minute
        elif job.schedule.kind == "cron":
            # Simple implementation for cron expressions
            # For production, use a proper cron library
            return now_ms + 60000  # Default 1 minute
        return now_ms + 60000

    async def _execute_job(self, job: CronJob, now_ms: int) -> None:
        """Execute a cron job."""
        start_ms = now_ms
        try:
            if self.on_job:
                await self.on_job(job)
            job.state.last_run_at_ms = now_ms
            job.state.last_status = "ok"
            job.state.last_error = None
            job.state.run_history.append(
                CronRunRecord(
                    run_at_ms=now_ms,
                    status="ok",
                    duration_ms=now_ms - start_ms
                )
            )
        except Exception as e:
            job.state.last_run_at_ms = now_ms
            job.state.last_status = "error"
            job.state.last_error = str(e)
            job.state.run_history.append(
                CronRunRecord(
                    run_at_ms=now_ms,
                    status="error",
                    duration_ms=now_ms - start_ms,
                    error=str(e)
                )
            )
        finally:
            # Calculate next run time
            job.state.next_run_at_ms = self._calculate_next_run(job, now_ms)
            job.updated_at_ms = now_ms
            if job.delete_after_run:
                self.unregister_job(job.id)
            else:
                self._save_store()
