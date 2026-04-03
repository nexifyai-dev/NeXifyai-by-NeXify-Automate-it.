"""
Outbound Lead Machine mit Legal Gate.

Pipeline:
1. Lead-Discovery / Firmenfindung
2. Vorqualifizierung
3. Unternehmensanalyse
4. Website-/Social-/Positionierungsanalyse
5. Fit-Scoring gegen NeXifyAI-Produkte
6. Personalisierte Erstansprache
7. Follow-up-Logik
8. Übergabe in Angebot / Termin / Nurture
9. Vollständige History in Admin, Memory, Audit, Timeline

Pflichtregeln:
- Keine blinde Massenansprache
- Keine generischen E-Mails
- Keine Ansprache ohne dokumentierte Passung
- Jede Ansprache basiert auf realer Analyse
- Opt-out/Suppression-Logik
- Legal-Gate: DSGVO, UWG, kanalspezifische Rechtslage
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from domain import LeadStatus, Channel, new_id, utcnow, create_timeline_event

logger = logging.getLogger("nexifyai.services.outbound")


# ══════════════════════════════════════════
# OUTBOUND STATUS
# ══════════════════════════════════════════

class OutboundStatus:
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    LEGAL_BLOCKED = "legal_blocked"
    OUTREACH_READY = "outreach_ready"
    CONTACTED = "contacted"
    FOLLOWUP_1 = "followup_1"
    FOLLOWUP_2 = "followup_2"
    FOLLOWUP_3 = "followup_3"
    RESPONDED = "responded"
    MEETING_BOOKED = "meeting_booked"
    QUOTE_SENT = "quote_sent"
    NURTURE = "nurture"
    OPT_OUT = "opt_out"
    SUPPRESSED = "suppressed"


# ══════════════════════════════════════════
# PRODUCT FIT SCORING
# ══════════════════════════════════════════

PRODUCT_FIT_CRITERIA = {
    "NXA-SAA-24-499": {
        "name": "Starter AI Agenten AG",
        "ideal_size": "1-50",
        "ideal_industries": ["handwerk", "beratung", "agentur", "dienstleistung", "handel"],
        "pain_signals": ["keine website", "veraltete website", "kein crm", "manuelle prozesse", "keine ki"],
        "budget_range": "499-999",
        "weight": 1.0,
    },
    "NXA-GAA-24-1299": {
        "name": "Growth AI Agenten AG",
        "ideal_size": "10-500",
        "ideal_industries": ["technologie", "saas", "e-commerce", "finance", "immobilien", "gesundheit"],
        "pain_signals": ["skalierung", "lead-generierung", "automatisierung", "ki-strategie", "digitalisierung"],
        "budget_range": "1000-5000",
        "weight": 1.5,
    },
}


class OutboundLeadMachine:
    """
    KI-gestützte Outbound-Lead-Pipeline mit Legal Gate.
    Jeder Schritt ist auditiert, scorebar und nachvollziehbar.
    """

    def __init__(self, db, worker_manager=None, comms_service=None):
        self.db = db
        self.worker = worker_manager
        self.comms = comms_service

    # ══════════════════════════════════════════
    # 1. LEAD DISCOVERY
    # ══════════════════════════════════════════

    async def discover_lead(self, company_data: dict, source: str = "manual") -> dict:
        """
        Lead erfassen und Discovery starten.
        company_data: {name, website, industry, email, phone, country, notes}
        """
        lead_id = new_id("obl")  # outbound lead
        now = utcnow()

        lead = {
            "outbound_lead_id": lead_id,
            "company_name": company_data.get("name", ""),
            "website": company_data.get("website", ""),
            "industry": company_data.get("industry", ""),
            "contact_email": company_data.get("email", ""),
            "contact_phone": company_data.get("phone", ""),
            "contact_name": company_data.get("contact_name", ""),
            "country": company_data.get("country", "DE"),
            "source": source,
            "status": OutboundStatus.DISCOVERED,
            "score": 0,
            "fit_products": [],
            "analysis": {},
            "legal_status": "pending",
            "suppressed": False,
            "opt_out": False,
            "outreach_history": [],
            "followup_count": 0,
            "owner": company_data.get("owner", "system"),
            "notes": company_data.get("notes", ""),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        await self.db.outbound_leads.insert_one({**lead})

        await self._timeline(lead_id, "outbound_lead_discovered", {
            "company": lead["company_name"],
            "source": source,
        })

        return {"outbound_lead_id": lead_id, "status": "discovered"}

    # ══════════════════════════════════════════
    # 2. VORQUALIFIZIERUNG
    # ══════════════════════════════════════════

    async def prequalify(self, lead_id: str) -> dict:
        """Schnelle Vorqualifizierung: Doppel-Check, Suppression, Basis-Kriterien."""
        lead = await self.db.outbound_leads.find_one(
            {"outbound_lead_id": lead_id}, {"_id": 0}
        )
        if not lead:
            return {"error": "Lead nicht gefunden"}

        issues = []

        # Suppression-Check
        email = lead.get("contact_email", "")
        if email:
            suppressed = await self.db.suppression_list.find_one({"email": email.lower()})
            if suppressed:
                await self._update_status(lead_id, OutboundStatus.SUPPRESSED)
                return {"status": "suppressed", "reason": "suppression_list"}

            # Doppel-Check: bereits Kunde?
            existing_customer = await self.db.customers.find_one({"email": email.lower()})
            if existing_customer:
                issues.append("already_customer")

            # Doppel-Check: bereits Lead?
            existing_lead = await self.db.leads.find_one({"email": email.lower()})
            if existing_lead:
                issues.append("existing_inbound_lead")

        # Basis-Kriterien
        if not lead.get("company_name"):
            issues.append("no_company_name")
        if not lead.get("contact_email") and not lead.get("contact_phone"):
            issues.append("no_contact_info")

        qualified = len(issues) == 0 or (
            len(issues) == 1 and issues[0] == "existing_inbound_lead"
        )

        new_status = OutboundStatus.QUALIFIED if qualified else OutboundStatus.UNQUALIFIED
        await self._update_status(lead_id, new_status, {"prequalify_issues": issues})

        return {"status": new_status, "issues": issues, "qualified": qualified}

    # ══════════════════════════════════════════
    # 3-5. ANALYSE & SCORING
    # ══════════════════════════════════════════

    async def analyze_and_score(self, lead_id: str, analysis_data: dict = None) -> dict:
        """
        Unternehmensanalyse und Fit-Scoring.
        analysis_data kann manuell oder per KI-Agent befüllt werden.
        """
        lead = await self.db.outbound_leads.find_one(
            {"outbound_lead_id": lead_id}, {"_id": 0}
        )
        if not lead:
            return {"error": "Lead nicht gefunden"}

        # Analyse-Daten (manuell oder KI)
        analysis = analysis_data or {}
        if not analysis:
            # Basis-Analyse aus vorhandenen Daten
            analysis = {
                "company_name": lead.get("company_name", ""),
                "industry": lead.get("industry", ""),
                "website": lead.get("website", ""),
                "country": lead.get("country", "DE"),
                "analysis_type": "basic",
                "analyzed_at": utcnow().isoformat(),
            }

        # Fit-Scoring
        score, fit_products = self._calculate_fit_score(lead, analysis)

        # Update
        await self.db.outbound_leads.update_one(
            {"outbound_lead_id": lead_id},
            {"$set": {
                "analysis": analysis,
                "score": score,
                "fit_products": fit_products,
                "status": OutboundStatus.QUALIFIED if score >= 40 else OutboundStatus.UNQUALIFIED,
                "analyzed_at": utcnow().isoformat(),
                "updated_at": utcnow().isoformat(),
            }},
        )

        await self._timeline(lead_id, "outbound_lead_analyzed", {
            "score": score,
            "fit_products": fit_products,
            "analysis_type": analysis.get("analysis_type", "basic"),
        })

        return {"score": score, "fit_products": fit_products, "analysis": analysis}

    def _calculate_fit_score(self, lead: dict, analysis: dict) -> tuple:
        """Produkt-Fit berechnen. Returns (score 0-100, fit_products)."""
        score = 0
        fit_products = []
        industry = (lead.get("industry", "") or analysis.get("industry", "")).lower()

        for product_id, criteria in PRODUCT_FIT_CRITERIA.items():
            product_score = 0

            # Industry-Match
            if any(ind in industry for ind in criteria["ideal_industries"]):
                product_score += 30

            # Pain-Signal-Match
            notes = (lead.get("notes", "") + " " + analysis.get("notes", "")).lower()
            pain_matches = sum(1 for p in criteria["pain_signals"] if p in notes)
            product_score += min(30, pain_matches * 10)

            # Kontaktqualität
            if lead.get("contact_email"):
                product_score += 15
            if lead.get("contact_phone"):
                product_score += 10
            if lead.get("website"):
                product_score += 10
            if lead.get("contact_name"):
                product_score += 5

            weighted = int(product_score * criteria["weight"])
            if weighted >= 30:
                fit_products.append({
                    "product_id": product_id,
                    "name": criteria["name"],
                    "score": weighted,
                })

            score = max(score, weighted)

        return min(100, score), fit_products

    # ══════════════════════════════════════════
    # 6. LEGAL GATE
    # ══════════════════════════════════════════

    async def legal_check(self, lead_id: str) -> dict:
        """
        Legal Gate: DSGVO, UWG, kanalspezifische Rechtslage prüfen.
        Muss vor jeder Erstansprache passieren.
        """
        lead = await self.db.outbound_leads.find_one(
            {"outbound_lead_id": lead_id}, {"_id": 0}
        )
        if not lead:
            return {"error": "Lead nicht gefunden"}

        issues = []
        country = lead.get("country", "DE").upper()

        # Opt-Out-Check
        if lead.get("opt_out"):
            issues.append("opt_out_active")

        # Suppression-Check
        if lead.get("suppressed"):
            issues.append("suppressed")

        # E-Mail-Kaltansprache: B2B in DE/AT/CH unter UWG § 7 bedingt erlaubt
        # wenn konkretes geschäftliches Interesse anzunehmen ist
        if country in ("DE", "AT"):
            if not lead.get("industry"):
                issues.append("uwg:industry_unknown")
            if lead.get("score", 0) < 40:
                issues.append("uwg:insufficient_fit_score")

        # DSGVO: Berechtigtes Interesse (Art. 6 Abs. 1 lit. f)
        # Dokumentation erforderlich
        if not lead.get("analysis") or not lead["analysis"]:
            issues.append("dsgvo:no_documented_analysis")

        legal_ok = len(issues) == 0
        legal_status = "approved" if legal_ok else "blocked"

        await self.db.outbound_leads.update_one(
            {"outbound_lead_id": lead_id},
            {"$set": {
                "legal_status": legal_status,
                "legal_issues": issues,
                "legal_checked_at": utcnow().isoformat(),
                "updated_at": utcnow().isoformat(),
            }},
        )

        if legal_ok:
            await self._update_status(lead_id, OutboundStatus.OUTREACH_READY)

        await self._timeline(lead_id, "outbound_legal_check", {
            "legal_ok": legal_ok,
            "issues": issues,
            "country": country,
        })

        return {"legal_ok": legal_ok, "issues": issues, "status": legal_status}

    # ══════════════════════════════════════════
    # 7. PERSONALISIERTE ERSTANSPRACHE
    # ══════════════════════════════════════════

    async def create_outreach(self, lead_id: str, outreach_data: dict) -> dict:
        """
        Personalisierte Erstansprache erstellen.
        outreach_data: {channel, subject, content, template_key}
        """
        lead = await self.db.outbound_leads.find_one(
            {"outbound_lead_id": lead_id}, {"_id": 0}
        )
        if not lead:
            return {"error": "Lead nicht gefunden"}

        # Legal-Gate prüfen
        if lead.get("legal_status") != "approved":
            return {"error": "Legal Gate nicht bestanden", "legal_status": lead.get("legal_status")}

        channel = outreach_data.get("channel", "email")
        subject = outreach_data.get("subject", "")
        content = outreach_data.get("content", "")

        outreach_record = {
            "outreach_id": new_id("otr"),
            "channel": channel,
            "subject": subject,
            "content": content,
            "status": "draft",
            "created_at": utcnow().isoformat(),
            "sent_at": None,
            "response_at": None,
        }

        await self.db.outbound_leads.update_one(
            {"outbound_lead_id": lead_id},
            {
                "$push": {"outreach_history": outreach_record},
                "$set": {"updated_at": utcnow().isoformat()},
            },
        )

        return {"outreach_id": outreach_record["outreach_id"], "status": "draft"}

    async def send_outreach(self, lead_id: str, outreach_id: str) -> dict:
        """Outreach tatsächlich versenden (über Worker)."""
        lead = await self.db.outbound_leads.find_one(
            {"outbound_lead_id": lead_id}, {"_id": 0}
        )
        if not lead:
            return {"error": "Lead nicht gefunden"}

        outreach = None
        for o in lead.get("outreach_history", []):
            if o.get("outreach_id") == outreach_id:
                outreach = o
                break

        if not outreach:
            return {"error": "Outreach nicht gefunden"}

        if outreach.get("status") == "sent":
            return {"error": "Bereits versendet"}

        # Über Worker versenden
        if self.worker and outreach.get("channel") == "email":
            from workers.job_queue import JobPriority
            from server import email_template
            await self.worker.enqueue(
                "send_email",
                {
                    "to": [lead.get("contact_email", "")],
                    "subject": outreach.get("subject", ""),
                    "html": email_template(
                        outreach.get("subject", ""),
                        outreach.get("content", ""),
                    ),
                },
                priority=JobPriority.HIGH,
                ref_id=lead_id,
                ref_type="outbound_lead",
                created_by="outbound:outreach",
            )

        # Status aktualisieren
        await self.db.outbound_leads.update_one(
            {"outbound_lead_id": lead_id, "outreach_history.outreach_id": outreach_id},
            {"$set": {
                "outreach_history.$.status": "sent",
                "outreach_history.$.sent_at": utcnow().isoformat(),
                "status": OutboundStatus.CONTACTED,
                "updated_at": utcnow().isoformat(),
            }},
        )

        await self._timeline(lead_id, "outbound_outreach_sent", {
            "outreach_id": outreach_id,
            "channel": outreach.get("channel"),
        })

        return {"status": "sent", "outreach_id": outreach_id}

    # ══════════════════════════════════════════
    # 8. FOLLOW-UP LOGIK
    # ══════════════════════════════════════════

    async def schedule_followup(self, lead_id: str, days_delay: int = 3) -> dict:
        """Follow-up planen."""
        if self.worker:
            from workers.job_queue import JobPriority
            await self.worker.enqueue(
                "lead_followup",
                {"contact_id": lead_id, "source": "outbound"},
                priority=JobPriority.NORMAL,
                delay_seconds=days_delay * 86400,
                ref_id=lead_id,
                ref_type="outbound_lead",
                created_by="outbound:followup",
            )

        await self.db.outbound_leads.update_one(
            {"outbound_lead_id": lead_id},
            {"$inc": {"followup_count": 1},
             "$set": {"next_followup_at": (utcnow() + timedelta(days=days_delay)).isoformat()}},
        )

        return {"scheduled": True, "days_delay": days_delay}

    # ══════════════════════════════════════════
    # 9. OPT-OUT / SUPPRESSION
    # ══════════════════════════════════════════

    async def opt_out(self, email: str, reason: str = "") -> dict:
        """E-Mail auf Suppression-Liste setzen."""
        email_lower = email.lower().strip()
        await self.db.suppression_list.update_one(
            {"email": email_lower},
            {"$set": {
                "email": email_lower,
                "reason": reason,
                "opted_out_at": utcnow().isoformat(),
            }},
            upsert=True,
        )

        # Alle aktiven Outbound-Leads mit dieser E-Mail suppressen
        await self.db.outbound_leads.update_many(
            {"contact_email": email_lower},
            {"$set": {"opt_out": True, "suppressed": True, "status": OutboundStatus.OPT_OUT}},
        )

        return {"email": email_lower, "status": "opted_out"}

    # ══════════════════════════════════════════
    # ADMIN-VIEWS
    # ══════════════════════════════════════════

    async def list_outbound_leads(
        self, status: str = None, min_score: int = 0,
        skip: int = 0, limit: int = 50
    ) -> List[dict]:
        """Outbound-Leads mit Filtern auflisten."""
        query = {}
        if status:
            query["status"] = status
        if min_score > 0:
            query["score"] = {"$gte": min_score}

        leads = []
        async for lead in self.db.outbound_leads.find(
            query, {"_id": 0}
        ).sort("score", -1).skip(skip).limit(limit):
            leads.append(lead)
        return leads

    async def get_outbound_stats(self) -> dict:
        """Outbound-Pipeline-Statistiken."""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        stats = {}
        async for doc in self.db.outbound_leads.aggregate(pipeline):
            stats[doc["_id"]] = doc["count"]

        total = sum(stats.values())
        return {
            "total": total,
            "by_status": stats,
            "conversion_rate": round(
                (stats.get("meeting_booked", 0) + stats.get("quote_sent", 0)) / max(total, 1) * 100, 1
            ),
        }

    # ══════════════════════════════════════════
    # HELFER
    # ══════════════════════════════════════════

    async def _update_status(self, lead_id: str, new_status: str, details: dict = None):
        await self.db.outbound_leads.update_one(
            {"outbound_lead_id": lead_id},
            {
                "$set": {"status": new_status, "updated_at": utcnow().isoformat()},
                "$push": {"status_history": {
                    "status": new_status,
                    "at": utcnow().isoformat(),
                    "details": details or {},
                }},
            },
        )

    async def _timeline(self, lead_id: str, action: str, details: dict):
        evt = create_timeline_event("outbound_lead", lead_id, action, details=details)
        await self.db.timeline_events.insert_one({**evt})
