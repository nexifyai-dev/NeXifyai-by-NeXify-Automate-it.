"""NeXifyAI — Public Routes"""
import os
import re
import json
import secrets
import asyncio
from datetime import datetime, timezone, timedelta
from io import BytesIO
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address
from routes.shared import S
from routes.shared import (
    check_rate_limit,
    send_email,
    email_template,
    _build_customer_memory,
    log_audit,
    logger,
)
from domain import create_contact, create_timeline_event, new_id, utcnow
from memory_service import AGENT_IDS
from commercial import (
    TARIFF_CONFIG, calc_contract, get_tariff, get_commercial_faq,
    SERVICE_CATALOG, BUNDLE_CATALOG, PRODUCT_DESCRIPTIONS,
    COMPLIANCE_STATUS, ISO_GAP_ANALYSIS, generate_tariff_sheet_pdf,
    generate_quote_pdf, generate_access_token, get_next_number,
    COMPANY_DATA as COMM_COMPANY,
)

router = APIRouter(tags=["public"])


def get_system_prompt(language="de"):
    """Build the full system prompt with date context and language instruction."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    weekday_de = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][datetime.now(timezone.utc).weekday()]
    lang_instruction = ""
    if language == "nl":
        lang_instruction = "\n\nBELANGRIJK: Antwoord altijd in het Nederlands (u-vorm). Schrijf de merknaam altijd als NeXify**AI** (met vetgedrukt AI). Gebruik dezelfde opmaakregels: **vetgedrukt**, opsommingstekens, genummerde lijsten."
    elif language == "en":
        lang_instruction = "\n\nIMPORTANT: Always respond in English. Always write the brand name as NeXify**AI** (with bold AI). Use the same formatting rules: **bold** for key terms, bullet points, numbered lists."
    base = getattr(S, "ADVISOR_SYSTEM_PROMPT", "Du bist der NeXifyAI Advisor.")
    return base + f"\n\nWICHTIG: Das heutige Datum ist {today} ({weekday_de}). Alle Terminvorschläge müssen in der Zukunft liegen (frühestens ab morgen). Verwende ausschließlich Daten im Format YYYY-MM-DD. Schlage nur Werktage (Mo-Fr) vor, keine Wochenenden." + lang_instruction


def generate_response_fallback(message: str, history: list, qualification: dict) -> str:
    """Rule-based fallback when LLM provider is unavailable."""
    msg = message.lower()
    if any(k in msg for k in ["preis", "kosten", "tarif", "price", "cost"]):
        return ("Wir bieten zwei Haupttarife an:\n\n"
                "**Starter AI Agenten AG** — 499 EUR/Monat (24 Monate)\n"
                "**Growth AI Agenten AG** — 1.299 EUR/Monat (24 Monate)\n\n"
                "Gerne erstelle ich Ihnen ein individuelles Angebot. "
                "Buchen Sie ein unverbindliches Strategiegespräch, damit wir Ihre Anforderungen besprechen können.")
    if any(k in msg for k in ["termin", "buchen", "gespräch", "meeting", "call"]):
        return ("Sehr gerne! Für ein Strategiegespräch benötige ich:\n\n"
                "1. Ihren **Vor- und Nachnamen**\n"
                "2. Ihre **geschäftliche E-Mail-Adresse**\n"
                "3. Ihren **Wunschtermin** (Mo–Fr, 09:00–17:00)\n\n"
                "Alternativ können Sie auch direkt über WhatsApp buchen: +31 6 133 188 56")
    if any(k in msg for k in ["seo", "suchmaschine", "google", "ranking"]):
        return ("Unser **KI-gesteuertes SEO** optimiert Ihre Sichtbarkeit systematisch:\n\n"
                "- **SEO Starter**: 799 EUR/Monat — 50 Keywords\n"
                "- **SEO Growth**: 1.499 EUR/Monat — 200 Keywords, Content-Strategie, Multilingual\n"
                "- **SEO Enterprise**: Individuell\n\n"
                "Was ist Ihr aktueller Stand bei Suchmaschinenoptimierung?")
    if any(k in msg for k in ["website", "webseite", "homepage", "app", "mobile"]):
        return ("Wir entwickeln maßgeschneiderte digitale Lösungen:\n\n"
                "- **Website Starter**: 2.990 EUR (bis 5 Seiten, 3 Wochen)\n"
                "- **Website Professional**: 7.490 EUR (bis 15 Seiten, Animationen, Blog)\n"
                "- **App MVP**: 9.900 EUR (iOS + Android, 8 Wochen)\n"
                "- **App Professional**: 24.900 EUR (Full-Stack, 14 Wochen)\n\n"
                "Haben Sie bereits konkrete Vorstellungen zum Umfang?")
    if any(k in msg for k in ["hallo", "hi", "guten", "moin", "hey"]):
        return ("Willkommen bei NeXify**AI**! Ich bin Ihr strategischer KI-Berater.\n\n"
                "Wie kann ich Ihnen weiterhelfen? Interessieren Sie sich für:\n"
                "- **KI-Agenten** für Vertrieb, Support oder Prozessautomation?\n"
                "- **Website-** oder **App-Entwicklung**?\n"
                "- **KI-gesteuertes SEO**?\n\n"
                "Erzählen Sie mir von Ihrem Vorhaben — ich berate Sie gerne.")
    return ("Vielen Dank für Ihre Nachricht. Leider steht unser KI-Berater gerade nicht zur Verfügung.\n\n"
            "Sie erreichen uns direkt:\n"
            "- **WhatsApp**: +31 6 133 188 56\n"
            "- **E-Mail**: support@nexify-automate.com\n\n"
            "Oder buchen Sie ein unverbindliches Strategiegespräch — wir melden uns innerhalb von 24 Stunden.")

class ContactForm(BaseModel):
    vorname: str = Field(..., min_length=2, max_length=100)
    nachname: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefon: Optional[str] = None
    unternehmen: Optional[str] = None
    nachricht: str = Field(..., min_length=10, max_length=5000)
    source: str = "contact_form"
    language: Optional[str] = "de"
    consent: bool = True
    datenschutz_akzeptiert: bool = True
    honeypot: Optional[str] = Field(None, alias="_hp")

class BookingRequest(BaseModel):
    vorname: str = Field(..., min_length=2)
    nachname: str = Field(..., min_length=2)
    email: EmailStr
    telefon: Optional[str] = None
    unternehmen: Optional[str] = None
    date: str
    time: str
    thema: Optional[str] = None
    datenschutz_akzeptiert: bool = True

class QuoteRequest(BaseModel):
    vorname: str = Field(..., min_length=2, max_length=100)
    nachname: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefon: Optional[str] = None
    unternehmen: Optional[str] = None
    interesse: str = Field(..., min_length=5, max_length=2000)
    tarif: Optional[str] = None
    budget: Optional[str] = None
    source: str = "website"
    language: Optional[str] = "de"

class ChatMessage(BaseModel):
    session_id: str
    message: str
    context: Optional[dict] = None
    language: Optional[str] = "de"

class AnalyticsEvent(BaseModel):
    event: str
    properties: Optional[dict] = {}
    session_id: Optional[str] = None


@router.get("/api/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/api/company")
async def get_company():
    return {
        "name": "NeXifyAI by NeXify",
        "tagline": "Chat it. Automate it.",
        "legal_name": "NeXify Automate",
        "ceo": "Pascal Courbois, Geschäftsführer",
        "address_de": {"street": "Wallstraße 9", "city": "41334 Nettetal-Kaldenkirchen", "country": "Deutschland"},
        "address_nl": {"street": "Graaf van Loonstraat 1E", "city": "5921 JA Venlo", "country": "Niederlande"},
        "phone": "+31 6 133 188 56",
        "email": "support@nexify-automate.com",
        "website": "nexify-automate.com",
        "kvk": "90483944",
        "vat_id": "NL865786276B01",
    }


@router.post("/api/contact")
async def submit_contact(data: ContactForm, request: Request):
    await check_rate_limit(request, limit=5, window=60)
    
    if data.honeypot:
        return {"success": True, "message": "Vielen Dank."}
    
    lead_id = f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
    
    lead = {
        "lead_id": lead_id,
        "vorname": data.vorname.strip(),
        "nachname": data.nachname.strip(),
        "email": data.email.lower(),
        "telefon": data.telefon,
        "unternehmen": data.unternehmen,
        "nachricht": data.nachricht,
        "source": data.source,
        "status": "neu",
        "notes": [],
        "consent": data.consent,
        "datenschutz_akzeptiert": data.datenschutz_akzeptiert,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await S.db.leads.insert_one(lead)
    
    # Customer email
    asyncio.create_task(send_email(
        [data.email],
        "Ihre Anfrage bei NeXifyAI – Bestätigung",
        email_template(
            "Anfrage erhalten",
            f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Vielen Dank für Ihre Anfrage</h1>
            <p>Guten Tag {data.vorname} {data.nachname},</p>
            <p>wir haben Ihre Anfrage erhalten und werden uns <strong style="color:#ffb599;">innerhalb von 24 Stunden</strong> bei Ihnen melden.</p>
            <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
            <p style="margin:0;font-size:13px;color:#8f9095;">REFERENZ-NR.</p>
            <p style="margin:4px 0 0;color:#fff;font-weight:600;">{lead_id}</p>
            </div>
            <p>Mit freundlichen Grüßen,<br>Pascal Courbois<br>Geschäftsführer, NeXify Automate</p>'''
        )
    ))
    
    # Internal notification
    asyncio.create_task(send_email(
        S.NOTIFICATION_EMAILS,
        f"[NeXifyAI] Neue Anfrage: {data.vorname} {data.nachname}",
        email_template(
            "Neue Anfrage",
            f'''<h1 style="color:#fff;font-size:20px;margin:0 0 16px;">Neue Kontaktanfrage</h1>
            <div style="background:#252a32;padding:20px;margin:16px 0;">
            <p style="margin:0 0 12px;"><span style="color:#8f9095;font-size:12px;">NAME</span><br><strong style="color:#fff;">{data.vorname} {data.nachname}</strong></p>
            <p style="margin:0 0 12px;"><span style="color:#8f9095;font-size:12px;">E-MAIL</span><br><a href="mailto:{data.email}" style="color:#ffb599;">{data.email}</a></p>
            {f'<p style="margin:0 0 12px;"><span style="color:#8f9095;font-size:12px;">TELEFON</span><br><a href="tel:{data.telefon}" style="color:#ffb599;">{data.telefon}</a></p>' if data.telefon else ''}
            {f'<p style="margin:0 0 12px;"><span style="color:#8f9095;font-size:12px;">UNTERNEHMEN</span><br><span style="color:#fff;">{data.unternehmen}</span></p>' if data.unternehmen else ''}
            <p style="margin:0;"><span style="color:#8f9095;font-size:12px;">LEAD-ID</span><br><span style="color:#fff;">{lead_id}</span></p>
            </div>
            <h2 style="color:#fff;font-size:16px;margin:24px 0 12px;">Nachricht</h2>
            <div style="background:#171c23;padding:16px;color:#c5c6cb;white-space:pre-wrap;">{data.nachricht}</div>''',
            "https://nexifyai.de/admin",
            "Im Admin öffnen"
        )
    ))
    
    return {"success": True, "message": "Vielen Dank. Wir melden uns innerhalb von 24 Stunden.", "lead_id": lead_id}


@router.get("/api/booking/slots")
async def get_slots(date: str):
    slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
    booked = await S.db.bookings.find({"date": date, "status": {"$ne": "cancelled"}}, {"time": 1}).to_list(50)
    booked_times = [b["time"] for b in booked]
    blocked = await S.db.blocked_slots.find({"date": date}, {"time": 1, "all_day": 1}).to_list(50)
    blocked_times = set()
    for b in blocked:
        if b.get("all_day"):
            return {"date": date, "slots": []}
        if b.get("time"):
            blocked_times.add(b["time"])
    return {"date": date, "slots": [s for s in slots if s not in booked_times and s not in blocked_times]}


@router.post("/api/quote/request")
async def request_individual_quote(data: QuoteRequest, request: Request):
    """Individuelle Angebotsanfrage — dreifach gesichert: MongoDB + Timeline + Memory."""
    await check_rate_limit(request, limit=5, window=120)
    now = datetime.now(timezone.utc)
    quote_id = f"QR-{now.strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    
    # 1. Lead erstellen oder aktualisieren
    existing_lead = await S.db.leads.find_one({"email": data.email})
    lead_id = None
    if existing_lead:
        lead_id = existing_lead.get("lead_id")
        await S.db.leads.update_one(
            {"email": data.email},
            {"$set": {"updated_at": now.isoformat(), "interesse": data.interesse, "tarif": data.tarif, "budget": data.budget},
             "$push": {"tags": "angebot_angefragt"}}
        )
    else:
        lead_id = f"LEAD-{now.strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
        await S.db.leads.insert_one({
            "lead_id": lead_id, "email": data.email,
            "vorname": data.vorname, "nachname": data.nachname,
            "telefon": data.telefon, "unternehmen": data.unternehmen,
            "status": "qualifiziert", "source": data.source,
            "interesse": data.interesse, "tarif": data.tarif, "budget": data.budget,
            "tags": ["angebot_angefragt"], "score": 40,
            "created_at": now.isoformat(), "updated_at": now.isoformat()
        })
    
    # 2. Angebotsanfrage speichern
    quote_req = {
        "quote_request_id": quote_id, "lead_id": lead_id,
        "email": data.email, "vorname": data.vorname, "nachname": data.nachname,
        "unternehmen": data.unternehmen, "telefon": data.telefon,
        "interesse": data.interesse, "tarif": data.tarif, "budget": data.budget,
        "status": "eingegangen", "source": data.source, "language": data.language,
        "created_at": now.isoformat()
    }
    await S.db.quote_requests.insert_one(quote_req)
    
    # 3. Timeline-Event (Audit-Trail)
    await S.db.timeline_events.insert_one({
        "event_id": f"TL-{secrets.token_hex(4).upper()}",
        "type": "quote_request", "entity_type": "lead", "entity_id": lead_id,
        "title": f"Angebotsanfrage von {data.vorname} {data.nachname}",
        "description": f"Interesse: {data.interesse[:100]}{'...' if len(data.interesse) > 100 else ''}",
        "metadata": {"quote_request_id": quote_id, "tarif": data.tarif, "email": data.email},
        "created_at": now.isoformat(), "created_by": "system"
    })
    
    # 4. Memory-Eintrag (Wissensquelle)
    if hasattr(S, 'memory_service') and S.memory_service:
        try:
            await S.memory_service.write_classified(
                content=f"Angebotsanfrage: {data.vorname} {data.nachname} ({data.email}), Interesse: {data.interesse}, Tarif: {data.tarif or 'individuell'}",
                classification="operational", category="quote_request",
                metadata={"quote_request_id": quote_id, "lead_id": lead_id}
            )
        except Exception:
            pass
    
    return {"quote_request_id": quote_id, "lead_id": lead_id, "status": "eingegangen",
            "message": "Ihre Angebotsanfrage wurde erfolgreich übermittelt. Wir melden uns innerhalb von 24 Stunden."}


@router.post("/api/booking")
async def create_booking(data: BookingRequest, request: Request):
    await check_rate_limit(request, limit=3, window=60)
    
    existing = await S.db.bookings.find_one({"date": data.date, "time": data.time, "status": {"$ne": "cancelled"}})
    if existing:
        raise HTTPException(status_code=400, detail="Dieser Termin ist nicht mehr verfügbar.")
    
    booking_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    lead_id = f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
    
    # Create lead
    await S.db.leads.insert_one({
        "lead_id": lead_id,
        "vorname": data.vorname,
        "nachname": data.nachname,
        "email": data.email.lower(),
        "telefon": data.telefon,
        "unternehmen": data.unternehmen,
        "source": "booking",
        "status": "termin_gebucht",
        "notes": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })
    
    # Create booking
    await S.db.bookings.insert_one({
        "booking_id": booking_id,
        "lead_id": lead_id,
        "vorname": data.vorname,
        "nachname": data.nachname,
        "email": data.email.lower(),
        "telefon": data.telefon,
        "unternehmen": data.unternehmen,
        "date": data.date,
        "time": data.time,
        "thema": data.thema,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc)
    })
    
    date_formatted = datetime.strptime(data.date, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    # Customer confirmation
    asyncio.create_task(send_email(
        [data.email],
        f"Ihr Beratungstermin am {date_formatted} ist bestätigt",
        email_template(
            "Termin bestätigt",
            f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr Beratungsgespräch ist bestätigt</h1>
            <p>Guten Tag {data.vorname} {data.nachname},</p>
            <p>vielen Dank für Ihre Terminbuchung. Wir freuen uns auf das Gespräch mit Ihnen.</p>
            <div style="background:#252a32;padding:24px;margin:24px 0;border-left:3px solid #ffb599;">
            <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">TERMIN</p>
            <p style="margin:0;font-size:20px;color:#ffb599;font-weight:700;">{date_formatted} um {data.time} Uhr</p>
            {f'<p style="margin:16px 0 0;font-size:12px;color:#8f9095;">THEMA</p><p style="margin:4px 0 0;color:#fff;">{data.thema}</p>' if data.thema else ''}
            <p style="margin:16px 0 0;font-size:12px;color:#8f9095;">BUCHUNGS-NR.</p>
            <p style="margin:4px 0 0;color:#fff;">{booking_id}</p>
            </div>
            <p>Sie erhalten vor dem Termin einen Link zum virtuellen Meetingraum.</p>
            <p>Mit freundlichen Grüßen,<br>Pascal Courbois</p>'''
        )
    ))
    
    # Admin notification
    asyncio.create_task(send_email(
        S.NOTIFICATION_EMAILS,
        f"[NeXifyAI] Neuer Termin: {date_formatted} {data.time} - {data.vorname} {data.nachname}",
        email_template(
            "Neuer Termin",
            f'''<h1 style="color:#fff;font-size:20px;margin:0 0 16px;">Neues Beratungsgespräch gebucht</h1>
            <div style="background:#252a32;padding:24px;margin:16px 0;">
            <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">TERMIN</p>
            <p style="margin:0 0 16px;font-size:20px;color:#ffb599;font-weight:700;">{date_formatted} um {data.time} Uhr</p>
            <p style="margin:0 0 8px;"><span style="color:#8f9095;font-size:12px;">NAME</span><br><strong style="color:#fff;">{data.vorname} {data.nachname}</strong></p>
            <p style="margin:0 0 8px;"><span style="color:#8f9095;font-size:12px;">E-MAIL</span><br><a href="mailto:{data.email}" style="color:#ffb599;">{data.email}</a></p>
            {f'<p style="margin:0 0 8px;"><span style="color:#8f9095;font-size:12px;">TELEFON</span><br><a href="tel:{data.telefon}" style="color:#ffb599;">{data.telefon}</a></p>' if data.telefon else ''}
            </div>''',
            "https://nexifyai.de/admin",
            "Im Admin öffnen"
        )
    ))
    
    return {"success": True, "message": "Ihr Beratungstermin wurde bestätigt.", "booking_id": booking_id}


@router.post("/api/chat/message")
async def chat_message(data: ChatMessage, request: Request):
    await check_rate_limit(request, limit=20, window=60)
    
    session = await S.db.chat_sessions.find_one({"session_id": data.session_id})
    if not session:
        session = {
            "session_id": data.session_id,
            "messages": [],
            "qualification": {},
            "customer_email": None,
            "created_at": datetime.now(timezone.utc)
        }
        await S.db.chat_sessions.insert_one(session)
    
    # Build customer memory context if email is known
    memory_context = ""
    customer_email = session.get("customer_email")
    if not customer_email:
        # Try to detect email from qualification or recent messages
        qual = session.get("qualification", {})
        if qual.get("email"):
            customer_email = qual["email"]
    
    if customer_email:
        memory_context = await _build_customer_memory(customer_email, data.session_id)
        if memory_context:
            # Update session with customer email
            await S.db.chat_sessions.update_one(
                {"session_id": data.session_id},
                {"$set": {"customer_email": customer_email}}
            )
    
    user_msg = {"role": "user", "content": data.message, "ts": datetime.now(timezone.utc).isoformat()}
    
    # LLM-powered response
    response_text = ""
    qualification = session.get("qualification", {})
    actions = []
    should_escalate = False
    
    try:
        if S.llm_provider:
            system_prompt = get_system_prompt(data.language or "de")
            if memory_context:
                system_prompt += f"\n\nKUNDENKONTEXT (NUR INTERN — NICHT ZITIEREN):\n{memory_context}"
            
            response_text = await S.llm_provider.chat_with_history(
                session_id=data.session_id,
                user_message=data.message,
                system_prompt=system_prompt,
                temperature=0.7,
            )
            
            # Extract email from offer/booking requests for memory linking
            offer_match_pre = re.search(r'\[OFFER_REQUEST\](.*?)\[/OFFER_REQUEST\]', response_text, re.DOTALL)
            if offer_match_pre:
                try:
                    od = json.loads(offer_match_pre.group(1))
                    if od.get("email"):
                        await S.db.chat_sessions.update_one(
                            {"session_id": data.session_id},
                            {"$set": {"customer_email": od["email"].lower()}}
                        )
                except Exception:
                    pass
            
            # Check for booking request in LLM response
            booking_match = re.search(r'\[BOOKING_REQUEST\](.*?)\[/BOOKING_REQUEST\]', response_text, re.DOTALL)
            if booking_match:
                try:
                    booking_data = json.loads(booking_match.group(1))
                    bk_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
                    lead_id = f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
                    
                    await S.db.leads.insert_one({
                        "lead_id": lead_id, "vorname": booking_data.get("vorname", ""),
                        "nachname": booking_data.get("nachname", ""), "email": booking_data.get("email", "").lower(),
                        "source": "chat_booking", "status": "termin_gebucht", "notes": [],
                        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
                    })
                    
                    await S.db.bookings.insert_one({
                        "booking_id": bk_id, "lead_id": lead_id,
                        "vorname": booking_data.get("vorname", ""), "nachname": booking_data.get("nachname", ""),
                        "email": booking_data.get("email", "").lower(),
                        "date": booking_data.get("date", ""), "time": booking_data.get("time", ""),
                        "thema": "Strategiegespräch (via Chat)", "status": "confirmed",
                        "created_at": datetime.now(timezone.utc)
                    })
                    
                    date_fmt = datetime.strptime(booking_data["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
                    import asyncio
                    asyncio.create_task(send_email(
                        [booking_data["email"]],
                        f"Ihr Beratungstermin am {date_fmt} ist bestätigt",
                        email_template("Termin bestätigt",
                            f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr Strategiegespräch ist bestätigt</h1>
                            <p>Guten Tag {booking_data["vorname"]} {booking_data["nachname"]},</p>
                            <p>Ihr Termin wurde erfolgreich über unseren KI-Advisor gebucht.</p>
                            <div style="background:#252a32;padding:24px;margin:24px 0;border-left:3px solid #ffb599;">
                            <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">TERMIN</p>
                            <p style="margin:0;font-size:20px;color:#ffb599;font-weight:700;">{date_fmt} um {booking_data["time"]} Uhr</p>
                            <p style="margin:16px 0 0;font-size:12px;color:#8f9095;">BUCHUNGS-NR.</p>
                            <p style="margin:4px 0 0;color:#fff;">{bk_id}</p></div>
                            <p>Sie erhalten rechtzeitig einen Link zum virtuellen Meetingraum.</p>
                            <p>Mit freundlichen Grüßen,<br>Pascal Courbois<br>Geschäftsführer, NeXify Automate</p>''')
                    ))
                    asyncio.create_task(send_email(
                        S.NOTIFICATION_EMAILS,
                        f"[NeXifyAI] Chat-Buchung: {date_fmt} {booking_data['time']} - {booking_data['vorname']} {booking_data['nachname']}",
                        email_template("Chat-Buchung",
                            f'''<h1 style="color:#fff;font-size:20px;margin:0 0 16px;">Neue Terminbuchung via Chat</h1>
                            <div style="background:#252a32;padding:24px;margin:16px 0;">
                            <p style="margin:0 0 16px;font-size:20px;color:#ffb599;font-weight:700;">{date_fmt} um {booking_data["time"]} Uhr</p>
                            <p style="margin:0 0 8px;"><strong style="color:#fff;">{booking_data["vorname"]} {booking_data["nachname"]}</strong></p>
                            <p style="margin:0;"><a href="mailto:{booking_data["email"]}" style="color:#ffb599;">{booking_data["email"]}</a></p></div>''',
                            "https://nexifyai.de/admin", "Im Admin öffnen")
                    ))
                    
                    response_text = re.sub(r'\[BOOKING_REQUEST\].*?\[/BOOKING_REQUEST\]', '', response_text, flags=re.DOTALL).strip()
                    qualification["booking_confirmed"] = bk_id
                    logger.info(f"Chat booking created: {bk_id}")
                except Exception as e:
                    logger.error(f"Chat booking error: {e}")

            # Check for offer request in LLM response
            offer_match = re.search(r'\[OFFER_REQUEST\](.*?)\[/OFFER_REQUEST\]', response_text, re.DOTALL)
            if offer_match:
                try:
                    offer_data = json.loads(offer_match.group(1))
                    tier = offer_data.get("tier", "starter")
                    from commercial import calc_contract as cc, get_tariff as gt, get_next_number as gnn
                    from commercial import generate_quote_pdf as gqpdf, generate_access_token as gat
                    calc = cc(tier)
                    if calc:
                        qnum = await gnn(S.db, "quote")
                        now_q = datetime.now(timezone.utc)
                        tariff = gt(tier)
                        quote_obj = {
                            "quote_id": f"q_{secrets.token_hex(8)}",
                            "quote_number": qnum,
                            "status": "generated",
                            "tier": tier,
                            "tariff_number": tariff.get("tariff_number", ""),
                            "customer": {
                                "name": offer_data.get("name", ""),
                                "email": offer_data.get("email", ""),
                                "company": offer_data.get("company", ""),
                                "phone": offer_data.get("phone", ""),
                                "country": offer_data.get("country", ""),
                                "industry": offer_data.get("industry", ""),
                            },
                            "discovery": {
                                "session_id": data.session_id,
                                "use_case": offer_data.get("use_case", ""),
                                "target_systems": offer_data.get("target_systems", ""),
                                "automations": offer_data.get("automations", ""),
                                "channels": offer_data.get("channels", ""),
                                "gdpr_relevant": offer_data.get("gdpr_relevant", True),
                                "timeline": offer_data.get("timeline", ""),
                                "special_requirements": offer_data.get("special_requirements", ""),
                            },
                            "calculation": calc,
                            "date": now_q.strftime("%d.%m.%Y"),
                            "valid_until": (now_q + timedelta(days=30)).isoformat(),
                            "created_at": now_q.isoformat(),
                            "created_by": "ai_advisor",
                            "history": [{"action": "generated_from_chat", "at": now_q.isoformat(), "by": "ai_advisor", "session": data.session_id}],
                        }
                        await S.db.quotes.insert_one(quote_obj)
                        quote_obj.pop("_id", None)
                        pdf_bytes = gqpdf(quote_obj)
                        await S.db.documents.insert_one({
                            "doc_id": f"doc_{secrets.token_hex(8)}", "type": "quote",
                            "ref_id": quote_obj["quote_id"], "number": qnum,
                            "pdf_data": pdf_bytes, "created_at": now_q.isoformat(),
                        })
                        tok = gat(offer_data.get("email", ""), "quote")
                        await S.db.access_links.insert_one({
                            "token_hash": tok["token_hash"], "customer_email": offer_data.get("email", ""),
                            "quote_id": quote_obj["quote_id"], "document_type": "quote",
                            "expires_at": tok["expires_at"], "created_at": tok["created_at"], "created_by": "ai_advisor",
                        })
                        if S.RESEND_API_KEY:
                            import base64
                            import asyncio as aio
                            pdf_b64 = base64.b64encode(pdf_bytes).decode()
                            frontend_url = os.environ.get("FRONTEND_URL", "https://nexifyai.de")
                            portal_link = f"{frontend_url}/angebot?token={tok['token']}&qid={quote_obj['quote_id']}"
                            aio.create_task(send_email(
                                [offer_data["email"]],
                                f"Ihr Angebot von NeXifyAI — {calc.get('tier_name','')}",
                                email_template("Ihr Angebot",
                                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr persönliches Angebot</h1>
                                    <p>Sehr geehrte/r {offer_data.get("name","")},</p>
                                    <p>basierend auf unserem Gespräch haben wir Ihr individuelles Angebot erstellt.</p>
                                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">TARIF</p>
                                    <p style="margin:0 0 8px;color:#ffb599;font-weight:600;">{calc.get("tier_name","")}</p>
                                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">GESAMTVERTRAGSWERT</p>
                                    <p style="margin:0;color:#fff;font-weight:600;">{calc.get("total_contract_eur",0):,.2f} EUR</p>
                                    </div>''',
                                    portal_link, "Angebot öffnen"
                                ),
                            ))
                        qualification["offer_generated"] = quote_obj["quote_id"]
                        actions.append({"type": "offer_generated", "quote_id": quote_obj["quote_id"], "quote_number": qnum, "pdf_url": f"/api/documents/quote/{quote_obj['quote_id']}/pdf"})
                        logger.info(f"Chat offer created: {qnum}")
                except Exception as e:
                    logger.error(f"Chat offer generation error: {e}")
                response_text = re.sub(r'\[OFFER_REQUEST\].*?\[/OFFER_REQUEST\]', '', response_text, flags=re.DOTALL).strip()
            
            # Detect qualification from message
            msg_lower = data.message.lower()
            kw_map = {"vertrieb": "Vertriebsautomation", "sales": "Vertriebsautomation", "crm": "CRM-Integration",
                       "erp": "ERP-Integration", "sap": "SAP-Integration", "wissen": "Wissenssystem",
                       "support": "Support-Automation", "app": "App-Entwicklung", "mobile": "Mobile-App",
                       "portal": "Kundenportal", "prozess": "Prozessautomation", "termin": "Terminbuchung",
                       "website": "Website-Entwicklung", "webseite": "Website-Entwicklung", "homepage": "Website-Entwicklung",
                       "chatbot": "KI-Chatbot", "automation": "KI-Automation", "bundle": "Bundle"}
            for kw, uc in kw_map.items():
                if kw in msg_lower:
                    qualification["use_case"] = uc
                    break
            
            if any(kw in msg_lower for kw in ["termin", "buchen", "gespräch", "beraten"]):
                should_escalate = True
        else:
            response_text = generate_response_fallback(data.message, session.get("messages", []), qualification)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        response_text = generate_response_fallback(data.message, session.get("messages", []), qualification)
    
    assistant_msg = {"role": "assistant", "content": response_text, "ts": datetime.now(timezone.utc).isoformat()}
    
    await S.db.chat_sessions.update_one(
        {"session_id": data.session_id},
        {"$push": {"messages": {"$each": [user_msg, assistant_msg]}},
         "$set": {"qualification": qualification, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # mem0 Pflicht-Write: Relevante Fakten aus dem Gespräch persistieren
    if customer_email and S.memory_svc:
        contact = await S.db.contacts.find_one({"email": customer_email.lower()})
        if contact:
            cid = contact["contact_id"]
            if qualification.get("use_case") and not session.get("_use_case_memorized"):
                await S.memory_svc.write(cid, f"Interesse an: {qualification['use_case']}", AGENT_IDS["chat"],
                                       category="interest", source="chat", source_ref=data.session_id)
                await S.db.chat_sessions.update_one({"session_id": data.session_id}, {"$set": {"_use_case_memorized": True}})
            if qualification.get("booking_confirmed"):
                await S.memory_svc.write(cid, f"Termin gebucht: {qualification['booking_confirmed']}", AGENT_IDS["chat"],
                                       category="context", source="chat", source_ref=data.session_id,
                                       verification_status="verifiziert")
            if qualification.get("offer_generated"):
                await S.memory_svc.write(cid, f"Angebot generiert: {qualification['offer_generated']}", AGENT_IDS["chat"],
                                       category="context", source="chat", source_ref=data.session_id,
                                       verification_status="verifiziert")
    
    return {"message": response_text, "qualification": qualification, "actions": actions, "should_escalate": should_escalate}


@router.post("/api/analytics/track")
async def track_event(event: AnalyticsEvent, request: Request):
    await S.db.analytics.insert_one({
        "event": event.event,
        "properties": event.properties or {},
        "session_id": event.session_id,
        "timestamp": datetime.now(timezone.utc)
    })
    return {"success": True}

# ============== ADMIN ENDPOINTS ==============


@router.get("/api/product/tariffs")
async def get_tariffs():
    """Public endpoint: all active tariffs with calculations"""
    tariffs = {}
    for key, tariff in TARIFF_CONFIG.items():
        if tariff.get("status") != "active":
            continue
        calc = calc_contract(key)
        tariffs[key] = {
            "tariff_number": tariff["tariff_number"],
            "slug": tariff["slug"],
            "name": tariff["name"],
            "reference_monthly_eur": tariff["reference_monthly_eur"],
            "contract_months": tariff["contract_months"],
            "upfront_percent": tariff["upfront_percent"],
            "agents": tariff["agents"],
            "infrastructure": tariff["infrastructure"],
            "support": tariff["support"],
            "features": tariff["features"],
            "recommended": tariff.get("recommended", False),
            "calculation": calc,
        }
    return {
        "tariffs": tariffs,
        "company": {
            "name": COMM_COMPANY["name"],
            "brand": COMM_COMPANY["brand"],
            "phone": COMM_COMPANY["phone"],
            "email": COMM_COMPANY["email"],
            "web": COMM_COMPANY["web"],
        },
        "currency": "EUR",
    }



@router.get("/api/product/faq")
async def get_product_faq():
    """FAQ derived from central TARIFF_CONFIG"""
    return {"faq": get_commercial_faq()}



@router.get("/api/product/services")
async def get_services():
    """Public: all active services (websites, apps, add-ons)"""
    services = {}
    for key, svc in SERVICE_CATALOG.items():
        if svc.get("status") != "active":
            continue
        services[key] = {k: v for k, v in svc.items() if k != "status"}
    bundles = {}
    for key, bdl in BUNDLE_CATALOG.items():
        if bdl.get("status") != "active":
            continue
        bundles[key] = {k: v for k, v in bdl.items() if k != "status"}
    return {"services": services, "bundles": bundles}



@router.get("/api/product/compliance")
async def get_compliance():
    """Public: compliance and trust status"""
    return {
        "compliance": COMPLIANCE_STATUS,
        "iso_gap_analysis": {
            k: {
                "name": v["name"],
                "summary": {
                    "fulfilled": sum(1 for c in v["controls"].values() if c["status"] == "fulfilled"),
                    "partial": sum(1 for c in v["controls"].values() if c["status"] == "partial"),
                    "delegated": sum(1 for c in v["controls"].values() if c["status"] == "delegated"),
                    "open": sum(1 for c in v["controls"].values() if c["status"] == "open"),
                    "total": len(v["controls"]),
                },
                "controls": v["controls"],
            }
            for k, v in ISO_GAP_ANALYSIS.items()
        },
        "company": {
            "name": COMM_COMPANY["name"],
            "kvk": COMM_COMPANY["kvk"],
            "vat_id": COMM_COMPANY["vat_id"],
            "hosting": "EU (Frankfurt, Amsterdam)",
        },
    }



# --- Tariff Sheet PDF Download ---


@router.get("/api/product/tariff-sheet")
async def download_tariff_sheet(category: str = "all"):
    """Download a CI-branded tariff comparison PDF"""
    valid = ("all", "agents", "websites", "seo", "apps", "addons", "bundles")
    if category not in valid:
        raise HTTPException(400, f"Ungültige Kategorie. Erlaubt: {', '.join(valid)}")
    pdf_bytes = generate_tariff_sheet_pdf(category)
    filename = f"NeXifyAI_Tarife_{category}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )




@router.get("/api/product/descriptions")
async def get_product_descriptions():
    """Complete product descriptions for all services"""
    return {
        "products": {k: v for k, v in PRODUCT_DESCRIPTIONS.items()},
        "services": {k: {
            "tariff_number": v["tariff_number"],
            "name": v["name"],
            "category": v.get("category", ""),
            "price": v.get("price_eur") or v.get("price_monthly_eur") or 0,
            "billing_mode": v.get("billing_mode", "one_time"),
            "features": v.get("features", []),
            "target": v.get("target", ""),
        } for k, v in SERVICE_CATALOG.items()},
        "bundles": {k: {
            "tariff_number": v["tariff_number"],
            "name": v["name"],
            "description": v["description"],
            "bundle_price_eur": v["bundle_price_eur"],
            "savings_desc": v.get("savings_desc", ""),
            "includes": v.get("includes", []),
        } for k, v in BUNDLE_CATALOG.items()},
    }


# --- Quote Management (Admin) ---


@router.post("/api/public/opt-out")
async def public_opt_out(data: dict):
    """Öffentlicher Opt-Out-Endpoint (kein Auth erforderlich)."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    email = data.get("email", "")
    if not email:
        raise HTTPException(400, "email erforderlich")
    return await S.legal_svc.opt_out(email, data.get("reason", "self_service"), actor="customer")

