"""
NeXifyAI — Domain Layer: Unified Communication & CRM Models
API-First Architecture. n8n is NOT the primary default.

Domain entities:
- Customer/Lead (unified identity)
- Conversation (cross-channel thread)
- Message (per-channel message in a conversation)
- Offer/Quote
- Invoice/Payment
- Booking/Appointment
- Timeline Event (append-only audit)
- Memory (customer context facts)

Channel adapters:
- chat (website AI chat)
- email (Resend/SMTP)
- whatsapp (QR bridge connector → later official API)
- portal (customer self-service)
"""

from datetime import datetime, timezone
from enum import Enum


# ══════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════

class Channel(str, Enum):
    CHAT = "chat"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PORTAL = "portal"
    ADMIN = "admin"
    SYSTEM = "system"

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class ConversationStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"

class OfferStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    OPENED = "opened"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVISION = "revision_requested"
    EXPIRED = "expired"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    PARTIALLY_PAID = "partially_paid"

class WhatsAppSessionStatus(str, Enum):
    UNPAIRED = "unpaired"
    PAIRING = "pairing"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    DISCOVERY = "discovery"
    PLANNING = "planning"
    APPROVED = "approved"
    BUILD = "build"
    REVIEW = "review"
    HANDOVER = "handover"
    LIVE = "live"
    PAUSED = "paused"
    CLOSED = "closed"


# ══════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════

def utcnow():
    return datetime.now(timezone.utc)

def new_id(prefix="nx"):
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ══════════════════════════════════════════
# DOMAIN MODELS (dict factories for MongoDB)
# ══════════════════════════════════════════

def create_contact(email: str, **kwargs) -> dict:
    """Unified contact/lead identity."""
    return {
        "contact_id": new_id("ct"),
        "email": email.lower().strip(),
        "first_name": kwargs.get("first_name", ""),
        "last_name": kwargs.get("last_name", ""),
        "company": kwargs.get("company", ""),
        "phone": kwargs.get("phone", ""),
        "whatsapp": kwargs.get("whatsapp", ""),
        "country": kwargs.get("country", "DE"),
        "industry": kwargs.get("industry", ""),
        "website": kwargs.get("website", ""),
        "lead_status": LeadStatus.NEW.value,
        "lead_score": 0,
        "lead_source": kwargs.get("source", "website"),
        "owner": kwargs.get("owner", "system"),
        "tags": kwargs.get("tags", []),
        "enrichment": {},
        "channels_used": [],
        "notes": [],
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_conversation(contact_id: str, channel: str, **kwargs) -> dict:
    """Cross-channel conversation thread."""
    return {
        "conversation_id": new_id("conv"),
        "contact_id": contact_id,
        "channel_origin": channel,
        "channels": [channel],
        "status": ConversationStatus.OPEN.value,
        "subject": kwargs.get("subject", ""),
        "assigned_to": kwargs.get("assigned_to", "ai"),
        "ai_handled": True,
        "messages": [],
        "message_count": 0,
        "last_message_at": utcnow(),
        "qualification": {},
        "related_offers": [],
        "related_invoices": [],
        "metadata": kwargs.get("metadata", {}),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_message(conversation_id: str, channel: str, direction: str, content: str, **kwargs) -> dict:
    """Individual message within a conversation."""
    return {
        "message_id": new_id("msg"),
        "conversation_id": conversation_id,
        "channel": channel,
        "direction": direction,
        "sender": kwargs.get("sender", ""),
        "content": content,
        "content_type": kwargs.get("content_type", "text"),
        "attachments": kwargs.get("attachments", []),
        "metadata": kwargs.get("metadata", {}),
        "ai_generated": kwargs.get("ai_generated", False),
        "read": kwargs.get("read", direction == "outbound"),
        "timestamp": utcnow(),
    }


def create_timeline_event(entity_type: str, entity_id: str, event: str, **kwargs) -> dict:
    """Append-only audit/timeline event."""
    return {
        "event_id": new_id("evt"),
        "entity_type": entity_type,  # contact, conversation, offer, invoice, etc.
        "entity_id": entity_id,
        "event": event,
        "channel": kwargs.get("channel", Channel.SYSTEM.value),
        "actor": kwargs.get("actor", "system"),
        "actor_type": kwargs.get("actor_type", "system"),  # ai, admin, customer, system
        "details": kwargs.get("details", {}),
        "timestamp": utcnow(),
    }


def create_memory(contact_id: str, fact: str, **kwargs) -> dict:
    """Customer memory fact (source-bound) — mem0-konform mit Pflicht-Scoping."""
    return {
        "memory_id": new_id("mem"),
        "contact_id": contact_id,
        "user_id": kwargs.get("user_id", contact_id),
        "agent_id": kwargs.get("agent_id", "system"),
        "app_id": kwargs.get("app_id", "nexifyai"),
        "run_id": kwargs.get("run_id", new_id("run")),
        "fact": fact,
        "category": kwargs.get("category", "general"),
        "source": kwargs.get("source", "chat"),
        "source_ref": kwargs.get("source_ref", ""),
        "confidence": kwargs.get("confidence", 0.8),
        "verified": kwargs.get("verified", False),
        "verification_status": kwargs.get("verification_status", "nicht verifiziert"),
        "created_at": utcnow(),
        "expires_at": kwargs.get("expires_at"),
    }


# Pflicht-Sektionen für abgeschlossene Projektplanung
PROJECT_SECTIONS = [
    "projektsteckbrief",
    "scope_dokument",
    "projektklassifikation",
    "zielgruppen_funnel_matrix",
    "discovery_ergebnis",
    "prozesslandkarte",
    "rollen_rechtekonzept",
    "systemarchitektur_integrationsplan",
    "datenquellen_datenmodell_matrix",
    "work_packages",
    "aufwandsschaetzung",
    "milestones_ressourcenplan",
    "risiko_register",
    "angebotsentwurf",
    "design_content_seo_konzept",
    "qa_compliance_freigabeplan",
    "finance_logik",
    "audit_dokumentationsstruktur",
    "build_ready_markdown",
    "startprompt_emergent",
    "kommunikations_statuslogik",
    "fortschrittslink_strategie",
]

PROJECT_SECTION_LABELS = {
    "projektsteckbrief": "Projektsteckbrief",
    "scope_dokument": "Scope-Dokument",
    "projektklassifikation": "Projektklassifikation",
    "zielgruppen_funnel_matrix": "Zielgruppen- und Funnel-Matrix",
    "discovery_ergebnis": "Discovery-Ergebnis",
    "prozesslandkarte": "Prozesslandkarte",
    "rollen_rechtekonzept": "Rollen- und Rechtekonzept",
    "systemarchitektur_integrationsplan": "Systemarchitektur und Integrationsplan",
    "datenquellen_datenmodell_matrix": "Datenquellen- und Datenmodell-Matrix",
    "work_packages": "Work Packages",
    "aufwandsschaetzung": "Aufwandsschätzung",
    "milestones_ressourcenplan": "Milestones und Ressourcenplan",
    "risiko_register": "Risiko-Register",
    "angebotsentwurf": "Angebotsentwurf",
    "design_content_seo_konzept": "Design-/Content-/SEO-Konzept",
    "qa_compliance_freigabeplan": "QA-/Compliance-/Freigabeplan",
    "finance_logik": "Finance-Logik",
    "audit_dokumentationsstruktur": "Audit- und Dokumentationsstruktur",
    "build_ready_markdown": "Build-Ready-Markdown",
    "startprompt_emergent": "Startprompt",
    "kommunikations_statuslogik": "Kommunikations- und Statuslogik",
    "fortschrittslink_strategie": "Fortschrittslink-Strategie",
}


def create_project(customer_email: str, title: str, **kwargs) -> dict:
    """Projektkontext — führende operative Kontextebene pro Kundenprojekt."""
    return {
        "project_id": new_id("prj"),
        "customer_email": customer_email.lower().strip(),
        "contact_id": kwargs.get("contact_id", ""),
        "title": title,
        "tier": kwargs.get("tier", ""),
        "quote_id": kwargs.get("quote_id", ""),
        "contract_id": kwargs.get("contract_id", ""),
        "status": ProjectStatus.DRAFT.value,
        "classification": kwargs.get("classification", ""),
        "tags": kwargs.get("tags", []),
        "risks": [],
        "sections_status": {s: "leer" for s in PROJECT_SECTIONS},
        "build_handover_version": 0,
        "created_by": kwargs.get("created_by", "admin"),
        "assigned_to": kwargs.get("assigned_to", ""),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_project_section(project_id: str, section_key: str, content: str, **kwargs) -> dict:
    """Einzelne Projekt-Sektion mit Versionierung."""
    return {
        "section_id": new_id("sec"),
        "project_id": project_id,
        "section_key": section_key,
        "label": PROJECT_SECTION_LABELS.get(section_key, section_key),
        "content": content,
        "version": kwargs.get("version", 1),
        "status": kwargs.get("status", "entwurf"),
        "review_comments": [],
        "author": kwargs.get("author", "admin"),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_project_chat_message(project_id: str, sender: str, content: str, **kwargs) -> dict:
    """Projektchat-Nachricht."""
    return {
        "message_id": new_id("pcm"),
        "project_id": project_id,
        "sender": sender,
        "sender_type": kwargs.get("sender_type", "admin"),
        "content": content,
        "attachments": kwargs.get("attachments", []),
        "metadata": kwargs.get("metadata", {}),
        "timestamp": utcnow(),
    }


def create_project_version(project_id: str, version_num: int, markdown: str, **kwargs) -> dict:
    """Versioniertes Build-Ready-Markdown."""
    return {
        "version_id": new_id("pv"),
        "project_id": project_id,
        "version": version_num,
        "markdown": markdown,
        "start_prompt": kwargs.get("start_prompt", ""),
        "changelog": kwargs.get("changelog", ""),
        "author": kwargs.get("author", "admin"),
        "created_at": utcnow(),
    }


def create_whatsapp_session(**kwargs) -> dict:
    """WhatsApp QR connector session state."""
    return {
        "session_id": new_id("wa"),
        "status": WhatsAppSessionStatus.UNPAIRED.value,
        "phone_number": kwargs.get("phone_number", ""),
        "qr_code": None,
        "qr_generated_at": None,
        "connected_at": None,
        "disconnected_at": None,
        "last_activity": None,
        "error": None,
        "metadata": {},
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
