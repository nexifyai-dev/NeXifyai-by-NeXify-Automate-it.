"""
NeXifyAI — Shared State, Configuration, Authentication & Helper Functions.
All route modules import from here. State is populated by server.py during lifespan.
"""
import os
import secrets
import logging
import hashlib
import re
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
import resend

from domain import (
    Channel, LeadStatus, MessageDirection, ConversationStatus,
    OfferStatus, InvoiceStatus, WhatsAppSessionStatus, ProjectStatus,
    ContractStatus, ContractType, AppendixType,
    create_contact, create_conversation, create_message,
    create_timeline_event, create_memory, create_whatsapp_session,
    create_project, create_project_section, create_project_chat_message,
    create_project_version, PROJECT_SECTIONS, PROJECT_SECTION_LABELS,
    create_contract, create_contract_appendix, create_contract_evidence,
    APPENDIX_TYPE_LABELS, LEGAL_MODULES,
    new_id, utcnow,
)
from memory_service import AGENT_IDS

logger = logging.getLogger("nexifyai")


# ══════════════════════════════════════════════════════════════
# STATE — Mutable Container (resolves Python import-binding issue)
# Route files import S and access S.db, S.memory_svc, etc.
# server.py populates S.xxx during lifespan.
# ══════════════════════════════════════════════════════════════
class _AppState:
    """Runtime state container. Attributes set after import propagate to all importers."""
    db = None
    worker_mgr = None
    comms_svc = None
    billing_svc = None
    outbound_svc = None
    legal_svc = None
    llm_provider = None
    orchestrator = None
    agents = {}
    memory_svc = None
    oracle_engine = None
    rate_limit_storage = {}

S = _AppState()


# ══════════════════════════════════════════════════════════════
# CONFIGURATION — populated by server.py init_config()
# ══════════════════════════════════════════════════════════════
S.RESEND_API_KEY = ""
S.SENDER_EMAIL = ""
S.SECRET_KEY = ""
S.ALGORITHM = "HS256"
S.ACCESS_TOKEN_EXPIRE_MINUTES = 60
S.NOTIFICATION_EMAILS = []
S.EMERGENT_LLM_KEY = ""
S.ADMIN_EMAIL = ""
S.ADVISOR_SYSTEM_PROMPT = ""


def init_config():
    """Load configuration from environment. Called by server.py at startup."""
    S.RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    S.SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@send.nexify-automate.com")
    S.SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    S.ALGORITHM = "HS256"
    S.ACCESS_TOKEN_EXPIRE_MINUTES = 60
    S.NOTIFICATION_EMAILS = ["support@nexify-automate.com", "nexifyai@nexifyai.de"]
    S.EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
    S.ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "p.courbois@icloud.com")


# ══════════════════════════════════════════════════════════════
# PASSWORD HASHING
# ══════════════════════════════════════════════════════════════
try:
    from pwdlib import PasswordHash
    _pwd_context = PasswordHash.recommended()
    def hash_password(password: str) -> str:
        return _pwd_context.hash(password)
    def verify_password(plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)
except Exception:
    def hash_password(password: str) -> str:
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'nexify_salt_v3', 100000).hex()
    def verify_password(plain: str, hashed: str) -> bool:
        return hash_password(plain) == hashed


# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=S.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, S.SECRET_KEY, algorithm=S.ALGORITHM)


async def get_current_admin(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, S.SECRET_KEY, algorithms=[S.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role", "admin")
        if not email:
            raise HTTPException(status_code=401, detail="Ungültiger Token")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Keine Admin-Berechtigung")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token abgelaufen oder ungültig")
    user = await S.db.admin_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
    return user


async def get_current_customer(token: str = Depends(oauth2_scheme)):
    """JWT-basierte Kunden-Authentifizierung — Rolle: customer."""
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")
    try:
        payload = jwt.decode(token, S.SECRET_KEY, algorithms=[S.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if not email or role != "customer":
            raise HTTPException(status_code=403, detail="Kein Kundenzugang")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token abgelaufen oder ungültig")
    contact = await S.db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Kundenkonto nicht gefunden")
    return {"email": email.lower(), "contact": contact}


# ══════════════════════════════════════════════════════════════
# RATE LIMITING
# ══════════════════════════════════════════════════════════════
async def check_rate_limit(request: Request, limit: int = 30, window: int = 60):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"
    now = datetime.now(timezone.utc).timestamp()
    if key in S.rate_limit_storage:
        requests, window_start = S.rate_limit_storage[key]
        if now - window_start > window:
            S.rate_limit_storage[key] = (1, now)
        elif requests >= limit:
            raise HTTPException(status_code=429, detail="Zu viele Anfragen. Bitte warten Sie.")
        else:
            S.rate_limit_storage[key] = (requests + 1, window_start)
    else:
        S.rate_limit_storage[key] = (1, now)


# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════
async def log_audit(action: str, user: str, details: dict = None):
    await S.db.audit_log.insert_one({
        "action": action,
        "user": user,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })


async def _log_event(db_ref, event_type: str, ref_id: str, user: str, details: dict = None):
    """Log a commercial event to the audit trail."""
    await db_ref.audit_log.insert_one({
        "event_type": event_type,
        "ref_id": ref_id,
        "user": user,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })


def email_template(title: str, content: str, cta_url: str = None, cta_text: str = None) -> str:
    cta_html = f'<div style="text-align:center;margin:24px 0;"><a href="{cta_url}" style="display:inline-block;background:#ff9b7a;color:#0c1117;padding:14px 32px;font-weight:700;text-decoration:none;border-radius:6px;font-size:15px;">{cta_text}</a></div>' if cta_url else ''
    return f'''<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title></head>
<body style="margin:0;padding:0;background:#0a0f14;font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;margin:0 auto;background:#12171e;border-radius:8px;overflow:hidden;">
<tr><td style="background:#0c1117;padding:28px 32px;border-bottom:2px solid #ff9b7a;">
<span style="color:#fff;font-size:20px;font-weight:700;">NeXify</span><span style="color:#ff9b7a;font-size:20px;font-weight:700;">AI</span>
<span style="color:#555;font-size:11px;margin-left:12px;">by NeXify</span>
</td></tr>
<tr><td style="padding:36px 32px;color:#c5c9d2;font-size:14px;line-height:1.75;">
{content}
{cta_html}
</td></tr>
<tr><td style="padding:28px 32px;border-top:1px solid rgba(255,255,255,0.04);">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="vertical-align:top;padding-right:16px;">
<p style="margin:0 0 2px;color:#fff;font-weight:700;font-size:13px;">Pascal Courbois</p>
<p style="margin:0 0 8px;color:#6b7b8d;font-size:11px;">Geschäftsführer</p>
<p style="margin:0;color:#6b7b8d;font-size:11px;line-height:1.6;">
Tel: <a href="tel:+31613318856" style="color:#6b7b8d;text-decoration:none;">+31 6 133 188 56</a><br>
E-Mail: <a href="mailto:nexifyai@nexifyai.de" style="color:#ff9b7a;text-decoration:none;">nexifyai@nexifyai.de</a><br>
Web: <a href="https://nexify-automate.com" style="color:#ff9b7a;text-decoration:none;">nexify-automate.com</a>
</p>
</td></tr></table>
</td></tr>
<tr><td style="background:#0a0f14;padding:20px 32px;">
<p style="margin:0 0 12px;text-align:center;"><a href="https://nexify-automate.com" style="color:#ff9b7a;font-size:12px;text-decoration:none;font-weight:500;">KI-Agenten, Websites, Apps & SEO — nexify-automate.com</a></p>
<p style="margin:0 0 6px;text-align:center;color:#444;font-size:10px;line-height:1.8;">
NeXify Automate — Graaf van Loonstraat 1E, 5921 JA Venlo, NL | KvK: 90483944 | USt-ID: NL865786276B01
</p>
<p style="margin:0;text-align:center;font-size:10px;">
<a href="https://nexify-automate.com/de/impressum" style="color:#555;text-decoration:none;">Impressum</a> &nbsp;|&nbsp;
<a href="https://nexify-automate.com/de/datenschutz" style="color:#555;text-decoration:none;">Datenschutz</a> &nbsp;|&nbsp;
<a href="https://nexify-automate.com/de/agb" style="color:#555;text-decoration:none;">AGB</a>
</p>
<p style="margin:8px 0 0;text-align:center;font-size:9px;color:#333;">Datenschutzorientiert für den europäischen Rechtsraum entwickelt. DSGVO (EU) 2016/679.</p>
</td></tr>
</table>
</body>
</html>'''


async def send_email(to: List[str], subject: str, html: str, category: str = "transactional", ref_id: str = None):
    """E-Mail versenden — SMTP (Hostinger) als primärer Kanal, Resend als Fallback."""
    result = None
    method = None

    # 1. SMTP (Hostinger) — primärer Kanal
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    if smtp_user and smtp_pass:
        try:
            from services.email_service import send_email as smtp_send
            for recipient in to:
                r = await smtp_send(
                    to_email=recipient,
                    subject=subject,
                    html_body=html,
                    reply_to="nexifyai@nexifyai.de",
                )
                if r.get("sent"):
                    result = r
                    method = "smtp"
            if result:
                logger.info(f"E-Mail via SMTP an {to} — {subject[:50]}")
        except Exception as e:
            logger.warning(f"SMTP-Fehler: {e} — versuche Resend-Fallback")
            result = None

    # 2. Resend — Fallback
    if not result and S.RESEND_API_KEY:
        try:
            import asyncio
            result = await asyncio.to_thread(resend.Emails.send, {
                "from": f"NeXifyAI <{S.SENDER_EMAIL}>",
                "to": to,
                "subject": subject,
                "html": html
            })
            method = "resend"
            logger.info(f"E-Mail via Resend an {to} — {subject[:50]}")
        except Exception as e:
            logger.error(f"Resend-Fehler: {e}")
            result = None

    # 3. Audit-Trail
    try:
        await S.db.email_events.insert_one({
            "to": to, "subject": subject, "category": category,
            "ref_id": ref_id,
            "status": "sent" if result else "failed",
            "method": method or "none",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass

    return result


async def archive_pdf_to_storage(doc_type: str, ref_id: str, number: str, pdf_bytes: bytes, version: int = 1, extra_meta: dict = None):
    """PDF in Object Storage archivieren und DB-Referenz aktualisieren."""
    storage_path = None
    try:
        from services.storage import put_object, is_available
        if is_available():
            path = f"nexifyai/documents/{doc_type}/{ref_id}_v{version}.pdf"
            result = put_object(path, pdf_bytes, "application/pdf")
            storage_path = result.get("path", path)
            logger.info(f"PDF archived to Object Storage: {storage_path}")
    except Exception as e:
        logger.warning(f"Object Storage upload fallback: {e}")

    doc_data = {
        "ref_id": ref_id, "type": doc_type, "number": number,
        "version": version, "generated_at": utcnow().isoformat(),
    }
    if storage_path:
        doc_data["storage_path"] = storage_path
    else:
        doc_data["pdf_data"] = pdf_bytes
    if extra_meta:
        doc_data.update(extra_meta)

    await S.db.documents.update_one(
        {"ref_id": ref_id, "type": doc_type},
        {"$set": doc_data},
        upsert=True,
    )
    return storage_path


async def _build_customer_memory(email: str, current_session_id: str = None) -> str:
    """Build comprehensive customer memory context from ALL channels."""
    if not email:
        return ""
    email_lower = email.lower()
    parts = []

    lead = await S.db.leads.find_one({"email": email_lower}, {"_id": 0})
    if lead:
        parts.append(f"Kontakt: {lead.get('vorname','')} {lead.get('nachname','')}, {lead.get('unternehmen','')}, Status: {lead.get('status','')}")
        if lead.get("notes"):
            recent_notes = lead["notes"][-3:] if isinstance(lead["notes"], list) else []
            for n in recent_notes:
                if isinstance(n, dict):
                    parts.append(f"  Notiz ({n.get('date','')[:10]}): {n.get('text','')[:100]}")

    contact = await S.db.contacts.find_one({"email": email_lower}, {"_id": 0})
    contact_id = contact.get("contact_id") if contact else None
    if contact:
        channels_used = contact.get("channels_used", [])
        if channels_used:
            parts.append(f"Kanäle genutzt: {', '.join(channels_used)}")
        if contact.get("industry"):
            parts.append(f"Branche: {contact['industry']}")
        if contact.get("company"):
            parts.append(f"Firma: {contact['company']}")

    quotes = []
    async for q in S.db.quotes.find({"customer.email": email_lower}, {"_id": 0}).sort("created_at", -1).limit(5):
        status = q.get("status", "unknown")
        tier = q.get("tier", "")
        calc = q.get("calculation", {})
        quotes.append(f"Angebot {q.get('quote_number','')}: {calc.get('tier_name',tier)} — {calc.get('total_contract_eur',0):,.2f} EUR, Status: {status}")
    if quotes:
        parts.append("Angebote: " + " | ".join(quotes))

    invoices = []
    async for inv in S.db.invoices.find({"customer.email": email_lower}, {"_id": 0}).sort("created_at", -1).limit(5):
        invoices.append(f"Rechnung {inv.get('invoice_number','')}: {inv.get('total_eur',0):,.2f} EUR, Status: {inv.get('status','')}")
    if invoices:
        parts.append("Rechnungen: " + " | ".join(invoices))

    bookings = []
    async for bk in S.db.bookings.find({"email": email_lower}, {"_id": 0}).sort("created_at", -1).limit(3):
        bookings.append(f"Termin {bk.get('date','')} {bk.get('time','')}: {bk.get('status','')}")
    if bookings:
        parts.append("Termine: " + " | ".join(bookings))

    prev_sessions = []
    query = {"customer_email": email_lower}
    if current_session_id:
        query["session_id"] = {"$ne": current_session_id}
    async for sess in S.db.chat_sessions.find(query, {"_id": 0, "messages": {"$slice": -4}, "qualification": 1, "created_at": 1}).sort("created_at", -1).limit(3):
        qual = sess.get("qualification", {})
        msgs = sess.get("messages", [])
        last_user_msgs = [m["content"][:80] for m in msgs if m.get("role") == "user"][-2:]
        if last_user_msgs:
            prev_sessions.append(f"Vorheriges Gespräch: {', '.join(last_user_msgs)}")
        if qual.get("use_case"):
            prev_sessions.append(f"  Interesse: {qual['use_case']}")
    if prev_sessions:
        parts.append("Chat-Historie: " + " | ".join(prev_sessions))

    if contact_id:
        conv_summaries = []
        async for conv in S.db.conversations.find({"contact_id": contact_id}, {"_id": 0}).sort("last_message_at", -1).limit(5):
            ch = ", ".join(conv.get("channels", []))
            cnt = conv.get("message_count", 0)
            status = conv.get("status", "open")
            last_msgs = []
            async for m in S.db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0, "content": 1, "direction": 1, "channel": 1}).sort("timestamp", -1).limit(2):
                preview = m.get("content", "")[:60]
                last_msgs.append(f"[{m.get('channel','?')}/{m.get('direction','?')}] {preview}")
            summary = f"{ch} ({cnt} Nachrichten, {status})"
            if last_msgs:
                summary += ": " + " | ".join(last_msgs)
            conv_summaries.append(summary)
        if conv_summaries:
            parts.append("Kanalübergreifende Konversationen:\n  " + "\n  ".join(conv_summaries))

    if contact_id:
        facts = []
        async for mem in S.db.customer_memory.find({"contact_id": contact_id}, {"_id": 0}).sort("created_at", -1).limit(10):
            facts.append(f"[{mem.get('category','general')}] {mem.get('fact','')}")
        if facts:
            parts.append("Bekannte Fakten:\n  " + "\n  ".join(facts))

    contact_form = await S.db.inquiries.find_one({"email": email_lower}, {"_id": 0})
    if contact_form:
        parts.append(f"Kontaktanfrage: {contact_form.get('nachricht','')[:120]}")

    if not parts:
        return ""
    return "Bekannter Kunde: " + email_lower + "\n" + "\n".join(parts)
