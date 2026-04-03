"""
Job-Handler — die eigentliche Business-Logik der entkoppelten Jobs.
Jeder Handler ist eine async Funktion: handler(payload, job_meta) → result

Handler-Typen:
- send_email: E-Mail-Versand (aus Request entkoppelt)
- payment_reminder: Zahlungserinnerung
- dunning_escalation: Mahnvorstufe
- lead_followup: Lead-Follow-up
- booking_reminder: Terminerinnerung
- quote_expiry: Angebotsablauf
- ai_task: KI-Aufgabe (asynchron)
- pdf_generation: PDF-Erstellung
- status_transition: Status-Folgelogik
- portal_access: Portalzugang erstellen
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict
from domain import utcnow

logger = logging.getLogger("nexifyai.workers.handlers")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@send.nexify-automate.com")


def _get_db():
    """Lazy DB-Zugriff über den globalen Handler-Context."""
    return _handler_db


_handler_db = None


def init_handlers(db):
    """DB-Referenz für Handler setzen."""
    global _handler_db
    _handler_db = db


# ══════════════════════════════════════════════════════
# E-MAIL HANDLER
# ══════════════════════════════════════════════════════

async def handle_send_email(payload: dict, job_meta: dict) -> str:
    """E-Mail über Resend versenden — entkoppelt vom Request."""
    if not RESEND_API_KEY:
        logger.warning("Resend nicht konfiguriert — E-Mail übersprungen")
        return "skipped:no_api_key"

    import resend
    import asyncio
    resend.api_key = RESEND_API_KEY

    to = payload.get("to", [])
    subject = payload.get("subject", "")
    html = payload.get("html", "")
    attachments = payload.get("attachments", None)

    if not to or not subject:
        return "skipped:missing_fields"

    email_params = {
        "from": f"NeXifyAI <{SENDER_EMAIL}>",
        "to": to if isinstance(to, list) else [to],
        "subject": subject,
        "html": html,
    }
    if attachments:
        email_params["attachments"] = attachments

    result = await asyncio.to_thread(resend.Emails.send, email_params)
    logger.info(f"E-Mail gesendet an {to}: {subject}")

    # Audit
    db = _get_db()
    if db:
        await db.timeline_events.insert_one({
            "action": "email_sent",
            "ref_id": job_meta.get("ref_id", ""),
            "ref_type": job_meta.get("ref_type", "email"),
            "user": "worker:email",
            "details": {"to": to, "subject": subject},
            "timestamp": utcnow(),
        })

    return f"sent:{result}"


# ══════════════════════════════════════════════════════
# ZAHLUNGSREMINDER HANDLER
# ══════════════════════════════════════════════════════

async def handle_payment_reminder(payload: dict, job_meta: dict) -> str:
    """Zahlungserinnerung senden und DB aktualisieren."""
    db = _get_db()
    invoice_id = payload["invoice_id"]
    level = payload["reminder_level"]
    customer_email = payload["customer_email"]
    customer_name = payload.get("customer_name", "")
    invoice_number = payload.get("invoice_number", "")
    days_overdue = payload.get("days_overdue", 0)
    totals = payload.get("totals", {})

    level_labels = {1: "Zahlungserinnerung", 2: "Zweite Zahlungserinnerung", 3: "Letzte Zahlungserinnerung"}
    label = level_labels.get(level, "Zahlungserinnerung")

    gross = totals.get("gross", 0)
    gross_str = f"{gross:,.2f} EUR" if isinstance(gross, (int, float)) else str(gross)

    # E-Mail via Job-Queue (direkt hier senden, da wir bereits im Worker sind)
    if RESEND_API_KEY and customer_email:
        import resend
        import asyncio
        resend.api_key = RESEND_API_KEY

        from server import email_template, COMM_COMPANY
        bank = COMM_COMPANY.get("bank", {})

        html = email_template(
            label,
            f'''<h1 style="color:#fff;font-size:20px;margin:0 0 16px;">{label}</h1>
            <p>Sehr geehrte/r {customer_name},</p>
            <p>für die Rechnung Nr. {invoice_number} steht noch eine Zahlung in Höhe von
            <strong style="color:#ffb599;">{gross_str}</strong> aus (seit {days_overdue} Tagen überfällig).</p>
            <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
            <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">BANKVERBINDUNG</p>
            <p style="margin:0;color:#fff;font-size:13px;">
            IBAN: {bank.get("iban", "NL66 REVO 3601 4304 36")}<br/>
            BIC: {bank.get("bic", "REVOLT21")}<br/>
            Verwendungszweck: {invoice_number}</p>
            </div>
            <p>Bitte überweisen Sie den Betrag umgehend. Bei Fragen stehen wir Ihnen gerne zur Verfügung.</p>''',
        )
        try:
            await asyncio.to_thread(resend.Emails.send, {
                "from": f"NeXifyAI <{SENDER_EMAIL}>",
                "to": [customer_email],
                "subject": f"{label} — {invoice_number} — NeXifyAI",
                "html": html,
            })
        except Exception as e:
            logger.error(f"Reminder-E-Mail fehlgeschlagen: {e}")
            raise

    # DB: reminder_count erhöhen
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {
            "$set": {"last_reminder_at": utcnow().isoformat()},
            "$inc": {"reminder_count": 1},
            "$push": {"history": {
                "action": f"reminder_level_{level}",
                "at": utcnow().isoformat(),
                "by": "worker:reminder",
            }},
        },
    )

    await db.timeline_events.insert_one({
        "action": f"payment_reminder_level_{level}",
        "ref_id": invoice_id,
        "ref_type": "invoice",
        "user": "worker:reminder",
        "details": {"level": level, "days_overdue": days_overdue, "email": customer_email},
        "timestamp": utcnow(),
    })

    return f"reminder_level_{level}_sent"


# ══════════════════════════════════════════════════════
# MAHNVORSTUFEN HANDLER
# ══════════════════════════════════════════════════════

async def handle_dunning_escalation(payload: dict, job_meta: dict) -> str:
    """Mahnstufe eskalieren."""
    db = _get_db()
    invoice_id = payload["invoice_id"]
    stage = payload["dunning_stage"]
    customer_email = payload.get("customer_email", "")
    invoice_number = payload.get("invoice_number", "")
    days_overdue = payload.get("days_overdue", 0)

    stage_labels = {1: "1. Mahnung", 2: "2. Mahnung", 3: "Letzte Mahnung vor Inkasso"}

    # DB: dunning_stage aktualisieren
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {
            "$set": {"dunning_stage": stage, "last_dunning_at": utcnow().isoformat()},
            "$push": {"history": {
                "action": f"dunning_stage_{stage}",
                "at": utcnow().isoformat(),
                "by": "worker:dunning",
            }},
        },
    )

    await db.timeline_events.insert_one({
        "action": f"dunning_stage_{stage}",
        "ref_id": invoice_id,
        "ref_type": "invoice",
        "user": "worker:dunning",
        "details": {
            "stage": stage,
            "label": stage_labels.get(stage, ""),
            "days_overdue": days_overdue,
            "customer_email": customer_email,
        },
        "timestamp": utcnow(),
    })

    # Bei Stufe 3: Admin-Alert
    if stage >= 3:
        await db.timeline_events.insert_one({
            "action": "dunning_escalation_alert",
            "ref_id": invoice_id,
            "ref_type": "alert",
            "user": "worker:dunning",
            "details": {
                "message": f"Rechnung {invoice_number} ist seit {days_overdue} Tagen überfällig. Inkasso-Prüfung erforderlich.",
                "invoice_number": invoice_number,
            },
            "timestamp": utcnow(),
        })

    return f"dunning_stage_{stage}"


# ══════════════════════════════════════════════════════
# LEAD FOLLOW-UP HANDLER
# ══════════════════════════════════════════════════════

async def handle_lead_followup(payload: dict, job_meta: dict) -> str:
    """Lead-Follow-up markieren und benachrichtigen."""
    db = _get_db()
    contact_id = payload.get("contact_id", "")
    email = payload.get("email", "")
    name = payload.get("name", "")

    # Markiere Follow-up als fällig im Lead
    await db.leads.update_one(
        {"contact_id": contact_id} if contact_id else {"email": email},
        {
            "$set": {"followup_due": True, "last_followup_at": utcnow().isoformat()},
            "$push": {"history": {
                "action": "followup_due",
                "at": utcnow().isoformat(),
                "by": "worker:followup",
            }},
        },
    )

    await db.timeline_events.insert_one({
        "action": "lead_followup_due",
        "ref_id": contact_id or email,
        "ref_type": "lead",
        "user": "worker:followup",
        "details": {"email": email, "name": name},
        "timestamp": utcnow(),
    })

    return "followup_marked"


# ══════════════════════════════════════════════════════
# BUCHUNGSERINNERUNG HANDLER
# ══════════════════════════════════════════════════════

async def handle_booking_reminder(payload: dict, job_meta: dict) -> str:
    """Terminerinnerung senden."""
    db = _get_db()
    booking_id = payload.get("booking_id", "")

    await db.bookings.update_one(
        {"booking_id": booking_id},
        {"$set": {"reminder_sent": True, "reminder_sent_at": utcnow().isoformat()}},
    )

    await db.timeline_events.insert_one({
        "action": "booking_reminder_sent",
        "ref_id": booking_id,
        "ref_type": "booking",
        "user": "worker:booking_reminder",
        "details": payload,
        "timestamp": utcnow(),
    })

    return "reminder_sent"


# ══════════════════════════════════════════════════════
# ANGEBOTSABLAUF HANDLER
# ══════════════════════════════════════════════════════

async def handle_quote_expiry(payload: dict, job_meta: dict) -> str:
    """Abgelaufenes Angebot markieren."""
    db = _get_db()
    quote_id = payload.get("quote_id", "")

    await db.quotes.update_one(
        {"quote_id": quote_id},
        {
            "$set": {"status": "expired", "expired_notified": True, "expired_at": utcnow().isoformat()},
            "$push": {"history": {
                "action": "expired",
                "at": utcnow().isoformat(),
                "by": "worker:quote_expiry",
            }},
        },
    )

    await db.timeline_events.insert_one({
        "action": "quote_expired",
        "ref_id": quote_id,
        "ref_type": "quote",
        "user": "worker:quote_expiry",
        "details": payload,
        "timestamp": utcnow(),
    })

    return "quote_expired"


# ══════════════════════════════════════════════════════
# AI-TASK HANDLER
# ══════════════════════════════════════════════════════

async def handle_ai_task(payload: dict, job_meta: dict) -> str:
    """KI-Task entkoppelt vom Request ausführen."""
    db = _get_db()
    task_type = payload.get("task_type", "")
    context = payload.get("context", "")
    agent_name = payload.get("agent_name", "")

    # Lazy Import der Agent-Instanzen
    from server import agents as server_agents, orchestrator

    if agent_name and agent_name in server_agents:
        result = await server_agents[agent_name].execute(
            payload.get("task", ""),
            context,
        )
    elif orchestrator:
        result = await orchestrator.route(
            payload.get("task", ""),
            {"context": context},
        )
    else:
        return "skipped:no_agents"

    await db.timeline_events.insert_one({
        "action": "ai_task_completed",
        "ref_id": job_meta.get("ref_id", ""),
        "ref_type": "ai_task",
        "user": f"worker:ai:{agent_name or 'orchestrator'}",
        "details": {"task_type": task_type, "result_preview": str(result)[:500]},
        "timestamp": utcnow(),
    })

    return f"ai_task_completed:{task_type}"


# ══════════════════════════════════════════════════════
# STATUS-TRANSITION HANDLER
# ══════════════════════════════════════════════════════

async def handle_status_transition(payload: dict, job_meta: dict) -> str:
    """Status-Folgelogik ausführen."""
    db = _get_db()
    entity_type = payload.get("entity_type", "")  # quote, invoice, lead
    entity_id = payload.get("entity_id", "")
    new_status = payload.get("new_status", "")
    triggered_by = payload.get("triggered_by", "system")

    collection_map = {
        "quote": "quotes", "invoice": "invoices",
        "lead": "leads", "booking": "bookings",
    }
    collection = collection_map.get(entity_type)
    if not collection:
        return f"skipped:unknown_entity:{entity_type}"

    id_field = f"{entity_type}_id"
    await db[collection].update_one(
        {id_field: entity_id},
        {
            "$set": {"status": new_status, "updated_at": utcnow().isoformat()},
            "$push": {"history": {
                "action": f"status_changed_to_{new_status}",
                "at": utcnow().isoformat(),
                "by": triggered_by,
            }},
        },
    )

    await db.timeline_events.insert_one({
        "action": f"{entity_type}_status_changed",
        "ref_id": entity_id,
        "ref_type": entity_type,
        "user": triggered_by,
        "details": {"new_status": new_status},
        "timestamp": utcnow(),
    })

    return f"status:{entity_type}:{new_status}"
