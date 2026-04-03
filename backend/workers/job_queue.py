"""
Async Job Queue mit Retry, Dead-Letter und MongoDB-Persistenz.
Kein externes Message-System nötig — läuft im selben Prozess,
aber vollständig entkoppelt vom Request-Thread.
"""

import asyncio
import logging
import traceback
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional
from domain import new_id, utcnow

logger = logging.getLogger("nexifyai.workers.queue")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class JobPriority(int, Enum):
    CRITICAL = 0   # Zahlungen, Webhooks
    HIGH = 1       # E-Mails, Statusänderungen
    NORMAL = 2     # KI-Tasks, PDF
    LOW = 3        # Analytics, Cleanup


class JobQueue:
    """
    In-process async job queue mit:
    - Priorität (asyncio.PriorityQueue)
    - Retry mit exponentiellem Backoff
    - Dead-Letter-Queue nach max_retries
    - MongoDB-Persistenz für Audit/History
    - Concurrent Worker-Pool
    """

    def __init__(self, db, max_workers: int = 4, max_retries: int = 3):
        self.db = db
        self.max_workers = max_workers
        self.max_retries = max_retries
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._handlers: Dict[str, Callable] = {}
        self._workers: list = []
        self._running = False
        self._stats = {
            "enqueued": 0, "completed": 0, "failed": 0,
            "retried": 0, "dead_letter": 0,
        }

    def register_handler(self, job_type: str, handler: Callable):
        """Handler für einen Job-Typ registrieren."""
        self._handlers[job_type] = handler
        logger.info(f"Job-Handler registriert: {job_type}")

    async def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        delay_seconds: int = 0,
        ref_id: str = "",
        ref_type: str = "",
        created_by: str = "system",
    ) -> str:
        """Job in die Queue legen. Gibt job_id zurück."""
        job_id = f"job_{new_id()}"
        now = utcnow()
        execute_after = now + timedelta(seconds=delay_seconds) if delay_seconds > 0 else now

        job = {
            "job_id": job_id,
            "job_type": job_type,
            "payload": payload,
            "priority": priority.value,
            "status": JobStatus.PENDING.value,
            "attempt": 0,
            "max_retries": self.max_retries,
            "execute_after": execute_after.isoformat(),
            "created_at": now.isoformat(),
            "created_by": created_by,
            "ref_id": ref_id,
            "ref_type": ref_type,
            "result": None,
            "error": None,
            "completed_at": None,
        }

        # MongoDB Persistenz
        await self.db.jobs.insert_one({**job, "_id": job_id})

        # In-Memory Queue (priority, timestamp für FIFO bei gleicher Prio, job)
        await self._queue.put((priority.value, now.timestamp(), job))
        self._stats["enqueued"] += 1

        logger.info(f"Job enqueued: {job_id} type={job_type} prio={priority.name} ref={ref_id}")
        return job_id

    async def start(self):
        """Worker-Pool starten."""
        if self._running:
            return
        self._running = True

        # Indexes
        await self.db.jobs.create_index("job_id", unique=True)
        await self.db.jobs.create_index("status")
        await self.db.jobs.create_index("job_type")
        await self.db.jobs.create_index("created_at")

        # Recovery: Pending/Running Jobs aus DB wiederherstellen
        await self._recover_jobs()

        # Worker-Tasks starten
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)

        logger.info(f"JobQueue gestartet: {self.max_workers} Worker")

    async def stop(self):
        """Worker-Pool stoppen."""
        self._running = False
        for task in self._workers:
            task.cancel()
        self._workers.clear()
        logger.info("JobQueue gestoppt")

    async def _recover_jobs(self):
        """Nicht abgeschlossene Jobs aus DB wiederherstellen (Crash-Recovery)."""
        count = 0
        async for job in self.db.jobs.find(
            {"status": {"$in": [JobStatus.PENDING.value, JobStatus.RETRYING.value]}},
            {"_id": 0}
        ):
            await self._queue.put((
                job.get("priority", 2),
                datetime.fromisoformat(job["created_at"]).timestamp(),
                job,
            ))
            count += 1
        if count > 0:
            logger.info(f"Recovery: {count} Jobs wiederhergestellt")

    async def _worker_loop(self, worker_id: int):
        """Einzelner Worker — verarbeitet Jobs aus der Queue."""
        while self._running:
            try:
                priority, ts, job = await asyncio.wait_for(
                    self._queue.get(), timeout=5.0
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            # Delay-Check
            execute_after = datetime.fromisoformat(job.get("execute_after", utcnow().isoformat()))
            now = utcnow()
            if execute_after > now:
                delay = (execute_after - now).total_seconds()
                if delay > 0:
                    await asyncio.sleep(min(delay, 60))
                    if not self._running:
                        break

            await self._process_job(worker_id, job)

    async def _process_job(self, worker_id: int, job: dict):
        """Einzelnen Job verarbeiten mit Retry-Logik."""
        job_id = job["job_id"]
        job_type = job["job_type"]
        attempt = job.get("attempt", 0) + 1

        handler = self._handlers.get(job_type)
        if not handler:
            logger.error(f"Kein Handler für Job-Typ: {job_type}")
            await self._mark_dead_letter(job, f"Kein Handler für {job_type}")
            return

        # Status → running
        await self.db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": JobStatus.RUNNING.value, "attempt": attempt,
                       "started_at": utcnow().isoformat(), "worker_id": worker_id}}
        )

        try:
            result = await handler(job["payload"], job)
            # Erfolg
            await self.db.jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": JobStatus.COMPLETED.value,
                    "result": str(result)[:2000] if result else "ok",
                    "completed_at": utcnow().isoformat(),
                    "error": None,
                }}
            )
            self._stats["completed"] += 1
            logger.info(f"Job abgeschlossen: {job_id} type={job_type} attempt={attempt}")

            # Timeline-Event
            await self._audit_job(job, "job_completed", {"attempt": attempt})

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            tb = traceback.format_exc()
            logger.error(f"Job fehlgeschlagen: {job_id} type={job_type} attempt={attempt} — {error_msg}")

            if attempt < job.get("max_retries", self.max_retries):
                # Retry mit exponentiellem Backoff
                backoff = min(300, 2 ** attempt * 5)  # 10s, 20s, 40s... max 5min
                retry_after = utcnow() + timedelta(seconds=backoff)
                job["attempt"] = attempt
                job["execute_after"] = retry_after.isoformat()

                await self.db.jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "status": JobStatus.RETRYING.value,
                        "attempt": attempt,
                        "error": error_msg,
                        "retry_after": retry_after.isoformat(),
                    },
                     "$push": {"error_log": {"attempt": attempt, "error": error_msg, "traceback": tb[:1000], "at": utcnow().isoformat()}}}
                )
                await self._queue.put((job.get("priority", 2), retry_after.timestamp(), job))
                self._stats["retried"] += 1
                await self._audit_job(job, "job_retrying", {"attempt": attempt, "backoff": backoff, "error": error_msg})
            else:
                await self._mark_dead_letter(job, error_msg)

    async def _mark_dead_letter(self, job: dict, error: str):
        """Job in Dead-Letter-Queue verschieben."""
        await self.db.jobs.update_one(
            {"job_id": job["job_id"]},
            {"$set": {
                "status": JobStatus.DEAD_LETTER.value,
                "error": error,
                "dead_letter_at": utcnow().isoformat(),
            }}
        )
        self._stats["dead_letter"] += 1
        self._stats["failed"] += 1

        await self._audit_job(job, "job_dead_letter", {"error": error})
        logger.error(f"Job → Dead-Letter: {job['job_id']} type={job['job_type']} error={error}")

    async def _audit_job(self, job: dict, action: str, details: dict = None):
        """Job-Event in Timeline schreiben."""
        try:
            await self.db.timeline_events.insert_one({
                "action": action,
                "ref_id": job.get("ref_id", job["job_id"]),
                "ref_type": job.get("ref_type", "job"),
                "user": job.get("created_by", "system"),
                "details": {
                    "job_id": job["job_id"],
                    "job_type": job["job_type"],
                    **(details or {}),
                },
                "timestamp": utcnow(),
            })
        except Exception as e:
            logger.error(f"Audit-Write fehlgeschlagen: {e}")

    def get_stats(self) -> dict:
        """Aktuelle Queue-Statistiken."""
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "workers_active": len(self._workers),
            "running": self._running,
            "registered_handlers": list(self._handlers.keys()),
        }
