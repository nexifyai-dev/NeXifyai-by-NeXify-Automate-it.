"""
Billing Service — Offer-to-Cash Status-Sync.

Durchgängig synchron:
Angebot → Vertragsstatus → Rechnung → Zahlungslink → Webhook →
Adminstatus → Portalstatus → Timeline → Mailkommunikation →
Reminderlogik → Mahnvorstufen

Pflicht:
- Keine divergierenden Status
- Keine zweite Wahrheitsquelle
- Webhooks idempotent
- Manuelle Überweisung und Online-Zahlung im selben Statusmodell
- Rechnungs-/Angebotsdokumente konsistent mit Tarif-Source-of-Truth
- Rabatte und Sonderpositionen überall synchron
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from domain import (
    OfferStatus, InvoiceStatus,
    create_timeline_event, new_id, utcnow,
)

logger = logging.getLogger("nexifyai.services.billing")


class BillingService:
    """Offer-to-Cash: Angebot → Rechnung → Zahlung → Abschluss."""

    def __init__(self, db, worker_manager=None, comms_service=None):
        self.db = db
        self.worker = worker_manager
        self.comms = comms_service

    # ══════════════════════════════════════════
    # STATUS-SYNC QUOTE → INVOICE
    # ══════════════════════════════════════════

    async def sync_quote_status(self, quote_id: str, new_status: str, by: str = "system") -> dict:
        """
        Quote-Status ändern und Folgelogik triggern.
        Stellt sicher: Quote + Invoice + Portal + Timeline synchron.
        """
        quote = await self.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
        if not quote:
            return {"error": "Quote nicht gefunden"}

        old_status = quote.get("status", "draft")
        now = utcnow()

        # Status-Update
        update = {
            "$set": {"status": new_status, "updated_at": now.isoformat()},
            "$push": {"history": {
                "action": f"status_changed:{old_status}→{new_status}",
                "at": now.isoformat(),
                "by": by,
            }},
        }
        await self.db.quotes.update_one({"quote_id": quote_id}, update)

        # Folgelogik
        result = {"quote_id": quote_id, "old_status": old_status, "new_status": new_status}

        if new_status == OfferStatus.ACCEPTED.value:
            # Vertragsstatus erstellen / Rechnung vorbereiten
            invoice_result = await self._create_deposit_invoice(quote)
            result["invoice_created"] = invoice_result

            # Kommunikation
            if self.comms:
                contact = await self.db.contacts.find_one(
                    {"email": quote.get("customer", {}).get("email", "")}, {"_id": 0}
                )
                if contact:
                    conv = await self.comms.get_or_create_conversation(
                        contact["contact_id"], "system"
                    )
                    await self.comms.add_message(
                        conv["conversation_id"], "system",
                        "outbound",
                        f"Angebot {quote.get('quote_number', '')} wurde angenommen. Aktivierungsrechnung wird erstellt.",
                        sender="system", ai_generated=False,
                        ref_id=quote_id, ref_type="quote",
                    )

        elif new_status == OfferStatus.DECLINED.value:
            # Nurturing-Flow starten
            if self.worker:
                from workers.job_queue import JobPriority
                await self.worker.enqueue(
                    "status_transition",
                    {
                        "entity_type": "lead",
                        "entity_id": quote.get("contact_id", ""),
                        "new_status": "nurturing",
                        "triggered_by": "billing:quote_declined",
                    },
                    priority=JobPriority.NORMAL,
                    ref_id=quote_id,
                    ref_type="quote",
                )

        # Timeline
        await self._timeline(
            "quote", quote_id,
            f"quote_status_{new_status}",
            actor=by,
            details={"old_status": old_status, "new_status": new_status},
        )

        return result

    # ══════════════════════════════════════════
    # RECHNUNGS-MANAGEMENT
    # ══════════════════════════════════════════

    async def sync_invoice_status(self, invoice_id: str, new_status: str, by: str = "system") -> dict:
        """
        Invoice-Status ändern und Folgelogik triggern.
        Synchronisiert: Invoice + Quote + Portal + Timeline.
        """
        invoice = await self.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
        if not invoice:
            return {"error": "Rechnung nicht gefunden"}

        old_status = invoice.get("payment_status", invoice.get("status", "draft"))
        now = utcnow()

        # Status-Update
        update_set = {"payment_status": new_status, "status": new_status, "updated_at": now.isoformat()}
        if new_status == "paid":
            update_set["paid_at"] = now.isoformat()

        await self.db.invoices.update_one(
            {"invoice_id": invoice_id},
            {
                "$set": update_set,
                "$push": {"history": {
                    "action": f"payment_status:{old_status}→{new_status}",
                    "at": now.isoformat(),
                    "by": by,
                }},
            },
        )

        result = {"invoice_id": invoice_id, "old_status": old_status, "new_status": new_status}

        # Quote-Sync bei Zahlung
        if new_status == "paid" and invoice.get("quote_id"):
            await self.db.quotes.update_one(
                {"quote_id": invoice["quote_id"]},
                {
                    "$set": {"payment_status": "deposit_paid", "updated_at": now.isoformat()},
                    "$push": {"history": {
                        "action": "deposit_paid",
                        "at": now.isoformat(),
                        "by": by,
                    }},
                },
            )
            result["quote_synced"] = True

        # Timeline
        await self._timeline(
            "invoice", invoice_id,
            f"invoice_status_{new_status}",
            actor=by,
            details={"old_status": old_status, "invoice_number": invoice.get("invoice_number", "")},
        )

        return result

    async def process_payment_webhook(self, provider: str, event_data: dict) -> dict:
        """
        Payment-Webhook verarbeiten — idempotent.
        Unterstützt: Revolut, Stripe, manuelle Überweisung.
        """
        order_id = event_data.get("order_id", "")
        event_type = event_data.get("event", "")
        amount = event_data.get("amount", 0)

        # Idempotenz-Check
        existing = await self.db.timeline_events.find_one({
            "action": "payment_webhook",
            "details.provider": provider,
            "details.order_id": order_id,
            "details.event_type": event_type,
        })
        if existing:
            return {"status": "already_processed", "order_id": order_id}

        # Invoice finden
        invoice = await self.db.invoices.find_one(
            {"$or": [
                {"payment_order_id": order_id},
                {"invoice_number": order_id},
            ]},
            {"_id": 0},
        )

        result = {"provider": provider, "event_type": event_type, "order_id": order_id}

        if invoice and event_type in ("ORDER_COMPLETED", "payment_intent.succeeded", "manual_paid"):
            sync_result = await self.sync_invoice_status(
                invoice["invoice_id"], "paid", by=f"webhook:{provider}"
            )
            result["invoice_synced"] = sync_result
        elif invoice and event_type in ("ORDER_FAILED", "payment_intent.payment_failed"):
            await self.sync_invoice_status(
                invoice["invoice_id"], "payment_failed", by=f"webhook:{provider}"
            )

        # Webhook-Event loggen
        await self._timeline(
            "payment", order_id, "payment_webhook",
            actor=f"webhook:{provider}",
            details={
                "provider": provider,
                "event_type": event_type,
                "order_id": order_id,
                "amount": amount,
            },
        )

        return result

    # ══════════════════════════════════════════
    # RECONCILIATION
    # ══════════════════════════════════════════

    async def get_billing_status(self, contact_email: str) -> dict:
        """
        Gesamter Billing-Status für einen Kontakt.
        Einheitliche Sicht: Quotes + Invoices + Payments.
        """
        quotes = []
        async for q in self.db.quotes.find(
            {"customer.email": contact_email},
            {"_id": 0, "items": 0},
        ).sort("created_at", -1):
            for k in ("created_at", "updated_at"):
                if hasattr(q.get(k), "isoformat"):
                    q[k] = q[k].isoformat()
            quotes.append(q)

        invoices = []
        async for inv in self.db.invoices.find(
            {"customer.email": contact_email},
            {"_id": 0},
        ).sort("created_at", -1):
            for k in ("created_at", "updated_at"):
                if hasattr(inv.get(k), "isoformat"):
                    inv[k] = inv[k].isoformat()
            invoices.append(inv)

        # Aggregation
        total_invoiced = sum(
            inv.get("totals", {}).get("gross", 0) for inv in invoices
            if isinstance(inv.get("totals", {}).get("gross", 0), (int, float))
        )
        total_paid = sum(
            inv.get("totals", {}).get("gross", 0) for inv in invoices
            if inv.get("payment_status") == "paid"
            and isinstance(inv.get("totals", {}).get("gross", 0), (int, float))
        )
        total_outstanding = total_invoiced - total_paid

        return {
            "contact_email": contact_email,
            "quotes": quotes,
            "invoices": invoices,
            "summary": {
                "total_quotes": len(quotes),
                "total_invoices": len(invoices),
                "total_invoiced": round(total_invoiced, 2),
                "total_paid": round(total_paid, 2),
                "total_outstanding": round(total_outstanding, 2),
            },
        }

    # ══════════════════════════════════════════
    # INTERNE HELFER
    # ══════════════════════════════════════════

    async def _create_deposit_invoice(self, quote: dict) -> dict:
        """Aktivierungsrechnung aus angenommenem Angebot erstellen."""
        from commercial import generate_invoice_from_quote

        try:
            invoice_data = generate_invoice_from_quote(quote)
            invoice_data["status"] = "draft"
            invoice_data["payment_status"] = "unpaid"
            invoice_data["quote_id"] = quote["quote_id"]
            invoice_data["created_at"] = utcnow().isoformat()

            await self.db.invoices.insert_one({**invoice_data})

            await self._timeline(
                "invoice", invoice_data.get("invoice_id", ""),
                "invoice_created_from_quote",
                details={"quote_id": quote["quote_id"]},
            )

            return {"invoice_id": invoice_data.get("invoice_id"), "status": "created"}
        except Exception as e:
            logger.error(f"Rechnungserstellung aus Angebot fehlgeschlagen: {e}")
            return {"error": str(e)}

    async def _timeline(self, entity_type: str, entity_id: str, event: str, **kwargs):
        evt = create_timeline_event(entity_type, entity_id, event, **kwargs)
        await self.db.timeline_events.insert_one({**evt})
