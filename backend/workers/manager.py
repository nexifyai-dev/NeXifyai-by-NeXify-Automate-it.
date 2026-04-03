"""
WorkerManager — Zentrale Verwaltung von JobQueue + Scheduler.
Einstiegspunkt für server.py lifespan.
"""

import logging
from workers.job_queue import JobQueue, JobPriority
from workers.scheduler import WorkerScheduler
from workers.handlers import (
    init_handlers,
    handle_send_email,
    handle_payment_reminder,
    handle_dunning_escalation,
    handle_lead_followup,
    handle_booking_reminder,
    handle_quote_expiry,
    handle_ai_task,
    handle_status_transition,
)

logger = logging.getLogger("nexifyai.workers.manager")


class WorkerManager:
    """
    Lifecycle-Management für den gesamten Worker-Layer.
    Wird in server.py lifespan gestartet/gestoppt.
    """

    def __init__(self, db, max_workers: int = 4):
        self.db = db
        self.job_queue = JobQueue(db, max_workers=max_workers)
        self.scheduler = WorkerScheduler(db, self.job_queue)

    async def start(self):
        """Worker-Infrastruktur starten."""
        # Handler-DB-Kontext setzen
        init_handlers(self.db)

        # Handler registrieren
        self.job_queue.register_handler("send_email", handle_send_email)
        self.job_queue.register_handler("payment_reminder", handle_payment_reminder)
        self.job_queue.register_handler("dunning_escalation", handle_dunning_escalation)
        self.job_queue.register_handler("lead_followup", handle_lead_followup)
        self.job_queue.register_handler("booking_reminder", handle_booking_reminder)
        self.job_queue.register_handler("quote_expiry", handle_quote_expiry)
        self.job_queue.register_handler("ai_task", handle_ai_task)
        self.job_queue.register_handler("status_transition", handle_status_transition)

        # Queue starten (Worker-Pool)
        await self.job_queue.start()

        # Scheduler starten (Cron-Jobs)
        await self.scheduler.start()

        logger.info("WorkerManager gestartet: Queue + Scheduler aktiv")

    async def stop(self):
        """Worker-Infrastruktur stoppen."""
        await self.scheduler.stop()
        await self.job_queue.stop()
        logger.info("WorkerManager gestoppt")

    async def enqueue(self, job_type: str, payload: dict, **kwargs) -> str:
        """Shortcut: Job in die Queue legen."""
        return await self.job_queue.enqueue(job_type, payload, **kwargs)

    def get_status(self) -> dict:
        """Gesamtstatus von Queue + Scheduler."""
        return {
            "queue": self.job_queue.get_stats(),
            "scheduler": self.scheduler.get_status(),
        }
