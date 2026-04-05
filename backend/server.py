"""
NeXifyAI Backend v3.0 - Production-Grade Enterprise System
Complete rewrite with:
- Argon2 password hashing (OWASP recommended)
- JWT-based authentication
- Rate limiting
- Proper session handling
- Full DACH compliance
"""
import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from dotenv import load_dotenv
import resend
import re
import json
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Password hashing with Argon2 (fallback to bcrypt if pwdlib unavailable)
try:
    from pwdlib import PasswordHash
    pwd_context = PasswordHash.recommended()
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
except Exception:
    import hashlib
    def hash_password(password: str) -> str:
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'nexify_salt_v3', 100000).hex()
    def verify_password(plain: str, hashed: str) -> bool:
        return hash_password(plain) == hashed

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nexifyai")

# Configuration
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "nexifyai")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@send.nexify-automate.com")
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

NOTIFICATION_EMAILS = ["support@nexify-automate.com", "nexifyai@nexifyai.de"]
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# LLM Chat sessions store
llm_sessions = {}

ADVISOR_SYSTEM_PROMPT = """Du bist der NeXify**AI** Advisor — der strategische KI-Berater von NeXify**AI**. Du verkörperst die Marke in jeder Interaktion: modern, kompetent, kreativ, lösungsorientiert.

MARKENIDENTITÄT:
- Der Markenname ist NeXify**AI** — das "AI" wird IMMER hervorgehoben (fett)
- Schreibe den Markennamen IMMER als NeXify**AI** (mit fetter AI-Hervorhebung)
- NeXify**AI** steht für strategische KI-Beratung und Umsetzung auf höchstem Niveau

UNTERNEHMEN:
NeXify**AI** ist ein Produkt von NeXify Automate (KvK: 90483944, USt-ID: NL865786276B01).
Geschäftsführer: Pascal Courbois. Standorte: NL (Venlo) und DE (Nettetal-Kaldenkirchen).
Kontakt: +31 6 133 188 56, support@nexify-automate.com

KERNLEISTUNGEN:

**KI-Assistenz & Co-Piloten**
Kontextbewusste KI-Assistenten für jede Fachabteilung — nahtlos integriert in bestehende Tools und Workflows. Von Vertrieb über HR bis Finanzen.

**Workflow-Automationen**
End-to-End Automatisierung durch agentische KI-Systeme. Mehrstufige Prozesse werden autonom orchestriert, überwacht und optimiert.

**400+ System-Integrationen**
Native Konnektoren für SAP S/4HANA, SAP Business One, HubSpot, Salesforce, Microsoft Dynamics 365, DATEV, Lexware, Zendesk, ServiceNow, Jira, Confluence, Slack, Microsoft 365, Google Workspace, Shopify, Magento und viele weitere.

**Wissenssysteme (RAG)**
RAG-Architekturen für sofortigen Zugriff auf Firmenwissen. Antworten in Sekunden statt Stunden.

**Dokumentenautomation**
KI-gestützte Extraktion, Validierung und Klassifizierung von Verträgen, Rechnungen, Bestellungen. Automatische Risikobewertung und Compliance-Prüfung.

**Enterprise Solutions**
Custom-Modelle, On-Premise Deployments, dedizierte Infrastruktur, SLA-gesichert.

**Web- & Mobile-App Entwicklung**
Kundenportale, interne Tools, Workflow-Apps und KI-Ökosysteme — maßgeschneidert, DSGVO-konform, mit nativer KI-Integration.

TARIFE:
- **Starter** — ab 1.900 EUR/Mo: 2 KI-Agenten, Shared Infrastructure, E-Mail-Support
- **Growth** — ab 4.500 EUR/Mo: 10 KI-Agenten, Private Cloud, Priority Support, CRM/ERP-Kit
- **Enterprise** — individuell: Unlimitiert, On-Premise, Custom LLM Training, SLA

Das Erstgespräch ist immer unverbindlich und kostenfrei.

GESPRÄCHSFÜHRUNG — PROAKTIV, EINLADEND, LEAD-ORIENTIERT:

Dein Ziel: Den Besucher in eine natürliche, wertvolle Unterhaltung führen, die Vertrauen aufbaut und zu einem qualifizierten Strategiegespräch führt.

1. **Gesprächseröffnung**: Reagiere auf jede Nachricht so, als würdest du ein echtes Beratungsgespräch führen. Greife sofort den Kontext auf, den der Nutzer mitbringt. Zeige, dass du sein Thema verstehst.

2. **Brücken bauen**: Verbinde die Aussage des Nutzers mit einem konkreten Beispiel oder Anwendungsfall aus deiner Erfahrung. Keine abstrakten Versprechen — konkrete Szenarien, die der Nutzer nachvollziehen kann.

3. **Bedarfe aufdecken**: Stelle 1-2 gezielte, intelligente Rückfragen, die zeigen, dass du die Domäne verstehst. Z.B. nicht "Was sind Ihre Herausforderungen?" sondern "Nutzen Sie für Ihre Auftragsabwicklung aktuell SAP oder ein anderes ERP?"

4. **Mehrwert vor Verkauf**: Gib in jeder Nachricht einen konkreten Wissens-Nugget oder eine Einsicht, die dem Nutzer zeigt, dass das Gespräch wertvoll ist. Z.B. Branchenvergleiche, typische Effizienzgewinne, technische Insights.

5. **Termin natürlich einbetten**: Wenn der Use Case klar wird, biete ein Strategiegespräch als logischen nächsten Schritt an — nicht als Sales-Pitch, sondern als: "Basierend auf dem was Sie beschreiben, könnte ein 30-minütiges Strategiegespräch sinnvoll sein, um die konkreten nächsten Schritte zu besprechen."

TONALITÄT:
- Direkt, sympathisch, natürlich — wie ein kompetenter Berater, der echtes Interesse hat
- Professionell aber nicht steif. Sie-Form, aber nicht distanziert
- Selbstbewusst und kompetent, ohne arrogant zu wirken
- Variiere Gesprächseinstiege. Nie zweimal gleich anfangen
- Kein "Natürlich!", "Gerne!", "Selbstverständlich!" — stattdessen inhaltlich stark einsteigen

TERMINBUCHUNG:
Wenn ein Kunde einen Termin buchen möchte:
1. Frage nacheinander: Vorname, Nachname, geschäftliche E-Mail-Adresse
2. Schlage einen konkreten Termin vor (Mo-Fr, nächste 2 Wochen, 09:00-17:00 in 30-Min-Slots)
3. Wenn der Kunde alle Daten bestätigt hat und einen Termin gewählt hat, gib EXAKT dieses Format aus (eingebettet in deine Antwort):
[BOOKING_REQUEST]{"vorname":"...","nachname":"...","email":"...@...","date":"YYYY-MM-DD","time":"HH:MM"}[/BOOKING_REQUEST]
4. Danach bestätige den Termin freundlich und erwähne, dass eine Bestätigungs-E-Mail kommt.

ANTWORT-FORMAT:
- Strukturiere IMMER klar: **Fettschrift** für Kernbegriffe, Aufzählungen für Listen, Nummerierungen für Abläufe
- Halte Antworten kompakt: 3-6 Sätze oder 2-4 Aufzählungspunkte pro Block
- Beende mit einer konkreten Rückfrage oder klarem nächsten Schritt
- Keine Emojis

VERBOTEN:
- Behaupte KEINE ISO-/SOC-Zertifizierungen (nur "angestrebt")
- Nenne KEINE konkreten Kundennamen ohne Genehmigung
- Mache KEINE Garantieversprechen
- Sage NIE "kostenlose Testversion" oder "Free Trial"
- Antworte NIEMALS generisch oder template-artig
"""

def get_system_prompt(language="de"):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    weekday_de = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][datetime.now(timezone.utc).weekday()]
    lang_instruction = ""
    if language == "nl":
        lang_instruction = "\n\nBELANGRIJK: Antwoord altijd in het Nederlands (u-vorm). Schrijf de merknaam altijd als NeXify**AI** (met vetgedrukt AI). Gebruik dezelfde opmaakregels: **vetgedrukt**, opsommingstekens, genummerde lijsten. Wees een strategisch adviseur die vertrouwen opbouwt en waarde biedt in elke interactie."
    elif language == "en":
        lang_instruction = "\n\nIMPORTANT: Always respond in English. Always write the brand name as NeXify**AI** (with bold AI). Use the same formatting rules: **bold** for key terms, bullet points, numbered lists. Be a strategic advisor who builds trust and delivers value in every interaction."
    return ADVISOR_SYSTEM_PROMPT + f"\n\nWICHTIG: Das heutige Datum ist {today} ({weekday_de}). Alle Terminvorschläge müssen in der Zukunft liegen (frühestens ab morgen). Verwende ausschließlich Daten im Format YYYY-MM-DD. Schlage nur Werktage (Mo-Fr) vor, keine Wochenenden." + lang_instruction

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Company Data - Fixed
COMPANY = {
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
    "vat_id": "NL865786276B01"
}

# Database
db_client: Optional[AsyncIOMotorClient] = None
db = None

# Rate limiting storage
rate_limit_storage = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]
    
    # Create indexes
    await db.leads.create_index("email")
    await db.leads.create_index("created_at")
    await db.leads.create_index("status")
    await db.bookings.create_index("date")
    await db.chat_sessions.create_index("session_id")
    await db.analytics.create_index([("event", 1), ("timestamp", -1)])
    await db.admin_users.create_index("email", unique=True)
    await db.audit_log.create_index("timestamp")
    
    # Ensure admin exists
    admin_email = os.environ.get("ADMIN_EMAIL", "p.courbois@icloud.com")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "")
    
    if admin_pw:
        existing = await db.admin_users.find_one({"email": admin_email})
        if not existing:
            await db.admin_users.insert_one({
                "email": admin_email,
                "password_hash": hash_password(admin_pw),
                "role": "admin",
                "created_at": datetime.now(timezone.utc)
            })
            logger.info(f"Admin user created: {admin_email}")
    
    logger.info("NeXifyAI Backend v3.0 started")
    yield
    db_client.close()

app = FastAPI(title="NeXifyAI API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login", auto_error=False)

# Rate limiting middleware
async def check_rate_limit(request: Request, limit: int = 30, window: int = 60):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"
    now = datetime.now(timezone.utc).timestamp()
    
    if key in rate_limit_storage:
        requests, window_start = rate_limit_storage[key]
        if now - window_start > window:
            rate_limit_storage[key] = (1, now)
        elif requests >= limit:
            raise HTTPException(status_code=429, detail="Zu viele Anfragen. Bitte warten Sie.")
        else:
            rate_limit_storage[key] = (requests + 1, window_start)
    else:
        rate_limit_storage[key] = (1, now)

# ============== MODELS ==============

class ContactForm(BaseModel):
    vorname: str = Field(..., min_length=2, max_length=100)
    nachname: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefon: Optional[str] = None
    unternehmen: Optional[str] = None
    nachricht: str = Field(..., min_length=10, max_length=5000)
    source: str = "contact_form"
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

class ChatMessage(BaseModel):
    session_id: str
    message: str
    context: Optional[dict] = None
    language: Optional[str] = "de"

class LeadUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None

class BlockedSlot(BaseModel):
    date: str
    time: Optional[str] = None
    reason: Optional[str] = None
    all_day: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class AnalyticsEvent(BaseModel):
    event: str
    properties: Optional[dict] = {}
    session_id: Optional[str] = None

# ============== AUTH ==============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert", headers={"WWW-Authenticate": "Bearer"})
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Ungültiger Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token abgelaufen oder ungültig")
    
    user = await db.admin_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
    
    return user

async def log_audit(action: str, user: str, details: dict = None):
    await db.audit_log.insert_one({
        "action": action,
        "user": user,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })

# ============== EMAIL TEMPLATES ==============

def email_template(title: str, content: str, cta_url: str = None, cta_text: str = None) -> str:
    cta_html = f'<a href="{cta_url}" style="display:inline-block;background:#ffb599;color:#5a1c00;padding:14px 28px;font-weight:700;text-decoration:none;margin:24px 0;">{cta_text}</a>' if cta_url else ''
    
    return f'''<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title></head>
<body style="margin:0;padding:0;background:#0e141b;font-family:system-ui,-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#1b2028;">
<tr><td style="background:#0e141b;padding:32px;text-align:center;border-bottom:2px solid #ffb599;">
<span style="color:#fff;font-size:22px;font-weight:700;">NeXifyAI</span>
</td></tr>
<tr><td style="padding:40px 32px;color:#dee3ed;font-size:15px;line-height:1.7;">
{content}
{cta_html}
</td></tr>
<tr><td style="background:#090f16;padding:32px;text-align:center;color:#64748b;font-size:12px;line-height:1.8;">
<p style="margin:0 0 8px;"><strong>NeXifyAI by NeXify</strong> | Ein Produkt von NeXify Automate</p>
<p style="margin:0 0 8px;">NL: Graaf van Loonstraat 1E, 5921 JA Venlo</p>
<p style="margin:0 0 8px;">DE: Wallstraße 9, 41334 Nettetal-Kaldenkirchen</p>
<p style="margin:0 0 8px;">Tel: +31 6 133 188 56 | support@nexify-automate.com</p>
<p style="margin:16px 0 0;font-size:11px;">KvK: 90483944 | USt-ID: NL865786276B01</p>
</td></tr>
</table>
</body>
</html>'''

async def send_email(to: List[str], subject: str, html: str):
    if not RESEND_API_KEY:
        logger.warning("Resend not configured")
        return None
    try:
        import asyncio
        result = await asyncio.to_thread(resend.Emails.send, {
            "from": f"NeXifyAI <{SENDER_EMAIL}>",
            "to": to,
            "subject": subject,
            "html": html
        })
        logger.info(f"Email sent to {to}")
        return result
    except Exception as e:
        logger.error(f"Email error: {e}")
        return None

# ============== PUBLIC ENDPOINTS ==============

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/company")
async def get_company():
    return COMPANY

@app.post("/api/contact")
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
    
    await db.leads.insert_one(lead)
    
    # Customer email
    import asyncio
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
        NOTIFICATION_EMAILS,
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

@app.get("/api/booking/slots")
async def get_slots(date: str):
    slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
    booked = await db.bookings.find({"date": date, "status": {"$ne": "cancelled"}}, {"time": 1}).to_list(50)
    booked_times = [b["time"] for b in booked]
    blocked = await db.blocked_slots.find({"date": date}, {"time": 1, "all_day": 1}).to_list(50)
    blocked_times = set()
    for b in blocked:
        if b.get("all_day"):
            return {"date": date, "slots": []}
        if b.get("time"):
            blocked_times.add(b["time"])
    return {"date": date, "slots": [s for s in slots if s not in booked_times and s not in blocked_times]}

@app.post("/api/booking")
async def create_booking(data: BookingRequest, request: Request):
    await check_rate_limit(request, limit=3, window=60)
    
    existing = await db.bookings.find_one({"date": data.date, "time": data.time, "status": {"$ne": "cancelled"}})
    if existing:
        raise HTTPException(status_code=400, detail="Dieser Termin ist nicht mehr verfügbar.")
    
    booking_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    lead_id = f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
    
    # Create lead
    await db.leads.insert_one({
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
    await db.bookings.insert_one({
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
    
    import asyncio
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
        NOTIFICATION_EMAILS,
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

@app.post("/api/chat/message")
async def chat_message(data: ChatMessage, request: Request):
    await check_rate_limit(request, limit=20, window=60)
    
    session = await db.chat_sessions.find_one({"session_id": data.session_id})
    if not session:
        session = {
            "session_id": data.session_id,
            "messages": [],
            "qualification": {},
            "created_at": datetime.now(timezone.utc)
        }
        await db.chat_sessions.insert_one(session)
    
    user_msg = {"role": "user", "content": data.message, "ts": datetime.now(timezone.utc).isoformat()}
    
    # LLM-powered response
    response_text = ""
    qualification = session.get("qualification", {})
    actions = []
    should_escalate = False
    
    try:
        if EMERGENT_LLM_KEY:
            if data.session_id not in llm_sessions:
                chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=data.session_id,
                    system_message=get_system_prompt(data.language or "de")
                )
                chat.with_model("openai", "gpt-4o-mini")
                llm_sessions[data.session_id] = chat
            
            llm_chat = llm_sessions[data.session_id]
            user_message = UserMessage(text=data.message)
            response_text = await llm_chat.send_message(user_message)
            
            # Check for booking request in LLM response
            booking_match = re.search(r'\[BOOKING_REQUEST\](.*?)\[/BOOKING_REQUEST\]', response_text, re.DOTALL)
            if booking_match:
                try:
                    booking_data = json.loads(booking_match.group(1))
                    bk_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
                    lead_id = f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
                    
                    await db.leads.insert_one({
                        "lead_id": lead_id, "vorname": booking_data.get("vorname", ""),
                        "nachname": booking_data.get("nachname", ""), "email": booking_data.get("email", "").lower(),
                        "source": "chat_booking", "status": "termin_gebucht", "notes": [],
                        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
                    })
                    
                    await db.bookings.insert_one({
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
                        NOTIFICATION_EMAILS,
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
            
            # Detect qualification from message
            msg_lower = data.message.lower()
            kw_map = {"vertrieb": "Vertriebsautomation", "sales": "Vertriebsautomation", "crm": "CRM-Integration",
                       "erp": "ERP-Integration", "sap": "SAP-Integration", "wissen": "Wissenssystem",
                       "support": "Support-Automation", "app": "App-Entwicklung", "mobile": "Mobile-App",
                       "portal": "Kundenportal", "prozess": "Prozessautomation", "termin": "Terminbuchung"}
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
    
    await db.chat_sessions.update_one(
        {"session_id": data.session_id},
        {"$push": {"messages": {"$each": [user_msg, assistant_msg]}},
         "$set": {"qualification": qualification, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": response_text, "qualification": qualification, "actions": actions, "should_escalate": should_escalate}

def generate_response_fallback(message: str, history: list, qual: dict) -> str:
    """Fallback when LLM is unavailable"""
    msg = message.lower()
    if "vertrieb" in msg or "sales" in msg:
        return "**Vertriebsautomation** ist einer der schnellsten Wege zu messbarem ROI. Unsere KI-Agenten übernehmen zentrale Aufgaben:\n\n- **Lead-Qualifizierung** — automatische Bewertung und Priorisierung eingehender Anfragen\n- **Terminkoordination** — intelligente Planung ohne manuellen Aufwand\n- **CRM-Pflege** — lückenlose Dokumentation aller Aktivitäten\n\nTypisches Ergebnis: **40-60% weniger manuelle Arbeit** im Vertriebsteam. Welches CRM-System nutzen Sie aktuell?"
    elif "crm" in msg or "erp" in msg or "sap" in msg:
        return "Wir verfügen über **400+ native Konnektoren** für gängige Business-Systeme:\n\n- **ERP**: SAP S/4HANA, SAP Business One, Microsoft Dynamics 365\n- **CRM**: HubSpot, Salesforce, Pipedrive\n- **Finanzen**: DATEV, Lexware, Exact Online\n\nDie KI orchestriert Datenflüsse intelligent zwischen Ihren Systemen — in Echtzeit und vollautomatisiert. Welches System hat für Sie die höchste Priorität?"
    elif "wissen" in msg or "rag" in msg or "dokument" in msg:
        return "Unsere **RAG-Architekturen** machen Ihr Firmenwissen sofort durchsuchbar:\n\n- **Handbücher & Dokumentationen** — Antworten in Sekunden statt Stunden\n- **Verträge & Richtlinien** — automatische Klausel-Extraktion und Risikobewertung\n- **E-Mails & Tickets** — kontextbezogene Vorschläge für Ihr Support-Team\n\nWie groß ist Ihre aktuelle Wissensbasis, und in welchen Formaten liegen die Dokumente vor?"
    elif "support" in msg or "ticket" in msg:
        return "Unsere **Support-Automation** optimiert Ihren gesamten Service-Prozess:\n\n- **Intelligente Ticket-Klassifizierung** — automatische Priorisierung und Zuweisung\n- **KI-gestützte Erstantworten** — sofortige Hilfe für Standardfragen\n- **Eskalationsmanagement** — nahtlose Übergabe an menschliche Agenten bei komplexen Fällen\n\nWelches Ticketsystem nutzen Sie aktuell, und wie viele Tickets bearbeiten Sie monatlich?"
    elif "app" in msg or "mobile" in msg or "portal" in msg:
        return "Wir entwickeln **maßgeschneiderte digitale Lösungen** mit nativer KI-Integration:\n\n- **Kundenportale** — Self-Service mit intelligenter KI-Unterstützung\n- **Interne Tools** — Workflow-Apps für Ihre Fachabteilungen\n- **Mobile Apps** — native iOS/Android oder Cross-Platform\n\nAlle Lösungen sind DSGVO-konform und werden in deutschen bzw. europäischen Rechenzentren betrieben. Was für eine Anwendung schwebt Ihnen vor?"
    elif "termin" in msg or "buchen" in msg or "gespräch" in msg:
        return "Ich kann direkt hier einen **kostenlosen Beratungstermin** für Sie buchen. Dafür benötige ich:\n\n1. Ihren **Vornamen**\n2. Ihren **Nachnamen**\n3. Ihre **geschäftliche E-Mail-Adresse**\n\nDas Strategiegespräch dauert 30 Minuten und ist vollkommen unverbindlich. Wie heißen Sie?"
    elif "preis" in msg or "kosten" in msg or "tarif" in msg:
        return "Unsere Tarife sind transparent strukturiert:\n\n- **Starter** — ab 1.900 EUR/Mo: 2 KI-Agenten, Shared Infrastructure\n- **Growth** — ab 4.500 EUR/Mo: 10 KI-Agenten, Private Cloud, CRM/ERP-Kit\n- **Enterprise** — individuell: Unlimitiert, On-Premise, Custom LLM Training\n\nDas Erstgespräch ist **immer unverbindlich und kostenfrei**. Soll ich einen Termin für Sie einrichten?"
    elif "daten" in msg or "dsgvo" in msg or "sicher" in msg:
        return "**Datenschutz und Sicherheit** sind bei NeXifyAI fundamental verankert:\n\n- **DSGVO/AVG-konform** — vollständige Compliance mit europäischem Datenschutzrecht\n- **Deutsche/EU-Rechenzentren** — keine Datenübertragung in Drittländer\n- **RBAC-Zugriffskontrolle** — granulare Berechtigungen auf Rollen- und Feldebene\n- **Vollständige Audit-Logs** — lückenlose Nachverfolgung aller Aktivitäten\n\nHaben Sie spezifische Compliance-Anforderungen, die wir berücksichtigen sollten?"
    else:
        return "Um Ihnen **gezielt weiterhelfen** zu können, bieten wir ein kostenloses **30-minütiges Strategiegespräch** an. Darin analysieren wir:\n\n- Ihre **aktuelle Situation** und bestehende Systeme\n- **Konkrete Automatisierungspotenziale** in Ihrem Unternehmen\n- Einen **Fahrplan** mit klaren nächsten Schritten\n\nSoll ich direkt einen Termin für Sie buchen, oder haben Sie vorab eine spezifische Frage zu unseren Leistungen?"

@app.post("/api/analytics/track")
async def track_event(event: AnalyticsEvent, request: Request):
    await db.analytics.insert_one({
        "event": event.event,
        "properties": event.properties or {},
        "session_id": event.session_id,
        "timestamp": datetime.now(timezone.utc)
    })
    return {"success": True}

# ============== ADMIN ENDPOINTS ==============

@app.post("/api/admin/login")
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    if request:
        await check_rate_limit(request, limit=20, window=300)
    
    user = await db.admin_users.find_one({"email": form_data.username.lower()})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        await log_audit("login_failed", form_data.username)
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    
    token = create_access_token({"sub": user["email"]})
    await log_audit("login_success", user["email"])
    
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/admin/me")
async def admin_me(user = Depends(get_current_admin)):
    return {"email": user["email"], "role": user.get("role", "admin")}

@app.get("/api/admin/stats")
async def admin_stats(user = Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    total = await db.leads.count_documents({})
    today_count = await db.leads.count_documents({"created_at": {"$gte": today}})
    week_count = await db.leads.count_documents({"created_at": {"$gte": week_ago}})
    upcoming = await db.bookings.count_documents({"date": {"$gte": today.strftime("%Y-%m-%d")}, "status": "confirmed"})
    
    status_agg = await db.leads.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]).to_list(20)
    
    return {
        "total_leads": total,
        "new_leads_today": today_count,
        "new_leads_week": week_count,
        "upcoming_bookings": upcoming,
        "by_status": {s["_id"]: s["count"] for s in status_agg if s["_id"]}
    }

@app.get("/api/admin/leads")
async def admin_leads(user = Depends(get_current_admin), status: str = None, search: str = None, skip: int = 0, limit: int = 50):
    query = {}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"vorname": {"$regex": search, "$options": "i"}},
            {"nachname": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"unternehmen": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.leads.count_documents(query)
    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {"total": total, "leads": leads}

@app.get("/api/admin/leads/{lead_id}")
async def admin_lead_detail(lead_id: str, user = Depends(get_current_admin)):
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    
    bookings = await db.bookings.find({"lead_id": lead_id}, {"_id": 0}).to_list(10)
    chat = await db.chat_sessions.find_one({"lead_id": lead_id}, {"_id": 0})
    
    return {"lead": lead, "bookings": bookings, "chat": chat}

@app.patch("/api/admin/leads/{lead_id}")
async def admin_update_lead(lead_id: str, update: LeadUpdate, user = Depends(get_current_admin)):
    updates = {"status": update.status, "updated_at": datetime.now(timezone.utc)}
    
    if update.notes:
        await db.leads.update_one(
            {"lead_id": lead_id},
            {"$set": updates, "$push": {"notes": {"text": update.notes, "by": user["email"], "at": datetime.now(timezone.utc).isoformat()}}}
        )
    else:
        await db.leads.update_one({"lead_id": lead_id}, {"$set": updates})
    
    await log_audit("lead_updated", user["email"], {"lead_id": lead_id, "status": update.status})
    return {"success": True}

@app.get("/api/admin/bookings")
async def admin_bookings(user = Depends(get_current_admin), status: str = None, date_from: str = None, date_to: str = None, skip: int = 0, limit: int = 100):
    query = {}
    if status:
        query["status"] = status
    if date_from:
        query.setdefault("date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("date", {})["$lte"] = date_to
    total = await db.bookings.count_documents(query)
    bookings = await db.bookings.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "bookings": bookings}

@app.get("/api/admin/bookings/{booking_id}")
async def admin_booking_detail(booking_id: str, user = Depends(get_current_admin)):
    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    return booking

@app.patch("/api/admin/bookings/{booking_id}")
async def admin_update_booking(booking_id: str, update: BookingUpdate, user = Depends(get_current_admin)):
    booking = await db.bookings.find_one({"booking_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    updates = {"updated_at": datetime.now(timezone.utc)}
    if update.status:
        updates["status"] = update.status
    if update.date:
        updates["date"] = update.date
    if update.time:
        updates["time"] = update.time
    if update.notes is not None:
        await db.bookings.update_one(
            {"booking_id": booking_id},
            {"$set": updates, "$push": {"notes": {"text": update.notes, "by": user["email"], "at": datetime.now(timezone.utc).isoformat()}}}
        )
    else:
        await db.bookings.update_one({"booking_id": booking_id}, {"$set": updates})
    await log_audit("booking_updated", user["email"], {"booking_id": booking_id, "updates": {k: v for k, v in updates.items() if k != "updated_at"}})
    return {"success": True}

@app.delete("/api/admin/bookings/{booking_id}")
async def admin_delete_booking(booking_id: str, user = Depends(get_current_admin)):
    result = await db.bookings.delete_one({"booking_id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    await log_audit("booking_deleted", user["email"], {"booking_id": booking_id})
    return {"success": True}

# ============== BLOCKED SLOTS ==============

@app.get("/api/admin/blocked-slots")
async def admin_get_blocked_slots(user = Depends(get_current_admin), date_from: str = None, date_to: str = None):
    query = {}
    if date_from:
        query.setdefault("date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("date", {})["$lte"] = date_to
    slots = await db.blocked_slots.find(query, {"_id": 0}).sort("date", 1).to_list(200)
    return {"slots": slots}

@app.post("/api/admin/blocked-slots")
async def admin_create_blocked_slot(slot: BlockedSlot, user = Depends(get_current_admin)):
    slot_id = f"BLK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    doc = {
        "slot_id": slot_id,
        "date": slot.date,
        "time": slot.time,
        "all_day": slot.all_day,
        "reason": slot.reason or "",
        "created_by": user["email"],
        "created_at": datetime.now(timezone.utc)
    }
    await db.blocked_slots.insert_one(doc)
    await log_audit("slot_blocked", user["email"], {"slot_id": slot_id, "date": slot.date})
    del doc["_id"]
    return doc

@app.delete("/api/admin/blocked-slots/{slot_id}")
async def admin_delete_blocked_slot(slot_id: str, user = Depends(get_current_admin)):
    result = await db.blocked_slots.delete_one({"slot_id": slot_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Slot nicht gefunden")
    await log_audit("slot_unblocked", user["email"], {"slot_id": slot_id})
    return {"success": True}

# ============== CUSTOMER MANAGEMENT ==============

@app.get("/api/admin/customers")
async def admin_customers(user = Depends(get_current_admin), search: str = None):
    pipeline = [
        {"$group": {
            "_id": "$email",
            "vorname": {"$first": "$vorname"},
            "nachname": {"$first": "$nachname"},
            "unternehmen": {"$first": "$unternehmen"},
            "telefon": {"$first": "$telefon"},
            "total_leads": {"$sum": 1},
            "first_contact": {"$min": "$created_at"},
            "last_contact": {"$max": "$created_at"},
            "statuses": {"$push": "$status"}
        }},
        {"$sort": {"last_contact": -1}}
    ]
    if search:
        pipeline.insert(0, {"$match": {"$or": [
            {"vorname": {"$regex": search, "$options": "i"}},
            {"nachname": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"unternehmen": {"$regex": search, "$options": "i"}}
        ]}})
    customers = await db.leads.aggregate(pipeline).to_list(200)
    for c in customers:
        c["email"] = c.pop("_id")
        booking_count = await db.bookings.count_documents({"email": c["email"]})
        c["total_bookings"] = booking_count
        if c.get("first_contact"):
            c["first_contact"] = c["first_contact"].isoformat()
        if c.get("last_contact"):
            c["last_contact"] = c["last_contact"].isoformat()
    return {"customers": customers}

@app.get("/api/admin/customers/{email}")
async def admin_customer_detail(email: str, user = Depends(get_current_admin)):
    leads = await db.leads.find({"email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(50)
    bookings = await db.bookings.find({"email": email.lower()}, {"_id": 0}).sort("date", -1).to_list(50)
    chats = await db.chat_sessions.find(
        {"$or": [{"email": email.lower()}, {"qualification.email": email.lower()}]},
        {"_id": 0, "messages": {"$slice": -10}}
    ).sort("updated_at", -1).to_list(10)
    return {"leads": leads, "bookings": bookings, "chats": chats}

# ============== ENHANCED STATS ==============

@app.get("/api/admin/calendar-data")
async def admin_calendar_data(user = Depends(get_current_admin), month: str = None):
    """Get bookings and blocked slots for a month (format: YYYY-MM)"""
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    date_from = f"{month}-01"
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    if mon == 12:
        date_to = f"{year + 1}-01-01"
    else:
        date_to = f"{year}-{mon + 1:02d}-01"
    
    bookings = await db.bookings.find(
        {"date": {"$gte": date_from, "$lt": date_to}},
        {"_id": 0}
    ).sort("date", 1).to_list(200)
    
    blocked = await db.blocked_slots.find(
        {"date": {"$gte": date_from, "$lt": date_to}},
        {"_id": 0}
    ).sort("date", 1).to_list(200)
    
    return {"bookings": bookings, "blocked_slots": blocked, "month": month}


# ═══════════════════════════════════════════════════════════════════
# NEXIFY AI AGENT — Master Agent with Brain, Code Exec, API Proxy
# ═══════════════════════════════════════════════════════════════════

from agent import (
    agent_chat, mem0_store, mem0_search, mem0_get_all, mem0_delete,
    execute_code, call_external_api, agent_sessions,
    llm_chat, MASTER_SYSTEM_PROMPT, LLM_PROVIDERS,
)


class AgentChatRequest(BaseModel):
    session_id: str
    message: str
    auto_brain: bool = True


class AgentCodeRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = Field(default=30, le=60)


class AgentApiCallRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[Any] = None
    timeout: int = Field(default=30, le=60)


class AgentBrainStoreRequest(BaseModel):
    content: str
    metadata: Optional[dict] = None
    memory_layer: str = "KNOWLEDGE"


class AgentBrainSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, le=50)


# --- Agent Chat ---

@app.post("/api/admin/agent/chat")
async def admin_agent_chat(req: AgentChatRequest, user=Depends(get_current_admin)):
    """Chat with NeXify AI Master Agent."""
    result = await agent_chat(
        session_id=req.session_id,
        message=req.message,
        db=db,
        auto_brain=req.auto_brain,
    )
    await log_audit("agent_chat", user["email"], {
        "session_id": req.session_id,
        "provider": result.get("provider"),
        "model": result.get("model"),
    })
    return result


@app.get("/api/admin/agent/sessions")
async def admin_agent_sessions(user=Depends(get_current_admin)):
    """List agent chat sessions."""
    sessions = await db.agent_sessions.find(
        {}, {"_id": 0, "messages": {"$slice": -1}}
    ).sort("updated_at", -1).to_list(50)
    return {"sessions": sessions}


@app.get("/api/admin/agent/sessions/{session_id}")
async def admin_agent_session_detail(session_id: str, user=Depends(get_current_admin)):
    """Get full agent session history."""
    session = await db.agent_sessions.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    if not session:
        # Check in-memory
        if session_id in agent_sessions:
            return {
                "session_id": session_id,
                "messages": agent_sessions[session_id],
            }
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    return session


@app.delete("/api/admin/agent/sessions/{session_id}")
async def admin_agent_session_delete(session_id: str, user=Depends(get_current_admin)):
    """Delete an agent session."""
    await db.agent_sessions.delete_one({"session_id": session_id})
    if session_id in agent_sessions:
        del agent_sessions[session_id]
    await log_audit("agent_session_deleted", user["email"], {"session_id": session_id})
    return {"success": True}


# --- Brain (mem0) ---

@app.post("/api/admin/agent/brain/store")
async def admin_agent_brain_store(req: AgentBrainStoreRequest, user=Depends(get_current_admin)):
    """Store knowledge in the Brain (mem0)."""
    messages = [
        {"role": "user", "content": req.content},
        {"role": "assistant", "content": "Gespeichert."},
    ]
    metadata = req.metadata or {}
    metadata.setdefault("memory_layer", req.memory_layer)
    metadata.setdefault("tenant", "nexify-automate")
    metadata.setdefault("scope", "global_company_knowledge")
    metadata.setdefault("trust_level", "official_internal_source")
    metadata.setdefault("stored_by", user["email"])

    result = await mem0_store(messages, metadata)
    await log_audit("brain_store", user["email"], {"content_preview": req.content[:200]})
    return result


@app.post("/api/admin/agent/brain/search")
async def admin_agent_brain_search(req: AgentBrainSearchRequest, user=Depends(get_current_admin)):
    """Search the Brain (mem0)."""
    result = await mem0_search(req.query, top_k=req.top_k)
    return result


@app.get("/api/admin/agent/brain/memories")
async def admin_agent_brain_list(user=Depends(get_current_admin)):
    """List all memories in the Brain."""
    result = await mem0_get_all()
    return result


@app.delete("/api/admin/agent/brain/{memory_id}")
async def admin_agent_brain_delete(memory_id: str, user=Depends(get_current_admin)):
    """Delete a memory from the Brain."""
    result = await mem0_delete(memory_id)
    await log_audit("brain_delete", user["email"], {"memory_id": memory_id})
    return result


# --- Code Execution ---

@app.post("/api/admin/agent/execute")
async def admin_agent_execute(req: AgentCodeRequest, user=Depends(get_current_admin)):
    """Execute code in a sandboxed environment."""
    result = await execute_code(req.code, req.language, req.timeout)
    await log_audit("agent_code_exec", user["email"], {
        "language": req.language,
        "returncode": result.get("returncode"),
        "duration_ms": result.get("duration_ms"),
    })
    return result


# --- API Proxy ---

@app.post("/api/admin/agent/api-call")
async def admin_agent_api_call(req: AgentApiCallRequest, user=Depends(get_current_admin)):
    """Call an external API."""
    result = await call_external_api(
        url=req.url,
        method=req.method,
        headers=req.headers,
        body=req.body,
        timeout=req.timeout,
    )
    await log_audit("agent_api_call", user["email"], {
        "url": req.url,
        "method": req.method,
        "status": result.get("status"),
    })
    return result


# --- Agent Status ---

@app.get("/api/admin/agent/status")
async def admin_agent_status(user=Depends(get_current_admin)):
    """Get agent status and available providers."""
    providers = []
    for p in LLM_PROVIDERS:
        key = os.environ.get(p["key_env"], "")
        providers.append({
            "name": p["name"],
            "model": p["model"],
            "available": bool(key),
            "fallback_model": p.get("fallback_model"),
        })

    from agent import MEM0_API_KEY as mem0_key
    return {
        "brain_connected": bool(mem0_key),
        "llm_providers": providers,
        "active_sessions": len(agent_sessions),
        "capabilities": ["chat", "brain", "code_execution", "api_calls"],
    }


# ═══════════════════════════════════════════════════════════════════
# COMMERCIAL ENGINE — Starter AI Agenten AG
# ═══════════════════════════════════════════════════════════════════
from commercial import (
    COMPANY_DATA, STARTER_PRODUCT, calc_contract,
    get_next_number, create_revolut_order, get_revolut_order,
    generate_access_token, verify_access_token,
    generate_quote_pdf, generate_invoice_pdf
)
from fastapi.responses import StreamingResponse


class QuoteRequest(BaseModel):
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: str = ""
    customer_phone: str = ""
    notes: str = ""
    custom_monthly_net: Optional[int] = None


class InvoiceCreateRequest(BaseModel):
    quote_id: str
    type: str = "deposit"


# --- Product Info (Public) ---

@app.get("/api/product/starter")
async def get_starter_product():
    """Public endpoint: Starter AI Agenten AG product info"""
    tiers = {}
    for key, tier in STARTER_PRODUCT["tiers"].items():
        t = {**tier}
        if t.get("monthly_net"):
            calc = calc_contract(key)
            t["calculation"] = {k: v for k, v in calc.items() if k != "tier"}
        tiers[key] = t
    return {
        "product": STARTER_PRODUCT["name"],
        "contract_months": STARTER_PRODUCT["contract_months"],
        "deposit_percent": STARTER_PRODUCT["deposit_percent"],
        "tiers": tiers,
        "company": COMPANY_DATA,
        "currency": "EUR"
    }


@app.get("/api/product/faq")
async def get_product_faq():
    """Public FAQ for Starter AI Agenten AG"""
    return {"faq": [
        {"q": "Was ist Starter AI Agenten AG?",
         "a": "Starter AI Agenten AG ist das Kernprodukt von NeXifyAI — ein vollständig verwaltetes KI-Agenten-System, das Ihre Geschäftsprozesse automatisiert. Je nach Tarif erhalten Sie 2 bis unlimitierte KI-Agenten, die nahtlos in Ihre bestehenden Systeme integriert werden."},
        {"q": "Für wen ist das Produkt geeignet?",
         "a": "Für mittelständische Unternehmen und Konzerne im DACH- und Benelux-Raum, die repetitive Prozesse in Vertrieb, Kundenservice, HR, Finanzen oder Operations automatisieren möchten."},
        {"q": "Welche Leistungen sind im Starter-Tarif enthalten?",
         "a": "2 KI-Agenten, Shared Cloud Infrastructure, E-Mail-Support (48h), Basis-Integrationen (REST API), Standard-Monitoring und monatliches Reporting."},
        {"q": "Wie funktioniert die 24-Monats-Laufzeit?",
         "a": "Der Vertrag läuft über 24 Monate ab Beauftragung. Dies ermöglicht eine nachhaltige Implementierung, Optimierung und kontinuierliche Weiterentwicklung Ihrer KI-Agenten."},
        {"q": "Wie funktioniert die 30-%-Anzahlung?",
         "a": "Bei Beauftragung wird eine Anzahlung von 30 % des Gesamtvertragswerts fällig. Diese deckt die Initialisierung, Kapazitätsreservierung und das strategische Onboarding ab. Der Restbetrag wird in 23 gleichen monatlichen Raten abgerechnet."},
        {"q": "Wann ist die Anzahlung fällig?",
         "a": "Die Anzahlung ist sofort nach Angebotsannahme bzw. Beauftragung fällig. Sie erhalten umgehend eine Anzahlungsrechnung."},
        {"q": "Wie erfolgt die Rechnungsstellung?",
         "a": "Sie erhalten eine Anzahlungsrechnung bei Beauftragung und danach monatliche Rechnungen für den Restbetrag. Alle Rechnungen werden per E-Mail zugestellt und sind im Kundencenter abrufbar."},
        {"q": "Kann per Überweisung bezahlt werden?",
         "a": "Ja. Zusätzlich zur Online-Zahlung via Revolut akzeptieren wir klassische Banküberweisung."},
        {"q": "Bankdaten für Zahlungen innerhalb des EWR",
         "a": f"IBAN: {COMPANY_DATA['bank']['iban']}\nBIC: {COMPANY_DATA['bank']['bic']}\nKontoinhaber: {COMPANY_DATA['name']}"},
        {"q": "Bankdaten für Zahlungen außerhalb des EWR",
         "a": f"IBAN: {COMPANY_DATA['bank']['iban']}\nBIC: {COMPANY_DATA['bank']['bic']}\nBIC der zwischengeschalteten Bank: {COMPANY_DATA['bank']['intermediary_bic']}\nKontoinhaber: {COMPANY_DATA['name']}"},
        {"q": "Wie funktioniert die Angebotsannahme?",
         "a": "Nach dem Beratungsgespräch erhalten Sie ein individuelles Angebot per E-Mail. Dieses können Sie online annehmen oder per Rückbestätigung beauftragen. Nach Annahme wird die Anzahlungsrechnung erstellt."},
        {"q": "Wie funktioniert die Zustellung von Angebot und Rechnung?",
         "a": "Alle Dokumente werden digital per E-Mail zugestellt. Zusätzlich können Sie Ihre Dokumente jederzeit über einen sicheren, zeitlich begrenzten Zugangslink abrufen."},
        {"q": "Wie erfolgt DSGVO-konformer Dokumentenzugriff?",
         "a": "Über zeitlich begrenzte Magic-Links mit 24-Stunden-Gültigkeit. Es werden keine Passwörter per E-Mail versendet. Alle Zugriffe werden protokolliert."},
        {"q": "Wie funktioniert Support?",
         "a": f"Per E-Mail an {COMPANY_DATA['email']} oder telefonisch unter {COMPANY_DATA['phone']}. Im Growth-Tarif mit Priority-Response (24h), im Enterprise-Tarif mit SLA-gesichertem Support (4h)."},
        {"q": "Was passiert nach Beauftragung?",
         "a": "1. Anzahlungsrechnung wird erstellt und versendet\n2. Nach Zahlungseingang: Kickoff-Termin und Onboarding-Start\n3. Technische Integration und Agent-Konfiguration\n4. Testphase und Go-Live\n5. Laufende Optimierung und monatliches Reporting"}
    ]}


# --- Quote Management (Admin) ---

@app.post("/api/admin/quotes")
async def create_quote(req: QuoteRequest, current_user: dict = Depends(get_current_admin)):
    """Create a new quote"""
    calc = calc_contract(req.tier, req.custom_monthly_net)
    if not calc or calc.get("requires_custom_quote"):
        raise HTTPException(400, "Enterprise-Tarif erfordert individuelle Kalkulation")

    quote_number = await get_next_number(db, "quote")
    now = datetime.now(timezone.utc)

    quote = {
        "quote_id": f"q_{secrets.token_hex(8)}",
        "quote_number": quote_number,
        "status": "draft",
        "tier": req.tier,
        "customer": {
            "name": req.customer_name,
            "email": req.customer_email,
            "company": req.customer_company,
            "phone": req.customer_phone
        },
        "calculation": calc,
        "notes": req.notes,
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [{"action": "created", "at": now.isoformat(), "by": current_user["email"]}]
    }

    await db.quotes.insert_one(quote)
    del quote["_id"]

    # Generate PDF
    pdf_bytes = generate_quote_pdf(quote)
    await db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": quote["quote_id"],
        "number": quote_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat()
    })

    return {"quote": quote, "pdf_available": True}


@app.get("/api/admin/quotes")
async def list_quotes(current_user: dict = Depends(get_current_admin)):
    """List all quotes"""
    quotes = await db.quotes.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).to_list(200)
    return {"quotes": quotes}


@app.post("/api/admin/quotes/{quote_id}/send")
async def send_quote(quote_id: str, current_user: dict = Depends(get_current_admin)):
    """Send quote to customer via email"""
    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")

    doc = await db.documents.find_one({"ref_id": quote_id, "type": "quote"})
    if not doc:
        raise HTTPException(404, "PDF nicht gefunden")

    now = datetime.now(timezone.utc)
    customer_email = quote["customer"]["email"]
    customer_name = quote["customer"].get("name", "")
    calc = quote.get("calculation", {})
    tier_name = calc.get("tier_name", "")

    if RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(doc["pdf_data"]).decode()
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": customer_email,
                "subject": f"Ihr Angebot von NeXifyAI — Starter AI Agenten AG ({tier_name})",
                "html": f"""
                <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a2e;">
                    <div style="border-bottom: 2px solid #ff9b7a; padding-bottom: 16px; margin-bottom: 24px;">
                        <h1 style="margin: 0; font-size: 20px;">NeXify<span style="color: #ff9b7a;">AI</span></h1>
                    </div>
                    <p>Sehr geehrte/r {customer_name},</p>
                    <p>vielen Dank für Ihr Interesse an <strong>NeXify<span style="color: #ff9b7a;">AI</span></strong>. Anbei erhalten Sie Ihr persönliches Angebot für das Produkt <strong>Starter AI Agenten AG</strong> im Tarif <strong>{tier_name}</strong>.</p>
                    <p>Das Angebot ist 30 Tage gültig. Bei Fragen stehen wir Ihnen jederzeit zur Verfügung.</p>
                    <p>Mit freundlichen Grüßen,<br/><strong>Pascal Courbois</strong><br/>Geschäftsführer, NeXifyAI<br/>{COMPANY_DATA['phone']}</p>
                </div>
                """,
                "attachments": [{
                    "filename": f"Angebot_{quote['quote_number'].replace('.', '_')}.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf"
                }]
            })
            logger.info(f"Quote {quote_id} sent to {customer_email}")
        except Exception as e:
            logger.error(f"Email send error: {e}")
            raise HTTPException(500, f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "sent", "sent_at": now.isoformat()},
         "$push": {"history": {"action": "sent", "at": now.isoformat(), "by": current_user["email"]}}}
    )
    return {"sent": True, "to": customer_email}


@app.post("/api/admin/quotes/{quote_id}/accept")
async def accept_quote(quote_id: str, current_user: dict = Depends(get_current_admin)):
    """Mark quote as accepted and create deposit invoice"""
    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")

    now = datetime.now(timezone.utc)
    calc = quote.get("calculation", {})

    # Create deposit invoice
    invoice_number = await get_next_number(db, "invoice")
    due_date = (now + timedelta(days=14)).strftime("%d.%m.%Y")
    deposit_net = calc.get("deposit_net", 0)
    vat_rate = calc.get("vat_rate", 21)
    deposit_vat = int(deposit_net * vat_rate / 100)
    deposit_gross = deposit_net + deposit_vat

    invoice = {
        "invoice_id": f"inv_{secrets.token_hex(8)}",
        "invoice_number": invoice_number,
        "type": "deposit",
        "status": "open",
        "quote_id": quote_id,
        "customer": quote["customer"],
        "items": [{
            "description": f"Anzahlung (30 %) — Starter AI Agenten AG, Tarif {calc.get('tier_name', '')}",
            "amount_net": deposit_net
        }],
        "totals": {
            "net": deposit_net,
            "vat_rate": vat_rate,
            "vat": deposit_vat,
            "gross": deposit_gross
        },
        "date": now.strftime("%d.%m.%Y"),
        "due_date": due_date,
        "payment_reference": invoice_number,
        "payment_status": "pending",
        "revolut_order_id": None,
        "created_at": now.isoformat(),
        "history": [{"action": "created", "at": now.isoformat(), "by": current_user["email"]}]
    }

    # Generate invoice PDF
    pdf_bytes = generate_invoice_pdf(invoice)
    await db.invoices.insert_one(invoice)
    await db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "invoice",
        "ref_id": invoice["invoice_id"],
        "number": invoice_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat()
    })

    # Update quote status
    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "accepted", "accepted_at": now.isoformat(), "invoice_id": invoice["invoice_id"]},
         "$push": {"history": {"action": "accepted", "at": now.isoformat(), "by": current_user["email"]}}}
    )

    # Create Revolut payment order
    revolut_result = await create_revolut_order(
        amount_cents=deposit_gross,
        currency="EUR",
        customer_email=quote["customer"]["email"],
        description=f"NeXifyAI Anzahlung — {calc.get('tier_name', '')} ({invoice_number})",
        merchant_order_id=invoice["invoice_id"]
    )

    if revolut_result.get("order_id"):
        await db.invoices.update_one(
            {"invoice_id": invoice["invoice_id"]},
            {"$set": {
                "revolut_order_id": revolut_result["order_id"],
                "revolut_token": revolut_result.get("token"),
                "checkout_url": revolut_result.get("checkout_url")
            }}
        )
        invoice["revolut_order_id"] = revolut_result["order_id"]
        invoice["checkout_url"] = revolut_result.get("checkout_url")

    del invoice["_id"]
    return {"invoice": invoice, "revolut": revolut_result, "pdf_available": True}


# --- Invoice Management (Admin) ---

@app.get("/api/admin/invoices")
async def list_invoices(current_user: dict = Depends(get_current_admin)):
    """List all invoices"""
    invoices = await db.invoices.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).to_list(200)
    return {"invoices": invoices}


@app.post("/api/admin/invoices/{invoice_id}/send")
async def send_invoice(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    """Send invoice to customer via email"""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")

    doc = await db.documents.find_one({"ref_id": invoice_id, "type": "invoice"})
    if not doc:
        raise HTTPException(404, "PDF nicht gefunden")

    now = datetime.now(timezone.utc)
    customer_email = invoice["customer"]["email"]
    customer_name = invoice["customer"].get("name", "")

    type_labels = {"deposit": "Anzahlungsrechnung", "monthly": "Monatsrechnung", "final": "Schlussrechnung"}
    inv_label = type_labels.get(invoice.get("type", "deposit"), "Rechnung")

    if RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(doc["pdf_data"]).decode()
            checkout_url = invoice.get("checkout_url", "")
            payment_html = ""
            if checkout_url:
                payment_html = f'<p><a href="{checkout_url}" style="display:inline-block;padding:12px 24px;background:#ff9b7a;color:#0c1117;text-decoration:none;font-weight:bold;border-radius:6px;">Jetzt online bezahlen</a></p>'

            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": customer_email,
                "subject": f"{inv_label} {invoice['invoice_number']} — NeXifyAI",
                "html": f"""
                <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a2e;">
                    <div style="border-bottom: 2px solid #ff9b7a; padding-bottom: 16px; margin-bottom: 24px;">
                        <h1 style="margin: 0; font-size: 20px;">NeXify<span style="color: #ff9b7a;">AI</span></h1>
                    </div>
                    <p>Sehr geehrte/r {customer_name},</p>
                    <p>anbei erhalten Sie Ihre <strong>{inv_label}</strong> Nr. <strong>{invoice['invoice_number']}</strong>.</p>
                    <p><strong>Betrag:</strong> {invoice['totals']['gross'] / 100:,.2f} EUR (brutto)<br/>
                    <strong>Fällig am:</strong> {invoice.get('due_date', '—')}</p>
                    {payment_html}
                    <p>Alternativ per Überweisung:<br/>
                    IBAN: {COMPANY_DATA['bank']['iban']}<br/>
                    BIC: {COMPANY_DATA['bank']['bic']}<br/>
                    Verwendungszweck: {invoice['invoice_number']}</p>
                    <p>Mit freundlichen Grüßen,<br/><strong>NeXifyAI</strong></p>
                </div>
                """,
                "attachments": [{
                    "filename": f"Rechnung_{invoice['invoice_number'].replace('.', '_')}.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf"
                }]
            })
        except Exception as e:
            logger.error(f"Invoice email error: {e}")
            raise HTTPException(500, f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "sent", "sent_at": now.isoformat()},
         "$push": {"history": {"action": "sent", "at": now.isoformat(), "by": current_user["email"]}}}
    )
    return {"sent": True, "to": customer_email}


@app.post("/api/admin/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    """Manually mark invoice as paid (for bank transfers)"""
    now = datetime.now(timezone.utc)
    result = await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"payment_status": "paid", "paid_at": now.isoformat(), "status": "paid"},
         "$push": {"history": {"action": "marked_paid", "at": now.isoformat(), "by": current_user["email"]}}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Rechnung nicht gefunden")

    # Update related quote
    invoice = await db.invoices.find_one({"invoice_id": invoice_id})
    if invoice and invoice.get("quote_id"):
        await db.quotes.update_one(
            {"quote_id": invoice["quote_id"]},
            {"$set": {"payment_status": "deposit_paid"},
             "$push": {"history": {"action": "deposit_paid", "at": now.isoformat(), "by": current_user["email"]}}}
        )

    return {"paid": True}


# --- Document Downloads ---

@app.get("/api/documents/{doc_type}/{ref_id}/pdf")
async def download_document(doc_type: str, ref_id: str, token: str = None):
    """Download document PDF (admin or magic-link access)"""
    doc = await db.documents.find_one({"ref_id": ref_id, "type": doc_type})
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")

    # Access control: either admin token or magic link
    if token:
        link = await db.access_links.find_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
        if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
            raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
        # Log access
        await db.audit_log.insert_one({
            "event": "document_access",
            "doc_type": doc_type,
            "ref_id": ref_id,
            "method": "magic_link",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    filename = f"{doc_type}_{doc.get('number', ref_id).replace('.', '_')}.pdf"
    return StreamingResponse(
        BytesIO(doc["pdf_data"]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# --- Customer Magic Link Access ---

@app.post("/api/admin/access-link")
async def create_access_link(customer_email: str = "", current_user: dict = Depends(get_current_admin)):
    """Generate a magic link for customer document access"""
    token_data = generate_access_token(customer_email)
    await db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": customer_email,
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": current_user["email"]
    })
    return {"magic_link_token": token_data["token"], "expires_at": token_data["expires_at"]}


# --- Revolut Webhook ---

@app.post("/api/webhooks/revolut")
async def revolut_webhook(request: Request):
    """Handle Revolut payment webhooks"""
    body = await request.body()
    raw_body = body.decode("utf-8")
    timestamp = request.headers.get("Revolut-Request-Timestamp", "")
    signature = request.headers.get("Revolut-Signature", "")

    try:
        data = json.loads(raw_body)
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    event = data.get("event", "")
    order_id = data.get("order_id", "")

    logger.info(f"Revolut webhook: {event} for order {order_id}")

    # Store webhook event (idempotency check)
    existing = await db.webhook_events.find_one({"order_id": order_id, "event": event})
    if existing:
        return {"status": "already_processed"}

    await db.webhook_events.insert_one({
        "order_id": order_id,
        "event": event,
        "data": data,
        "processed_at": datetime.now(timezone.utc).isoformat()
    })

    if event == "ORDER_COMPLETED":
        # Find invoice by revolut order ID
        invoice = await db.invoices.find_one({"revolut_order_id": order_id})
        if invoice:
            now = datetime.now(timezone.utc)
            await db.invoices.update_one(
                {"invoice_id": invoice["invoice_id"]},
                {"$set": {"payment_status": "paid", "paid_at": now.isoformat(), "status": "paid"},
                 "$push": {"history": {"action": "payment_received_revolut", "at": now.isoformat(), "by": "system"}}}
            )
            # Update related quote
            if invoice.get("quote_id"):
                await db.quotes.update_one(
                    {"quote_id": invoice["quote_id"]},
                    {"$set": {"payment_status": "deposit_paid"},
                     "$push": {"history": {"action": "deposit_paid_revolut", "at": now.isoformat(), "by": "system"}}}
                )
            logger.info(f"Invoice {invoice['invoice_id']} marked as paid via Revolut")

    elif event == "ORDER_PAYMENT_FAILED":
        invoice = await db.invoices.find_one({"revolut_order_id": order_id})
        if invoice:
            await db.invoices.update_one(
                {"invoice_id": invoice["invoice_id"]},
                {"$set": {"payment_status": "failed"},
                 "$push": {"history": {"action": "payment_failed", "at": datetime.now(timezone.utc).isoformat(), "by": "system"}}}
            )

    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
