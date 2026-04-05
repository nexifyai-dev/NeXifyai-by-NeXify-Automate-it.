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

class ContractStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CHANGE_REQUESTED = "change_requested"
    AMENDED = "amended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class ContractType(str, Enum):
    STANDARD = "standard"
    INDIVIDUAL = "individual"
    AMENDMENT = "amendment"

class AppendixType(str, Enum):
    AI_AGENTS = "ai_agents"
    WEBSITE = "website"
    SEO = "seo"
    APP = "app"
    AI_ADDON = "ai_addon"
    BUNDLE = "bundle"
    CUSTOM = "custom"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class DeliverableStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    DELIVERED = "delivered"
    REJECTED = "rejected"


class ReviewCycleStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    FEEDBACK_GIVEN = "feedback_given"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class BuildPhase(str, Enum):
    NOT_STARTED = "not_started"
    SETUP = "setup"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    DEPLOYMENT = "deployment"
    LIVE = "live"
    MAINTENANCE = "maintenance"


class AuditVerification(str, Enum):
    VERIFIZIERT = "verifiziert"
    TEILWEISE_VERIFIZIERT = "teilweise verifiziert"
    NICHT_VERIFIZIERT = "nicht verifiziert"
    WIDERLEGT = "widerlegt"


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


APPENDIX_TYPE_LABELS = {
    "ai_agents": "KI-Agenten",
    "website": "Website",
    "seo": "SEO",
    "app": "App-Entwicklung",
    "ai_addon": "KI Add-on",
    "bundle": "Bundle",
    "custom": "Sonderposition",
}

LEGAL_MODULES = [
    {"key": "agb", "label": "Allgemeine Geschäftsbedingungen", "required": True},
    {"key": "datenschutz", "label": "Datenschutzerklärung", "required": True},
    {"key": "ki_hinweise", "label": "KI-Nutzungshinweise", "required": True},
    {"key": "zahlungsbedingungen", "label": "Zahlungsbedingungen", "required": True},
    {"key": "sla", "label": "Service Level Agreement", "required": False},
    {"key": "auftragsverarbeitung", "label": "Auftragsverarbeitungsvertrag (AVV)", "required": False},
]


def create_contract(customer: dict, tier_key: str, contract_type: str = "standard", **kwargs) -> dict:
    """Mastervertrag-Objekt."""
    return {
        "contract_id": new_id("ctr"),
        "contract_number": kwargs.get("contract_number", ""),
        "contract_type": contract_type,
        "title": kwargs.get("title", ""),
        "status": ContractStatus.DRAFT.value,
        "customer": {
            "email": customer.get("email", "").lower().strip(),
            "name": customer.get("name", ""),
            "company": customer.get("company", ""),
            "phone": customer.get("phone", ""),
            "address": customer.get("address", ""),
        },
        "tier_key": tier_key,
        "quote_id": kwargs.get("quote_id", ""),
        "project_id": kwargs.get("project_id", ""),
        "calculation": kwargs.get("calculation", {}),
        "legal_modules": {m["key"]: {"accepted": False, "version": "1.0"} for m in LEGAL_MODULES},
        "appendices": [],
        "version": 1,
        "versions_history": [],
        "signature": None,
        "evidence": None,
        "notes": kwargs.get("notes", ""),
        "valid_until": kwargs.get("valid_until", ""),
        "created_by": kwargs.get("created_by", "admin"),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_contract_appendix(contract_id: str, appendix_type: str, title: str, content: dict, **kwargs) -> dict:
    """Modulare Vertragsanlage."""
    return {
        "appendix_id": new_id("apx"),
        "contract_id": contract_id,
        "appendix_type": appendix_type,
        "title": title,
        "label": APPENDIX_TYPE_LABELS.get(appendix_type, appendix_type),
        "content": content,
        "pricing": kwargs.get("pricing", {}),
        "version": kwargs.get("version", 1),
        "status": kwargs.get("status", "draft"),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_contract_evidence(contract_id: str, action: str, ip: str, user_agent: str, doc_hash: str, **kwargs) -> dict:
    """Evidenzpaket für digitale Annahme/Ablehnung."""
    return {
        "evidence_id": new_id("evd"),
        "contract_id": contract_id,
        "action": action,
        "timestamp": utcnow().isoformat(),
        "ip_address": ip,
        "user_agent": user_agent,
        "document_hash": doc_hash,
        "contract_version": kwargs.get("contract_version", 1),
        "consent_status": kwargs.get("consent_status", ""),
        "legal_modules_accepted": kwargs.get("legal_modules_accepted", {}),
        "signature_type": kwargs.get("signature_type", ""),
        "signature_data": kwargs.get("signature_data", ""),
        "customer_email": kwargs.get("customer_email", ""),
        "customer_name": kwargs.get("customer_name", ""),
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


# ══════════════════════════════════════════
# P2 PFLICHT-MODELLE: Payment, Audit, PromptHandover, BuildStatus, ReviewCycle, Deliverable
# ══════════════════════════════════════════

def create_payment(invoice_id: str, amount: float, method: str, **kwargs) -> dict:
    """Zahlungsobjekt — Transaktion zu einer Rechnung."""
    return {
        "payment_id": new_id("pay"),
        "invoice_id": invoice_id,
        "amount": amount,
        "currency": kwargs.get("currency", "EUR"),
        "method": method,  # revolut, bank_transfer, cash
        "status": PaymentStatus.PENDING.value,
        "provider_ref": kwargs.get("provider_ref", ""),  # Revolut order_id etc.
        "customer_email": kwargs.get("customer_email", ""),
        "idempotency_key": kwargs.get("idempotency_key", new_id("idem")),
        "metadata": kwargs.get("metadata", {}),
        "paid_at": None,
        "failed_at": None,
        "refunded_at": None,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_audit_entry(action: str, actor: str, **kwargs) -> dict:
    """Audit-Trail-Eintrag — Pflicht: kein relevanter Schritt ohne History."""
    return {
        "audit_id": new_id("aud"),
        "action": action,
        "actor": actor,
        "actor_type": kwargs.get("actor_type", "system"),  # admin, customer, agent, system
        "entity_type": kwargs.get("entity_type", ""),
        "entity_id": kwargs.get("entity_id", ""),
        "verification_status": kwargs.get("verification_status", AuditVerification.NICHT_VERIFIZIERT.value),
        "details": kwargs.get("details", {}),
        "source": kwargs.get("source", ""),
        "ip_address": kwargs.get("ip_address", ""),
        "user_agent": kwargs.get("user_agent", ""),
        "timestamp": utcnow(),
    }


def create_prompt_handover(project_id: str, context_markdown: str, **kwargs) -> dict:
    """Prompt-Handover — Kontextpaket für Build-Agent / Entwickler."""
    return {
        "handover_id": new_id("ho"),
        "project_id": project_id,
        "version": kwargs.get("version", 1),
        "context_markdown": context_markdown,
        "system_prompt": kwargs.get("system_prompt", ""),
        "architecture_notes": kwargs.get("architecture_notes", ""),
        "scope_summary": kwargs.get("scope_summary", ""),
        "constraints": kwargs.get("constraints", []),
        "tech_stack": kwargs.get("tech_stack", {}),
        "dependencies": kwargs.get("dependencies", []),
        "review_status": kwargs.get("review_status", "entwurf"),
        "approved_by": kwargs.get("approved_by", ""),
        "approved_at": None,
        "created_by": kwargs.get("created_by", "admin"),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_build_status(project_id: str, **kwargs) -> dict:
    """Build-Status-Tracking — operativer Stand pro Projekt."""
    return {
        "build_status_id": new_id("bs"),
        "project_id": project_id,
        "phase": BuildPhase.NOT_STARTED.value,
        "progress_pct": 0,
        "milestones_completed": [],
        "milestones_total": kwargs.get("milestones_total", []),
        "current_sprint": kwargs.get("current_sprint", ""),
        "blockers": [],
        "last_deploy_at": None,
        "deploy_url": kwargs.get("deploy_url", ""),
        "test_coverage_pct": 0,
        "qa_sign_off": False,
        "notes": kwargs.get("notes", ""),
        "updated_by": kwargs.get("updated_by", "system"),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_review_cycle(project_id: str, deliverable_id: str, reviewer: str, **kwargs) -> dict:
    """Review-Zyklus — formalisiertes Feedback-Loop."""
    return {
        "review_id": new_id("rev"),
        "project_id": project_id,
        "deliverable_id": deliverable_id,
        "reviewer": reviewer,
        "reviewer_type": kwargs.get("reviewer_type", "customer"),  # customer, admin, qa
        "status": ReviewCycleStatus.OPEN.value,
        "feedback": [],
        "round": kwargs.get("round", 1),
        "max_rounds": kwargs.get("max_rounds", 3),
        "deadline": kwargs.get("deadline", ""),
        "approved_at": None,
        "rejected_reason": kwargs.get("rejected_reason", ""),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


def create_deliverable(project_id: str, title: str, **kwargs) -> dict:
    """Deliverable — lieferbares Artefakt im Projektkontext."""
    return {
        "deliverable_id": new_id("del"),
        "project_id": project_id,
        "title": title,
        "description": kwargs.get("description", ""),
        "deliverable_type": kwargs.get("deliverable_type", ""),  # feature, page, integration, document
        "status": DeliverableStatus.PLANNED.value,
        "priority": kwargs.get("priority", "medium"),
        "assigned_to": kwargs.get("assigned_to", ""),
        "sprint": kwargs.get("sprint", ""),
        "milestone": kwargs.get("milestone", ""),
        "acceptance_criteria": kwargs.get("acceptance_criteria", []),
        "review_cycles": [],
        "artifacts": [],  # URLs, storage paths
        "estimated_hours": kwargs.get("estimated_hours", 0),
        "actual_hours": kwargs.get("actual_hours", 0),
        "completed_at": None,
        "delivered_at": None,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
