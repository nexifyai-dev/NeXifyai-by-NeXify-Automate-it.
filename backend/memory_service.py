"""
NeXifyAI — mem0 Memory Service (Pflicht-Layer)
Zentraler Memory-Dienst mit agent_id Scoping.
Jeder Agent MUSS vor Arbeit lesen und nach jeder relevanten Änderung schreiben.

Pflicht-Scoping pro Eintrag:
  - user_id (Kontakt/Kunden-ID)
  - agent_id (z.B. emergent_build_agent, intake_agent, finance_agent)
  - app_id (nexifyai)
  - run_id (eindeutige Ausführungs-ID)
"""

from datetime import datetime, timezone
from domain import create_memory, create_audit_entry, new_id, utcnow, AuditVerification

APP_ID = "nexifyai"

# Agent-IDs nach Dokumentation
AGENT_IDS = {
    "emergent_build": "emergent_build_agent",
    "intake": "intake_agent",
    "research": "research_agent",
    "outreach": "outreach_agent",
    "offer": "offer_agent",
    "planning": "planning_agent",
    "finance": "finance_agent",
    "support": "support_agent",
    "design": "design_agent",
    "qa": "qa_agent",
    "admin": "admin_agent",
    "system": "system_agent",
    "chat": "chat_agent",
}


class MemoryService:
    """Zentraler mem0 Memory-Dienst — Pflicht für alle Agenten."""

    def __init__(self, db):
        self.db = db
        self.collection = db.customer_memory

    async def read(self, contact_id: str, agent_id: str = None, category: str = None, limit: int = 20) -> list:
        """Pflicht-Read: Kontext vor Arbeit laden."""
        query = {"contact_id": contact_id}
        if agent_id:
            query["agent_id"] = agent_id
        if category:
            query["category"] = category
        facts = []
        async for mem in self.collection.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
            facts.append(mem)
        return facts

    async def read_all_for_context(self, contact_id: str, limit: int = 30) -> str:
        """Alle Memory-Einträge als Kontext-String für Agenten aufbereiten."""
        facts = await self.read(contact_id, limit=limit)
        if not facts:
            return ""
        lines = []
        for f in facts:
            agent = f.get("agent_id", "?")
            cat = f.get("category", "general")
            verified = f.get("verification_status", "nicht verifiziert")
            lines.append(f"[{agent}/{cat}/{verified}] {f.get('fact', '')}")
        return "\n".join(lines)

    async def write(self, contact_id: str, fact: str, agent_id: str, 
                    category: str = "general", source: str = "agent",
                    source_ref: str = "", confidence: float = 0.8,
                    verification_status: str = "nicht verifiziert",
                    run_id: str = None) -> dict:
        """Pflicht-Write: Nach jeder relevanten Änderung Memory schreiben."""
        mem = create_memory(
            contact_id, fact,
            user_id=contact_id,
            agent_id=agent_id,
            app_id=APP_ID,
            run_id=run_id or new_id("run"),
            category=category,
            source=source,
            source_ref=source_ref,
            confidence=confidence,
            verification_status=verification_status,
        )
        await self.collection.insert_one(mem)
        mem.pop("_id", None)
        return mem

    async def write_verified(self, contact_id: str, fact: str, agent_id: str,
                              category: str = "general", source: str = "agent",
                              source_ref: str = "", run_id: str = None) -> dict:
        """Verifizierter Memory-Eintrag."""
        return await self.write(
            contact_id, fact, agent_id, category, source, source_ref,
            confidence=1.0, verification_status="verifiziert", run_id=run_id,
        )

    async def search(self, query_text: str, contact_id: str = None, limit: int = 10) -> list:
        """Einfache Text-Suche in Memory-Fakten."""
        match = {"fact": {"$regex": query_text, "$options": "i"}}
        if contact_id:
            match["contact_id"] = contact_id
        results = []
        async for mem in self.collection.find(match, {"_id": 0}).sort("created_at", -1).limit(limit):
            results.append(mem)
        return results

    async def get_agent_history(self, agent_id: str, limit: int = 20) -> list:
        """Alle Memory-Einträge eines bestimmten Agenten."""
        results = []
        async for mem in self.collection.find({"agent_id": agent_id}, {"_id": 0}).sort("created_at", -1).limit(limit):
            results.append(mem)
        return results

    async def write_classified(self, contact_id: str, fact: str, agent_id: str,
                               verification: str, category: str = "general",
                               source: str = "agent", source_ref: str = "",
                               run_id: str = None) -> dict:
        """Memory-Write mit Pflicht-Klassifizierung (verifiziert/teilweise/nicht/widerlegt)."""
        valid = {v.value for v in AuditVerification}
        if verification not in valid:
            verification = AuditVerification.NICHT_VERIFIZIERT.value
        confidence = {
            AuditVerification.VERIFIZIERT.value: 1.0,
            AuditVerification.TEILWEISE_VERIFIZIERT.value: 0.7,
            AuditVerification.NICHT_VERIFIZIERT.value: 0.3,
            AuditVerification.WIDERLEGT.value: 0.0,
        }.get(verification, 0.3)
        return await self.write(
            contact_id, fact, agent_id, category, source, source_ref,
            confidence=confidence, verification_status=verification, run_id=run_id,
        )

    async def audit_action(self, action: str, actor: str, actor_type: str = "system",
                           entity_type: str = "", entity_id: str = "",
                           verification: str = "nicht verifiziert",
                           details: dict = None, source: str = "",
                           ip_address: str = "", user_agent: str = "") -> dict:
        """Audit-Trail-Eintrag mit Pflicht-Klassifizierung."""
        entry = create_audit_entry(
            action=action, actor=actor, actor_type=actor_type,
            entity_type=entity_type, entity_id=entity_id,
            verification_status=verification, details=details or {},
            source=source, ip_address=ip_address, user_agent=user_agent,
        )
        await self.db.audit_log.insert_one(entry)
        entry.pop("_id", None)
        return entry

    async def audit_verified(self, action: str, actor: str, **kwargs) -> dict:
        """Verifizierter Audit-Eintrag."""
        return await self.audit_action(
            action=action, actor=actor,
            verification=AuditVerification.VERIFIZIERT.value, **kwargs,
        )

    async def get_audit_trail(self, entity_type: str = None, entity_id: str = None,
                              actor: str = None, limit: int = 50) -> list:
        """Audit-Trail für ein Entity oder einen Actor abrufen."""
        query = {}
        if entity_type:
            query["entity_type"] = entity_type
        if entity_id:
            query["entity_id"] = entity_id
        if actor:
            query["actor"] = actor
        results = []
        async for entry in self.db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit):
            if "timestamp" in entry and hasattr(entry["timestamp"], "isoformat"):
                entry["timestamp"] = entry["timestamp"].isoformat()
            results.append(entry)
        return results

    # ══════════════════════════════════════════════════════════════
    # ORACLE — Single Source of Truth (Kontakt-Level)
    # ══════════════════════════════════════════════════════════════

    async def get_contact_oracle(self, contact_id: str = None, email: str = None) -> dict:
        """
        Oracle: Vollständiger IST-Stand eines Kontakts —
        Lead-Daten, Bookings, Quotes, Invoices, Contracts, Chat-Verlauf, Memory.
        Einzelne Wahrheitsquelle für alle Agenten und Admin-Oberflächen.
        """
        query = {"contact_id": contact_id} if contact_id else {"email": email}
        if not contact_id and not email:
            return {"error": "contact_id oder email erforderlich"}

        # Lead/Customer-Stammdaten
        lead = await self.db.leads.find_one(query, {"_id": 0})
        customer = await self.db.customers.find_one(
            {"email": email} if email else {"contact_id": contact_id}, {"_id": 0}
        )

        # Resolve contact_id from lead if only email was provided
        cid = contact_id or (lead or {}).get("contact_id") or (customer or {}).get("contact_id")

        # Bookings
        bk_query = {"contact_id": cid} if cid else {"email": email}
        bookings = []
        async for b in self.db.bookings.find(bk_query, {"_id": 0}).sort("created_at", -1).limit(10):
            bookings.append(b)

        # Quotes
        q_query = {"customer.email": email} if email else {"customer.contact_id": cid}
        quotes = []
        async for q in self.db.quotes.find(q_query, {"_id": 0, "history": 0}).sort("created_at", -1).limit(10):
            quotes.append(q)

        # Invoices
        invoices = []
        async for inv in self.db.invoices.find(q_query, {"_id": 0, "history": 0}).sort("created_at", -1).limit(10):
            invoices.append(inv)

        # Contracts
        contracts = []
        async for c in self.db.contracts.find(q_query, {"_id": 0, "history": 0}).sort("created_at", -1).limit(10):
            contracts.append(c)

        # Chat sessions/messages
        chat_query = {"contact_id": cid} if cid else {"email": email}
        chat_sessions = []
        async for cs in self.db.chat_sessions.find(chat_query, {"_id": 0}).sort("created_at", -1).limit(5):
            chat_sessions.append(cs)

        messages = []
        async for msg in self.db.messages.find(chat_query, {"_id": 0}).sort("created_at", -1).limit(20):
            messages.append(msg)

        # Memory (alle Agenten)
        memory_facts = await self.read(cid, limit=30) if cid else []

        # Timeline-Events
        timeline = []
        te_query = {"ref_id": cid} if cid else {}
        async for te in self.db.timeline_events.find(te_query, {"_id": 0}).sort("timestamp", -1).limit(20):
            if "timestamp" in te and hasattr(te["timestamp"], "isoformat"):
                te["timestamp"] = te["timestamp"].isoformat()
            timeline.append(te)

        # Audit entries
        audit = await self.get_audit_trail(entity_id=cid, limit=15) if cid else []

        return {
            "contact_id": cid,
            "oracle_type": "contact_full",
            "timestamp": utcnow().isoformat(),
            "stammdaten": {
                "lead": lead,
                "customer": customer,
            },
            "bookings": bookings,
            "quotes": quotes,
            "invoices": invoices,
            "contracts": contracts,
            "communication": {
                "chat_sessions": chat_sessions,
                "recent_messages": messages,
            },
            "memory": memory_facts,
            "timeline": timeline,
            "audit": audit,
        }
