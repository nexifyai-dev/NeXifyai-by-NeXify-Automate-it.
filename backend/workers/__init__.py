"""
NeXifyAI Worker & Scheduler Layer
Entkoppelt kritische Jobs vom FastAPI-Requestprozess:
- E-Mail-Versand
- KI-Tasks
- PDF-Generierung
- Reminder / Mahnvorstufen
- Follow-up-Logik
- Health-/Audit-Checks

Architektur:
  JobQueue → Worker-Pool (asyncio Tasks) → MongoDB Persistence
  Scheduler (APScheduler) → Cron-Jobs → JobQueue
  Dead-Letter-Queue für fehlgeschlagene Jobs
  Audit-Trail für jeden Job-Übergang
"""

from workers.job_queue import JobQueue, JobStatus, JobPriority
from workers.scheduler import WorkerScheduler
from workers.manager import WorkerManager

__all__ = [
    "JobQueue", "JobStatus", "JobPriority",
    "WorkerScheduler", "WorkerManager",
]
