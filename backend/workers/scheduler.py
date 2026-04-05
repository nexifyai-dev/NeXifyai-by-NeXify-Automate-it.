"""
APScheduler-basierter Cron-Scheduler für wiederkehrende Jobs.
Entkoppelt vom Request-Prozess.

Geplante Jobs:
- Zahlungsreminder (Rechnungen fällig/überfällig)
- Mahnvorstufen (1., 2., 3. Mahnung)
- Follow-up-Reminder für Leads
- Buchungs-Erinnerungen
- Health-/Audit-Checks
- Quote-Ablauf-Prüfung
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from domain import utcnow

logger = logging.getLogger("nexifyai.workers.scheduler")


class WorkerScheduler:
    """Zentraler Scheduler — delegiert an JobQueue."""

    def __init__(self, db, job_queue):
        self.db = db
        self.job_queue = job_queue
        self.scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
        self._job_registry = {}
        self._oracle_engine = None

    async def start(self):
        """Scheduler mit allen geplanten Jobs starten."""
        # Oracle Engine initialisieren
        from services.oracle_engine import OracleEngine
        self._oracle_engine = OracleEngine(self.db)
        await self._oracle_engine.start()

        # --- Oracle Task-Processing: alle 90 Sekunden ---
        self.scheduler.add_job(
            self._oracle_process_cycle,
            IntervalTrigger(seconds=90),
            id="oracle_process",
            name="Oracle Task-Processing",
            replace_existing=True,
        )

        # --- Oracle Knowledge-Sync: alle 30 Minuten ---
        self.scheduler.add_job(
            self._oracle_knowledge_sync,
            IntervalTrigger(minutes=30),
            id="oracle_knowledge_sync",
            name="Oracle Knowledge-Sync",
            replace_existing=True,
        )

        # --- Oracle Task-Derivation: alle 6 Stunden ---
        self.scheduler.add_job(
            self._oracle_derive_tasks,
            IntervalTrigger(hours=6),
            id="oracle_derive_tasks",
            name="Oracle Task-Derivation",
            replace_existing=True,
        )

        # --- Font-Audit: alle 12 Stunden ---
        self.scheduler.add_job(
            self._oracle_font_audit,
            IntervalTrigger(hours=12),
            id="oracle_font_audit",
            name="Font-Audit",
            replace_existing=True,
        )

        # --- Zahlungsreminder: täglich 09:00 ---
        self.scheduler.add_job(
            self._check_payment_reminders,
            CronTrigger(hour=9, minute=0),
            id="payment_reminders",
            name="Zahlungsreminder",
            replace_existing=True,
        )

        # --- Mahnvorstufen: täglich 10:00 ---
        self.scheduler.add_job(
            self._check_dunning_stages,
            CronTrigger(hour=10, minute=0),
            id="dunning_stages",
            name="Mahnvorstufen",
            replace_existing=True,
        )

        # --- Follow-up Leads: täglich 08:30 ---
        self.scheduler.add_job(
            self._check_lead_followups,
            CronTrigger(hour=8, minute=30),
            id="lead_followups",
            name="Lead-Follow-ups",
            replace_existing=True,
        )

        # --- Buchungserinnerungen: alle 4 Stunden ---
        self.scheduler.add_job(
            self._check_booking_reminders,
            IntervalTrigger(hours=4),
            id="booking_reminders",
            name="Buchungserinnerungen",
            replace_existing=True,
        )

        # --- Angebotsablauf: täglich 07:00 ---
        self.scheduler.add_job(
            self._check_quote_expiry,
            IntervalTrigger(hours=12),
            id="quote_expiry",
            name="Angebotsablauf",
            replace_existing=True,
        )

        # --- Health-Check: alle 30 Minuten ---
        self.scheduler.add_job(
            self._health_check,
            IntervalTrigger(minutes=30),
            id="health_check",
            name="System-Health-Check",
            replace_existing=True,
        )

        # --- Dead-Letter Alerting: alle 2 Stunden ---
        self.scheduler.add_job(
            self._check_dead_letters,
            IntervalTrigger(hours=2),
            id="dead_letter_alert",
            name="Dead-Letter-Alerting",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"Scheduler gestartet: {len(self.scheduler.get_jobs())} Jobs registriert")

    async def stop(self):
        """Scheduler stoppen."""
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler gestoppt")

    # ──────────── Zahlungsreminder ────────────

    async def _check_payment_reminders(self):
        """Prüft offene Rechnungen und erstellt Reminder-Jobs."""
        try:
            now = utcnow()
            # Rechnungen mit Status "sent" und Fälligkeitsdatum in der Vergangenheit
            overdue_invoices = []
            async for inv in self.db.invoices.find(
                {"status": "sent", "payment_status": {"$ne": "paid"}},
                {"_id": 0, "invoice_id": 1, "due_date": 1, "invoice_number": 1,
                 "customer": 1, "totals": 1, "reminder_count": 1}
            ):
                due = inv.get("due_date", "")
                if not due:
                    continue
                try:
                    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00")) if isinstance(due, str) else due
                    if due_dt.tzinfo is None:
                        due_dt = due_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    continue

                days_overdue = (now - due_dt).days
                reminder_count = inv.get("reminder_count", 0)

                # Reminder-Logik: 3 Tage, 7 Tage, 14 Tage überfällig
                if days_overdue >= 3 and reminder_count == 0:
                    overdue_invoices.append((inv, 1, days_overdue))
                elif days_overdue >= 7 and reminder_count == 1:
                    overdue_invoices.append((inv, 2, days_overdue))
                elif days_overdue >= 14 and reminder_count == 2:
                    overdue_invoices.append((inv, 3, days_overdue))

            for inv, level, days in overdue_invoices:
                from workers.job_queue import JobPriority
                await self.job_queue.enqueue(
                    job_type="payment_reminder",
                    payload={
                        "invoice_id": inv["invoice_id"],
                        "invoice_number": inv.get("invoice_number", ""),
                        "customer_email": inv.get("customer", {}).get("email", ""),
                        "customer_name": inv.get("customer", {}).get("name", ""),
                        "reminder_level": level,
                        "days_overdue": days,
                        "totals": inv.get("totals", {}),
                    },
                    priority=JobPriority.HIGH,
                    ref_id=inv["invoice_id"],
                    ref_type="invoice",
                    created_by="scheduler:payment_reminders",
                )

            if overdue_invoices:
                logger.info(f"Zahlungsreminder: {len(overdue_invoices)} Jobs erstellt")

        except Exception as e:
            logger.error(f"Zahlungsreminder-Check fehlgeschlagen: {e}")
            await self._log_scheduler_error("payment_reminders", str(e))

    # ──────────── Mahnvorstufen ────────────

    async def _check_dunning_stages(self):
        """Eskaliert überfällige Rechnungen in Mahnstufen."""
        try:
            now = utcnow()
            async for inv in self.db.invoices.find(
                {"payment_status": {"$ne": "paid"}, "reminder_count": {"$gte": 3}},
                {"_id": 0, "invoice_id": 1, "due_date": 1, "invoice_number": 1,
                 "customer": 1, "totals": 1, "dunning_stage": 1}
            ):
                due = inv.get("due_date", "")
                if not due:
                    continue
                try:
                    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00")) if isinstance(due, str) else due
                    if due_dt.tzinfo is None:
                        due_dt = due_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    continue

                days_overdue = (now - due_dt).days
                current_stage = inv.get("dunning_stage", 0)

                # Mahnstufe 1: 21 Tage, Stufe 2: 35 Tage, Stufe 3: 49 Tage
                new_stage = None
                if days_overdue >= 49 and current_stage < 3:
                    new_stage = 3
                elif days_overdue >= 35 and current_stage < 2:
                    new_stage = 2
                elif days_overdue >= 21 and current_stage < 1:
                    new_stage = 1

                if new_stage is not None:
                    from workers.job_queue import JobPriority
                    await self.job_queue.enqueue(
                        job_type="dunning_escalation",
                        payload={
                            "invoice_id": inv["invoice_id"],
                            "invoice_number": inv.get("invoice_number", ""),
                            "customer_email": inv.get("customer", {}).get("email", ""),
                            "customer_name": inv.get("customer", {}).get("name", ""),
                            "dunning_stage": new_stage,
                            "days_overdue": days_overdue,
                            "totals": inv.get("totals", {}),
                        },
                        priority=JobPriority.CRITICAL,
                        ref_id=inv["invoice_id"],
                        ref_type="invoice",
                        created_by="scheduler:dunning",
                    )

        except Exception as e:
            logger.error(f"Mahnvorstufen-Check fehlgeschlagen: {e}")
            await self._log_scheduler_error("dunning_stages", str(e))

    # ──────────── Lead-Follow-ups ────────────

    async def _check_lead_followups(self):
        """Prüft Leads die Follow-up brauchen."""
        try:
            now = utcnow()
            followup_cutoff = now - timedelta(days=3)

            async for lead in self.db.leads.find(
                {
                    "status": {"$in": ["new", "contacted", "qualified"]},
                    "last_followup_at": {"$lt": followup_cutoff.isoformat()},
                },
                {"_id": 0, "contact_id": 1, "email": 1, "vorname": 1,
                 "nachname": 1, "status": 1, "unternehmen": 1}
            ):
                from workers.job_queue import JobPriority
                await self.job_queue.enqueue(
                    job_type="lead_followup",
                    payload={
                        "contact_id": lead.get("contact_id", ""),
                        "email": lead.get("email", ""),
                        "name": f"{lead.get('vorname', '')} {lead.get('nachname', '')}".strip(),
                        "company": lead.get("unternehmen", ""),
                        "status": lead.get("status", ""),
                    },
                    priority=JobPriority.NORMAL,
                    ref_id=lead.get("contact_id", ""),
                    ref_type="lead",
                    created_by="scheduler:lead_followups",
                )

            # Auch Leads ohne last_followup_at, erstellt vor 3+ Tagen
            async for lead in self.db.leads.find(
                {
                    "status": {"$in": ["new", "contacted"]},
                    "last_followup_at": {"$exists": False},
                    "created_at": {"$lt": followup_cutoff.isoformat()},
                },
                {"_id": 0, "contact_id": 1, "email": 1, "vorname": 1,
                 "nachname": 1, "status": 1, "unternehmen": 1}
            ):
                from workers.job_queue import JobPriority
                await self.job_queue.enqueue(
                    job_type="lead_followup",
                    payload={
                        "contact_id": lead.get("contact_id", ""),
                        "email": lead.get("email", ""),
                        "name": f"{lead.get('vorname', '')} {lead.get('nachname', '')}".strip(),
                        "company": lead.get("unternehmen", ""),
                        "status": lead.get("status", ""),
                    },
                    priority=JobPriority.NORMAL,
                    ref_id=lead.get("contact_id", ""),
                    ref_type="lead",
                    created_by="scheduler:lead_followups",
                )

        except Exception as e:
            logger.error(f"Lead-Follow-up-Check fehlgeschlagen: {e}")
            await self._log_scheduler_error("lead_followups", str(e))

    # ──────────── Buchungserinnerungen ────────────

    async def _check_booking_reminders(self):
        """Erinnerungen für anstehende Termine."""
        try:
            now = utcnow()
            # Termine in den nächsten 24 Stunden
            reminder_window = now + timedelta(hours=24)

            async for booking in self.db.bookings.find(
                {
                    "status": {"$in": ["confirmed", "pending"]},
                    "datetime": {
                        "$gte": now.isoformat(),
                        "$lte": reminder_window.isoformat(),
                    },
                    "reminder_sent": {"$ne": True},
                },
                {"_id": 0}
            ):
                from workers.job_queue import JobPriority
                await self.job_queue.enqueue(
                    job_type="booking_reminder",
                    payload={
                        "booking_id": booking.get("booking_id", ""),
                        "email": booking.get("email", ""),
                        "name": booking.get("name", ""),
                        "datetime": booking.get("datetime", ""),
                        "type": booking.get("type", ""),
                    },
                    priority=JobPriority.HIGH,
                    ref_id=booking.get("booking_id", ""),
                    ref_type="booking",
                    created_by="scheduler:booking_reminders",
                )

        except Exception as e:
            logger.error(f"Buchungserinnerungen-Check fehlgeschlagen: {e}")
            await self._log_scheduler_error("booking_reminders", str(e))

    # ──────────── Angebotsablauf ────────────

    async def _check_quote_expiry(self):
        """Prüft ob Angebote abgelaufen sind."""
        try:
            now = utcnow()
            async for quote in self.db.quotes.find(
                {
                    "status": {"$in": ["sent", "viewed"]},
                    "valid_until": {"$lt": now.isoformat()},
                    "expired_notified": {"$ne": True},
                },
                {"_id": 0, "quote_id": 1, "quote_number": 1,
                 "customer": 1, "valid_until": 1}
            ):
                from workers.job_queue import JobPriority
                await self.job_queue.enqueue(
                    job_type="quote_expiry",
                    payload={
                        "quote_id": quote.get("quote_id", ""),
                        "quote_number": quote.get("quote_number", ""),
                        "customer_email": quote.get("customer", {}).get("email", ""),
                        "customer_name": quote.get("customer", {}).get("name", ""),
                        "valid_until": quote.get("valid_until", ""),
                    },
                    priority=JobPriority.NORMAL,
                    ref_id=quote.get("quote_id", ""),
                    ref_type="quote",
                    created_by="scheduler:quote_expiry",
                )

        except Exception as e:
            logger.error(f"Angebotsablauf-Check fehlgeschlagen: {e}")
            await self._log_scheduler_error("quote_expiry", str(e))

    # ──────────── Health-Check ────────────

    async def _health_check(self):
        """Regelmäßiger System-Health-Check."""
        try:
            checks = {}

            # DB-Ping
            try:
                await self.db.command("ping")
                checks["database"] = "ok"
            except Exception:
                checks["database"] = "error"

            # Queue-Status
            checks["job_queue"] = self.job_queue.get_stats()

            # Dead-Letter-Count
            dl_count = await self.db.jobs.count_documents({"status": "dead_letter"})
            checks["dead_letter_count"] = dl_count

            # Fehler letzte 24h
            error_count = await self.db.timeline_events.count_documents({
                "action": {"$regex": "error|fail|dead_letter"},
                "timestamp": {"$gte": utcnow() - timedelta(hours=24)},
            })
            checks["errors_24h"] = error_count

            await self.db.timeline_events.insert_one({
                "action": "system_health_check",
                "ref_id": "system",
                "ref_type": "health",
                "user": "scheduler:health",
                "details": checks,
                "timestamp": utcnow(),
            })

            if checks.get("database") == "error" or dl_count > 10:
                logger.warning(f"Health-Check: Probleme erkannt — {checks}")

        except Exception as e:
            logger.error(f"Health-Check fehlgeschlagen: {e}")

    # ──────────── Dead-Letter Alerting ────────────

    async def _check_dead_letters(self):
        """Prüft Dead-Letter-Queue und erstellt Alert."""
        try:
            dl_count = await self.db.jobs.count_documents({
                "status": "dead_letter",
                "dead_letter_at": {"$gte": (utcnow() - timedelta(hours=2)).isoformat()},
            })
            if dl_count > 0:
                await self.db.timeline_events.insert_one({
                    "action": "dead_letter_alert",
                    "ref_id": "system",
                    "ref_type": "alert",
                    "user": "scheduler:dead_letter",
                    "details": {"count": dl_count, "window_hours": 2},
                    "timestamp": utcnow(),
                })
                logger.warning(f"Dead-Letter-Alert: {dl_count} fehlgeschlagene Jobs in 2h")

        except Exception as e:
            logger.error(f"Dead-Letter-Alert fehlgeschlagen: {e}")

    # ──────────── Hilfsfunktionen ────────────

    async def _log_scheduler_error(self, job_name: str, error: str):
        """Scheduler-Fehler in Timeline schreiben."""
        try:
            await self.db.timeline_events.insert_one({
                "action": "scheduler_error",
                "ref_id": job_name,
                "ref_type": "scheduler",
                "user": "scheduler",
                "details": {"error": error},
                "timestamp": utcnow(),
            })
        except Exception:
            pass

    def get_status(self) -> dict:
        """Status aller geplanten Jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        oracle_stats = self._oracle_engine.get_stats() if self._oracle_engine else {}
        return {
            "running": self.scheduler.running,
            "jobs": jobs,
            "count": len(jobs),
            "oracle_engine": oracle_stats,
        }

    # ──────────── Oracle Engine Wrapper ────────────

    async def _oracle_process_cycle(self):
        """Oracle Task-Processing Zyklus."""
        if self._oracle_engine:
            await self._oracle_engine.process_cycle()

    async def _oracle_knowledge_sync(self):
        """Oracle Knowledge-Sync."""
        if self._oracle_engine:
            await self._oracle_engine.sync_knowledge()

    async def _oracle_derive_tasks(self):
        """Oracle Task-Derivation."""
        if self._oracle_engine:
            await self._oracle_engine.derive_tasks()

    async def _oracle_font_audit(self):
        """Oracle Font-Audit."""
        if self._oracle_engine:
            await self._oracle_engine.run_font_audit()
