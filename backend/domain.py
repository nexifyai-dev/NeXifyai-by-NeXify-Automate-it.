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
    """Customer memory fact (source-bound)."""
    return {
        "memory_id": new_id("mem"),
        "contact_id": contact_id,
        "fact": fact,
        "category": kwargs.get("category", "general"),  # interest, objection, requirement, preference, context
        "source": kwargs.get("source", "chat"),
        "source_ref": kwargs.get("source_ref", ""),
        "confidence": kwargs.get("confidence", 0.8),
        "created_at": utcnow(),
        "expires_at": kwargs.get("expires_at"),
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
