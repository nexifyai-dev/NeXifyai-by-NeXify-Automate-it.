"""
Kanalübergreifender Kommunikationskern.

Zentrale Conversation-Domain, Message-Domain, kanalübergreifende Timeline.
Gleiche Wahrheitslogik über: Website-Chat, E-Mail, WhatsApp, Kundenportal.

Pflichten:
- Keine Doppelhistorien
- Keine kanalgetrennten Statuswahrheiten
- Jede ausgehende/eingehende Nachricht historisiert
- KI- und manuelle Antworten unterscheidbar
- Owner, Quelle, Status, nächster Schritt, Eskalationspfad pro Konversation
- Zentrale Routing-Regeln
- Templates kanalabhängig formatiert, inhaltlich synchron
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from domain import (
    Channel, ConversationStatus, MessageDirection,
    create_contact, create_conversation, create_message,
    create_timeline_event, new_id, utcnow,
)

logger = logging.getLogger("nexifyai.services.comms")


class CommunicationService:
    """Zentrale Kommunikationsschicht — Single Source of Truth für alle Kanäle."""

    def __init__(self, db, worker_manager=None):
        self.db = db
        self.worker = worker_manager

    # ══════════════════════════════════════════
    # KONTAKT-MANAGEMENT (Unified Identity)
    # ══════════════════════════════════════════

    async def get_or_create_contact(self, email: str, **kwargs) -> dict:
        """Findet oder erstellt einen Kontakt. Dedupliziert via E-Mail."""
        email_lower = email.lower().strip()
        existing = await self.db.contacts.find_one({"email": email_lower}, {"_id": 0})
        if existing:
            # Update channels_used
            channel = kwargs.get("channel", "")
            if channel and channel not in existing.get("channels_used", []):
                await self.db.contacts.update_one(
                    {"email": email_lower},
                    {"$addToSet": {"channels_used": channel}, "$set": {"updated_at": utcnow()}}
                )
                existing["channels_used"] = existing.get("channels_used", []) + [channel]
            return existing

        # Auch in leads suchen
        lead = await self.db.leads.find_one({"email": email_lower}, {"_id": 0})
        if lead:
            contact = create_contact(
                email_lower,
                first_name=lead.get("vorname", ""),
                last_name=lead.get("nachname", ""),
                company=lead.get("unternehmen", ""),
                phone=lead.get("telefon", ""),
                source=lead.get("source", "website"),
            )
            contact["lead_id"] = lead.get("contact_id", "")
            await self.db.contacts.insert_one({**contact})
            return contact

        # Neuen Kontakt erstellen
        contact = create_contact(email_lower, **kwargs)
        await self.db.contacts.insert_one({**contact})
        return contact

    # ══════════════════════════════════════════
    # KONVERSATION-MANAGEMENT (Cross-Channel)
    # ══════════════════════════════════════════

    async def get_or_create_conversation(
        self, contact_id: str, channel: str, **kwargs
    ) -> dict:
        """Findet offene Konversation oder erstellt neue."""
        # Offene Konversation für diesen Kontakt suchen
        existing = await self.db.conversations.find_one(
            {
                "contact_id": contact_id,
                "status": {"$in": [ConversationStatus.OPEN.value, ConversationStatus.PENDING.value]},
            },
            {"_id": 0},
        )
        if existing:
            # Channel hinzufügen falls neu
            if channel not in existing.get("channels", []):
                await self.db.conversations.update_one(
                    {"conversation_id": existing["conversation_id"]},
                    {"$addToSet": {"channels": channel}, "$set": {"updated_at": utcnow()}}
                )
            return existing

        # Neue Konversation
        conv = create_conversation(contact_id, channel, **kwargs)
        await self.db.conversations.insert_one({**conv})

        # Timeline
        await self._timeline(
            "conversation", conv["conversation_id"],
            "conversation_created",
            channel=channel, details={"contact_id": contact_id},
        )
        return conv

    async def add_message(
        self,
        conversation_id: str,
        channel: str,
        direction: str,
        content: str,
        sender: str = "",
        ai_generated: bool = False,
        metadata: dict = None,
        ref_id: str = "",
        ref_type: str = "",
    ) -> dict:
        """Nachricht zur Konversation hinzufügen — zentrale Historisierung."""
        msg = create_message(
            conversation_id, channel, direction, content,
            sender=sender, ai_generated=ai_generated,
            metadata=metadata or {},
        )

        # Referenz setzen (z.B. Angebot, Rechnung)
        if ref_id:
            msg["ref_id"] = ref_id
            msg["ref_type"] = ref_type

        await self.db.messages.insert_one({**msg})

        # Konversation aktualisieren
        update = {
            "$set": {
                "last_message_at": utcnow(),
                "updated_at": utcnow(),
            },
            "$inc": {"message_count": 1},
            "$addToSet": {"channels": channel},
        }

        # Status-Logik: Inbound → open/pending, Outbound → pending
        if direction == MessageDirection.INBOUND.value:
            update["$set"]["status"] = ConversationStatus.OPEN.value
        elif direction == MessageDirection.OUTBOUND.value and not ai_generated:
            update["$set"]["status"] = ConversationStatus.PENDING.value

        await self.db.conversations.update_one(
            {"conversation_id": conversation_id},
            update,
        )

        return msg

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 100
    ) -> List[dict]:
        """Alle Nachrichten einer Konversation, kanalübergreifend."""
        messages = []
        async for msg in self.db.messages.find(
            {"conversation_id": conversation_id},
            {"_id": 0},
        ).sort("timestamp", 1).limit(limit):
            if hasattr(msg.get("timestamp"), "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
            messages.append(msg)
        return messages

    async def get_contact_conversations(
        self, contact_id: str, limit: int = 20
    ) -> List[dict]:
        """Alle Konversationen eines Kontakts."""
        convs = []
        async for conv in self.db.conversations.find(
            {"contact_id": contact_id},
            {"_id": 0},
        ).sort("last_message_at", -1).limit(limit):
            for k in ("created_at", "updated_at", "last_message_at"):
                if hasattr(conv.get(k), "isoformat"):
                    conv[k] = conv[k].isoformat()
            convs.append(conv)
        return convs

    # ══════════════════════════════════════════
    # CROSS-CHANNEL ROUTING
    # ══════════════════════════════════════════

    async def route_inbound(
        self,
        channel: str,
        sender_email: str = "",
        sender_phone: str = "",
        content: str = "",
        metadata: dict = None,
    ) -> dict:
        """
        Eingehende Nachricht routen:
        1. Kontakt identifizieren/erstellen
        2. Offene Konversation finden/erstellen
        3. Nachricht speichern
        4. Routing-Entscheidung (AI / Admin / Eskalation)
        """
        # Kontakt identifizieren
        if sender_email:
            contact = await self.get_or_create_contact(sender_email, channel=channel)
        elif sender_phone:
            contact = await self.db.contacts.find_one(
                {"phone": sender_phone}, {"_id": 0}
            )
            if not contact:
                contact = create_contact(
                    f"{sender_phone}@phone.nexifyai.local",
                    phone=sender_phone,
                    channel=channel,
                )
                await self.db.contacts.insert_one({**contact})
        else:
            return {"error": "Kein Absender identifiziert"}

        contact_id = contact["contact_id"]

        # Konversation
        conv = await self.get_or_create_conversation(
            contact_id, channel, subject=content[:80] if content else ""
        )

        # Nachricht speichern
        msg = await self.add_message(
            conv["conversation_id"], channel,
            MessageDirection.INBOUND.value, content,
            sender=sender_email or sender_phone,
            metadata=metadata or {},
        )

        # Routing-Entscheidung
        routing = await self._determine_routing(conv, contact, content)

        return {
            "contact_id": contact_id,
            "conversation_id": conv["conversation_id"],
            "message_id": msg["message_id"],
            "routing": routing,
        }

    async def send_outbound(
        self,
        conversation_id: str,
        channel: str,
        content: str,
        sender: str = "system",
        ai_generated: bool = False,
        ref_id: str = "",
        ref_type: str = "",
        template_key: str = "",
    ) -> dict:
        """
        Ausgehende Nachricht senden:
        1. Content kanalspezifisch formatieren
        2. Nachricht speichern
        3. Über Worker-Queue versenden
        """
        # Kanalspezifische Formatierung
        formatted_content = self._format_for_channel(content, channel, template_key)

        # Nachricht speichern
        msg = await self.add_message(
            conversation_id, channel,
            MessageDirection.OUTBOUND.value, formatted_content,
            sender=sender, ai_generated=ai_generated,
            ref_id=ref_id, ref_type=ref_type,
        )

        # Versand über Worker (wenn verfügbar und nicht nur Chat)
        if self.worker and channel in (Channel.EMAIL.value,):
            conv = await self.db.conversations.find_one(
                {"conversation_id": conversation_id}, {"_id": 0}
            )
            if conv:
                contact = await self.db.contacts.find_one(
                    {"contact_id": conv["contact_id"]}, {"_id": 0}
                )
                if contact:
                    from workers.job_queue import JobPriority
                    await self.worker.enqueue(
                        "send_email",
                        {
                            "to": [contact["email"]],
                            "subject": f"Nachricht von NeXifyAI",
                            "html": formatted_content,
                        },
                        priority=JobPriority.HIGH,
                        ref_id=conversation_id,
                        ref_type="conversation",
                        created_by=sender,
                    )

        return msg

    # ══════════════════════════════════════════
    # ENTITY-VERKNÜPFUNG
    # ══════════════════════════════════════════

    async def link_entity(
        self, conversation_id: str, entity_type: str, entity_id: str
    ):
        """Verknüpft eine Konversation mit einem Geschäftsobjekt."""
        field_map = {
            "quote": "related_offers",
            "invoice": "related_invoices",
            "booking": "related_bookings",
            "project": "related_projects",
        }
        field = field_map.get(entity_type)
        if not field:
            return

        await self.db.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$addToSet": {field: entity_id}, "$set": {"updated_at": utcnow()}},
        )

        await self._timeline(
            "conversation", conversation_id,
            f"linked_{entity_type}",
            details={"entity_id": entity_id, "entity_type": entity_type},
        )

    # ══════════════════════════════════════════
    # KONVERSATION-STATUS
    # ══════════════════════════════════════════

    async def update_conversation_status(
        self, conversation_id: str, new_status: str, by: str = "system"
    ):
        """Konversationsstatus aktualisieren."""
        await self.db.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {"status": new_status, "updated_at": utcnow()},
            },
        )
        await self._timeline(
            "conversation", conversation_id,
            f"status_changed_to_{new_status}",
            actor=by,
        )

    async def assign_conversation(
        self, conversation_id: str, assigned_to: str, by: str = "system"
    ):
        """Konversation zuweisen (AI → Admin, Admin → Admin)."""
        await self.db.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "assigned_to": assigned_to,
                    "ai_handled": assigned_to == "ai",
                    "updated_at": utcnow(),
                },
            },
        )
        await self._timeline(
            "conversation", conversation_id,
            "conversation_assigned",
            actor=by,
            details={"assigned_to": assigned_to},
        )

    # ══════════════════════════════════════════
    # KANALÜBERGREIFENDE TIMELINE
    # ══════════════════════════════════════════

    async def get_unified_timeline(
        self, contact_id: str = None, limit: int = 50
    ) -> List[dict]:
        """Kanalübergreifende Timeline für einen Kontakt oder global."""
        query = {}
        if contact_id:
            # Alle Konversations-IDs dieses Kontakts
            conv_ids = []
            async for conv in self.db.conversations.find(
                {"contact_id": contact_id}, {"conversation_id": 1, "_id": 0}
            ):
                conv_ids.append(conv["conversation_id"])

            query = {"$or": [
                {"entity_id": contact_id},
                {"entity_id": {"$in": conv_ids}},
                {"details.contact_id": contact_id},
            ]}

        events = []
        async for evt in self.db.timeline_events.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).limit(limit):
            if hasattr(evt.get("timestamp"), "isoformat"):
                evt["timestamp"] = evt["timestamp"].isoformat()
            events.append(evt)
        return events

    # ══════════════════════════════════════════
    # INTERNE HELFER
    # ══════════════════════════════════════════

    async def _determine_routing(self, conv: dict, contact: dict, content: str) -> dict:
        """Routing-Entscheidung für eingehende Nachrichten."""
        # Einfache Regeln — erweiterbar durch KI
        routing = {
            "handler": "ai",
            "escalation": False,
            "reason": "standard_ai_routing",
        }

        # Bestehende Kunden bekommen höhere Priorität
        customer = await self.db.customers.find_one(
            {"email": contact.get("email", "")}, {"_id": 0}
        )
        if customer:
            routing["priority"] = "high"
            routing["reason"] = "existing_customer"

        # Keyword-basierte Eskalation
        escalation_keywords = ["beschwerde", "inkasso", "anwalt", "kündigung", "complaint"]
        if any(kw in content.lower() for kw in escalation_keywords):
            routing["handler"] = "admin"
            routing["escalation"] = True
            routing["reason"] = "escalation_keyword"

        return routing

    def _format_for_channel(self, content: str, channel: str, template_key: str = "") -> str:
        """Content kanalspezifisch formatieren."""
        if channel == Channel.WHATSAPP.value:
            # WhatsApp: Plain-Text, max 4096 Zeichen
            import re
            plain = re.sub(r'<[^>]+>', '', content)
            return plain[:4096]
        elif channel == Channel.EMAIL.value:
            # E-Mail: HTML
            return content
        else:
            return content

    async def _timeline(
        self, entity_type: str, entity_id: str, event: str, **kwargs
    ):
        """Timeline-Event schreiben."""
        evt = create_timeline_event(entity_type, entity_id, event, **kwargs)
        await self.db.timeline_events.insert_one({**evt})
