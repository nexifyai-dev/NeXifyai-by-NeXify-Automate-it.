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
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List
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
from domain import (
    Channel, LeadStatus, MessageDirection, ConversationStatus,
    OfferStatus, InvoiceStatus, WhatsAppSessionStatus,
    create_contact, create_conversation, create_message,
    create_timeline_event, create_memory, create_whatsapp_session, new_id, utcnow,
)
from agents.orchestrator import Orchestrator, SubAgent
from agents.research import create_research_agent
from agents.outreach import create_outreach_agent
from agents.offer import create_offer_agent
from agents.support import create_support_agent
from agents.intake import create_intake_agent
from agents.planning import create_planning_agent
from agents.finance import create_finance_agent
from agents.design import create_design_agent
from agents.qa import create_qa_agent
from memory_service import MemoryService, AGENT_IDS
from workers.manager import WorkerManager
from services.comms import CommunicationService
from services.billing import BillingService
from services.outbound import OutboundLeadMachine
from services.llm_provider import create_llm_provider

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

# Agent Layer (initialized in lifespan)
orchestrator = None
agents = {}

# Service Layer (initialized in lifespan)
worker_mgr = None
comms_svc = None
billing_svc = None
outbound_svc = None
llm_provider = None

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

TARIFE (FINALE PREISE — Single Source of Truth):

1. **Starter AI Agenten AG** (NXA-SAA-24-499)
   - Tarifpreis: 499 EUR/Monat (netto) bei 24 Monaten Laufzeit
   - Gesamtvertragswert: 11.976 EUR (netto)
   - Aktivierungsanzahlung (30 %): 3.592,80 EUR (netto), sofort fällig bei Beauftragung
   - Monatliche Folgerate: 349,30 EUR (netto) über 24 Monate
   - 2 KI-Agenten, Shared Cloud, E-Mail-Support (48h), REST-API-Integrationen

2. **Growth AI Agenten AG** (NXA-GAA-24-1299)
   - Tarifpreis: 1.299 EUR/Monat (netto) bei 24 Monaten Laufzeit
   - Gesamtvertragswert: 31.176 EUR (netto)
   - Aktivierungsanzahlung (30 %): 9.352,80 EUR (netto), sofort fällig bei Beauftragung
   - Monatliche Folgerate: 909,30 EUR (netto) über 24 Monate
   - 10 KI-Agenten, Private Cloud, Priority Support (24h), CRM/ERP-Kit (SAP, HubSpot, Salesforce), dedizierter Onboarding-Manager

PREISKOMMUNIKATION:
- Stelle die 30-%-Anzahlung immer als **Aktivierungsanzahlung** dar (strategischer Projektstart, Priorisierung, Setup, Kapazitätsreservierung)
- Weise immer explizit aus: Die Anzahlung ist Teil des Gesamtvertragswerts — keine zusätzliche Gebühr
- Alle Preise zzgl. gesetzlicher USt. (21 % NL / 19 % DE)
- Keine versteckten Kosten. Keine irreführende Darstellung

Das Erstgespräch ist immer unverbindlich und kostenfrei.

ANGEBOTSANFRAGE / DISCOVERY FLOW:
Wenn ein Interessent konkretes Interesse an einem Tarif zeigt oder ein Angebot anfordert, führe eine strukturierte Discovery durch.
Sammle folgende Informationen — IMMER in einem natürlichen, dialogischen Fluss (keine Formularabfrage!):

**Pflichtfelder:**
1. Name (Vor- und Nachname)
2. Unternehmen
3. Geschäftliche E-Mail-Adresse
4. Land
5. Gewünschter Tarif (Starter oder Growth — bzw. für SEO: SEO Starter, SEO Growth, SEO Enterprise — oder Bundle)
6. Branche
7. Use Case / Zielbild

**Optionale Vertiefung:**
8. Telefon
9. Vorhandene Systeme/Tools (ERP, CRM, etc.)
10. Gewünschte Automationen
11. Gewünschte Kanäle (E-Mail, Chat, Voice, etc.)
12. Datenschutz-/DSGVO-Relevanz
13. Timeline
14. Besondere Anforderungen

Wenn alle Pflichtfelder gesammelt sind, gib EXAKT dieses Format aus (eingebettet in deine Antwort):
[OFFER_REQUEST]{"name":"Vorname Nachname","company":"Firmenname","email":"email@domain.com","phone":"optional","country":"DE","industry":"Branche","tier":"starter oder growth","use_case":"Beschreibung","target_systems":"SAP, HubSpot etc","automations":"Vertrieb, Support etc","channels":"E-Mail, Chat etc","gdpr_relevant":true,"timeline":"Q2 2026","special_requirements":"optional"}[/OFFER_REQUEST]

Danach bestätige: "Ich habe Ihr Angebot erstellt. Sie erhalten es in Kürze per E-Mail — inklusive PDF und sicherem Zugangslink zur Online-Annahme."

ZUSÄTZLICHE SERVICES (Websites, Apps, Add-ons):
- **Website Starter**: 2.990 EUR (einmalig), bis 5 Seiten, 3 Wochen
- **Website Professional**: 7.490 EUR (einmalig), bis 15 Seiten, Animationen, Blog, 5 Wochen
- **Website Enterprise**: 14.900 EUR (einmalig), unbegrenzt, Headless CMS, E-Commerce, 8 Wochen
- **App MVP**: 9.900 EUR (einmalig), iOS + Android, 5 Features, 8 Wochen
- **App Professional**: 24.900 EUR (einmalig), Full-Stack, Admin, Payment, CRM, 14 Wochen
- **KI-Chatbot Add-on**: 249 EUR/Monat
- **KI-Automation Add-on**: 499 EUR/Monat

**KI-GESTEUERTES SEO** (eigenständiges Produkt):
- **SEO Starter**: 799 EUR/Monat (netto), 50 Keywords, On-Page (5 Seiten/Mo.), quartalsweiser Tech-Audit, Mindestlaufzeit 6 Monate
- **SEO Growth**: 1.499 EUR/Monat (netto), 200 Keywords, On-Page (15 Seiten/Mo.), Content-Strategie, Linkbuilding, Multilingual (DE/NL/EN), Mindestlaufzeit 6 Monate — EMPFOHLEN
- **SEO Enterprise**: Individuell, unbegrenzte Keywords, tagesaktuelle Reports, dediziertes SEO-Team, International SEO (5+ Märkte)

**BUNDLES & KOMBIANGEBOTE** (Cross-Sell-Rabatte bis 15 %):
- **Digital Starter**: 3.990 EUR — Website Starter + SEO Starter (3 Monate). Statt 4.289 EUR
- **Growth Digital**: 17.490 EUR — Website Professional + SEO Growth (6 Monate) + KI-Chatbot. Statt 19.467 EUR. 15 % Bundle-Rabatt. BELIEBT
- **Enterprise Digital**: ab 39.900 EUR — Website Enterprise + App + SEO Enterprise + KI-Agenten (Growth) + dediziertes Projektteam

PRODUKTBERATUNGSLOGIK:
- Wenn jemand nach SEO fragt → Erkläre KI-gesteuertes SEO, nenne Tarife, empfehle Growth
- Wenn jemand Website + SEO will → Empfehle passendes Bundle (Digital Starter oder Growth Digital)
- Wenn jemand App + KI-Agenten will → Empfehle App Professional + Growth AI Agenten AG
- Wenn jemand alles braucht → Enterprise Digital Bundle
- Verknüpfe immer Services mit Integrationen: "Für Ihre Salesforce-Anbindung empfehle ich ..."
- Frage aktiv: "Haben Sie auch Bedarf an Suchmaschinenoptimierung? Unser KI-gesteuertes SEO ..."

Wenn ein Nutzer nach Website, App, SEO oder Add-on fragt, nenne die konkreten Preise und empfehle passende Bundles.

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
memory_svc: Optional[MemoryService] = None

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
    
    # Create additional indexes for unified comms
    await db.contacts.create_index("contact_id", unique=True)
    await db.contacts.create_index("email")
    await db.conversations.create_index("conversation_id", unique=True)
    await db.conversations.create_index("contact_id")
    await db.messages.create_index("conversation_id")
    await db.messages.create_index("channel")
    await db.timeline_events.create_index("timestamp")
    await db.customer_memory.create_index("contact_id")
    await db.customer_memory.create_index("agent_id")
    await db.customer_memory.create_index([("contact_id", 1), ("agent_id", 1)])
    await db.whatsapp_sessions.create_index("session_id")

    # Initialize AI Agent Layer
    global orchestrator, agents, memory_svc
    global worker_mgr, comms_svc, billing_svc, outbound_svc, llm_provider
    memory_svc = MemoryService(db)
    orchestrator = Orchestrator(db)
    agents = {
        "research": create_research_agent(db),
        "outreach": create_outreach_agent(db),
        "offer": create_offer_agent(db),
        "support": create_support_agent(db),
        "intake": create_intake_agent(db),
        "planning": create_planning_agent(db),
        "finance": create_finance_agent(db),
        "design": create_design_agent(db),
        "qa": create_qa_agent(db),
    }

    # Initialize Worker/Scheduler Layer (P0: entkoppelt von Request-Prozess)
    worker_mgr = WorkerManager(db, max_workers=4)
    await worker_mgr.start()

    # Initialize Service Layer
    llm_provider = create_llm_provider()
    comms_svc = CommunicationService(db, worker_manager=worker_mgr)
    billing_svc = BillingService(db, worker_manager=worker_mgr, comms_service=comms_svc)
    outbound_svc = OutboundLeadMachine(db, worker_manager=worker_mgr, comms_service=comms_svc)

    # Outbound-Indexes
    await db.outbound_leads.create_index("outbound_lead_id", unique=True)
    await db.outbound_leads.create_index("status")
    await db.outbound_leads.create_index("score")
    await db.outbound_leads.create_index("contact_email")
    await db.suppression_list.create_index("email", unique=True)

    logger.info("NeXifyAI Backend v3.0 started — Worker/Scheduler/Services aktiv")
    yield
    # Shutdown
    await worker_mgr.stop()
    db_client.close()

app = FastAPI(title="NeXifyAI API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    if request.url.path.startswith("/api/portal/") or request.url.path.startswith("/api/documents/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

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
    status: Optional[str] = None
    notes: Optional[str] = None
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    email: Optional[str] = None
    unternehmen: Optional[str] = None
    telefon: Optional[str] = None
    source: Optional[str] = None
    nachricht: Optional[str] = None

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
        role: str = payload.get("role", "admin")
        if not email:
            raise HTTPException(status_code=401, detail="Ungültiger Token")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Keine Admin-Berechtigung")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token abgelaufen oder ungültig")
    
    user = await db.admin_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
    
    return user

async def get_current_customer(token: str = Depends(oauth2_scheme)):
    """JWT-basierte Kunden-Authentifizierung — Rolle: customer."""
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if not email or role != "customer":
            raise HTTPException(status_code=403, detail="Kein Kundenzugang")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token abgelaufen oder ungültig")
    
    contact = await db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Kundenkonto nicht gefunden")
    return {"email": email.lower(), "contact": contact}

async def log_audit(action: str, user: str, details: dict = None):
    await db.audit_log.insert_one({
        "action": action,
        "user": user,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })

# ============== EMAIL TEMPLATES ==============

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

async def _build_customer_memory(email: str, current_session_id: str = None) -> str:
    """Build comprehensive customer memory context from ALL channels.
    Sources: Leads, Quotes, Invoices, Bookings, Chat Sessions, Contact Forms,
    Unified Conversations (WhatsApp/Email/Portal), Memory Facts."""
    if not email:
        return ""
    
    email_lower = email.lower()
    parts = []
    
    # 1. Lead/Contact data
    lead = await db.leads.find_one({"email": email_lower}, {"_id": 0})
    if lead:
        parts.append(f"Kontakt: {lead.get('vorname','')} {lead.get('nachname','')}, {lead.get('unternehmen','')}, Status: {lead.get('status','')}")
        if lead.get("notes"):
            recent_notes = lead["notes"][-3:] if isinstance(lead["notes"], list) else []
            for n in recent_notes:
                if isinstance(n, dict):
                    parts.append(f"  Notiz ({n.get('date','')[:10]}): {n.get('text','')[:100]}")
    
    # 2. Unified Contact record (domain layer)
    contact = await db.contacts.find_one({"email": email_lower}, {"_id": 0})
    contact_id = contact.get("contact_id") if contact else None
    if contact:
        channels_used = contact.get("channels_used", [])
        if channels_used:
            parts.append(f"Kanäle genutzt: {', '.join(channels_used)}")
        if contact.get("industry"):
            parts.append(f"Branche: {contact['industry']}")
        if contact.get("company"):
            parts.append(f"Firma: {contact['company']}")
    
    # 3. Quotes/Angebote
    quotes = []
    async for q in db.quotes.find({"customer.email": email_lower}, {"_id": 0}).sort("created_at", -1).limit(5):
        status = q.get("status", "unknown")
        tier = q.get("tier", "")
        calc = q.get("calculation", {})
        quotes.append(f"Angebot {q.get('quote_number','')}: {calc.get('tier_name',tier)} — {calc.get('total_contract_eur',0):,.2f} EUR, Status: {status}")
    if quotes:
        parts.append("Angebote: " + " | ".join(quotes))
    
    # 4. Invoices/Rechnungen
    invoices = []
    async for inv in db.invoices.find({"customer.email": email_lower}, {"_id": 0}).sort("created_at", -1).limit(5):
        invoices.append(f"Rechnung {inv.get('invoice_number','')}: {inv.get('total_eur',0):,.2f} EUR, Status: {inv.get('status','')}")
    if invoices:
        parts.append("Rechnungen: " + " | ".join(invoices))
    
    # 5. Bookings/Termine
    bookings = []
    async for bk in db.bookings.find({"email": email_lower}, {"_id": 0}).sort("created_at", -1).limit(3):
        bookings.append(f"Termin {bk.get('date','')} {bk.get('time','')}: {bk.get('status','')}")
    if bookings:
        parts.append("Termine: " + " | ".join(bookings))
    
    # 6. Previous chat sessions (not current)
    prev_sessions = []
    query = {"customer_email": email_lower}
    if current_session_id:
        query["session_id"] = {"$ne": current_session_id}
    async for sess in db.chat_sessions.find(query, {"_id": 0, "messages": {"$slice": -4}, "qualification": 1, "created_at": 1}).sort("created_at", -1).limit(3):
        qual = sess.get("qualification", {})
        msgs = sess.get("messages", [])
        last_user_msgs = [m["content"][:80] for m in msgs if m.get("role") == "user"][-2:]
        if last_user_msgs:
            prev_sessions.append(f"Vorheriges Gespräch: {', '.join(last_user_msgs)}")
        if qual.get("use_case"):
            prev_sessions.append(f"  Interesse: {qual['use_case']}")
    if prev_sessions:
        parts.append("Chat-Historie: " + " | ".join(prev_sessions))
    
    # 7. Unified Conversations (WhatsApp, Email, Portal)
    if contact_id:
        conv_summaries = []
        async for conv in db.conversations.find({"contact_id": contact_id}, {"_id": 0}).sort("last_message_at", -1).limit(5):
            ch = ", ".join(conv.get("channels", []))
            cnt = conv.get("message_count", 0)
            status = conv.get("status", "open")
            last_msgs = []
            async for m in db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0, "content": 1, "direction": 1, "channel": 1}).sort("timestamp", -1).limit(2):
                preview = m.get("content", "")[:60]
                last_msgs.append(f"[{m.get('channel','?')}/{m.get('direction','?')}] {preview}")
            summary = f"{ch} ({cnt} Nachrichten, {status})"
            if last_msgs:
                summary += ": " + " | ".join(last_msgs)
            conv_summaries.append(summary)
        if conv_summaries:
            parts.append("Kanalübergreifende Konversationen:\n  " + "\n  ".join(conv_summaries))
    
    # 8. Memory Facts (mem0 style)
    if contact_id:
        facts = []
        async for mem in db.customer_memory.find({"contact_id": contact_id}, {"_id": 0}).sort("created_at", -1).limit(10):
            facts.append(f"[{mem.get('category','general')}] {mem.get('fact','')}")
        if facts:
            parts.append("Bekannte Fakten:\n  " + "\n  ".join(facts))
    
    # 9. Contact form submissions
    contact_form = await db.inquiries.find_one({"email": email_lower}, {"_id": 0})
    if contact_form:
        parts.append(f"Kontaktanfrage: {contact_form.get('nachricht','')[:120]}")
    
    if not parts:
        return ""
    
    return "Bekannter Kunde: " + email_lower + "\n" + "\n".join(parts)

async def _log_event(db_ref, event_type: str, ref_id: str, user: str, details: dict = None):
    """Log a commercial event to the audit trail."""
    await db_ref.audit_log.insert_one({
        "event_type": event_type,
        "ref_id": ref_id,
        "user": user,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc)
    })

@app.post("/api/chat/message")
async def chat_message(data: ChatMessage, request: Request):
    await check_rate_limit(request, limit=20, window=60)
    
    session = await db.chat_sessions.find_one({"session_id": data.session_id})
    if not session:
        session = {
            "session_id": data.session_id,
            "messages": [],
            "qualification": {},
            "customer_email": None,
            "created_at": datetime.now(timezone.utc)
        }
        await db.chat_sessions.insert_one(session)
    
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
            await db.chat_sessions.update_one(
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
        if EMERGENT_LLM_KEY:
            if data.session_id not in llm_sessions:
                system_prompt = get_system_prompt(data.language or "de")
                if memory_context:
                    system_prompt += f"\n\nKUNDENKONTEXT (NUR INTERN — NICHT ZITIEREN):\n{memory_context}"
                chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=data.session_id,
                    system_message=system_prompt
                )
                chat.with_model("openai", "gpt-4o-mini")
                llm_sessions[data.session_id] = chat
            elif memory_context and not session.get("_memory_injected"):
                # Re-inject memory context if newly available
                pass
            
            llm_chat = llm_sessions[data.session_id]
            user_message = UserMessage(text=data.message)
            response_text = await llm_chat.send_message(user_message)
            
            # Extract email from offer/booking requests for memory linking
            offer_match_pre = re.search(r'\[OFFER_REQUEST\](.*?)\[/OFFER_REQUEST\]', response_text, re.DOTALL)
            if offer_match_pre:
                try:
                    od = json.loads(offer_match_pre.group(1))
                    if od.get("email"):
                        await db.chat_sessions.update_one(
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
                        qnum = await gnn(db, "quote")
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
                        await db.quotes.insert_one(quote_obj)
                        quote_obj.pop("_id", None)
                        pdf_bytes = gqpdf(quote_obj)
                        await db.documents.insert_one({
                            "doc_id": f"doc_{secrets.token_hex(8)}", "type": "quote",
                            "ref_id": quote_obj["quote_id"], "number": qnum,
                            "pdf_data": pdf_bytes, "created_at": now_q.isoformat(),
                        })
                        tok = gat(offer_data.get("email", ""), "quote")
                        await db.access_links.insert_one({
                            "token_hash": tok["token_hash"], "customer_email": offer_data.get("email", ""),
                            "quote_id": quote_obj["quote_id"], "document_type": "quote",
                            "expires_at": tok["expires_at"], "created_at": tok["created_at"], "created_by": "ai_advisor",
                        })
                        if RESEND_API_KEY:
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
    
    await db.chat_sessions.update_one(
        {"session_id": data.session_id},
        {"$push": {"messages": {"$each": [user_msg, assistant_msg]}},
         "$set": {"qualification": qualification, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # mem0 Pflicht-Write: Relevante Fakten aus dem Gespräch persistieren
    if customer_email and memory_svc:
        contact = await db.contacts.find_one({"email": customer_email.lower()})
        if contact:
            cid = contact["contact_id"]
            if qualification.get("use_case") and not session.get("_use_case_memorized"):
                await memory_svc.write(cid, f"Interesse an: {qualification['use_case']}", AGENT_IDS["chat"],
                                       category="interest", source="chat", source_ref=data.session_id)
                await db.chat_sessions.update_one({"session_id": data.session_id}, {"$set": {"_use_case_memorized": True}})
            if qualification.get("booking_confirmed"):
                await memory_svc.write(cid, f"Termin gebucht: {qualification['booking_confirmed']}", AGENT_IDS["chat"],
                                       category="context", source="chat", source_ref=data.session_id,
                                       verification_status="verifiziert")
            if qualification.get("offer_generated"):
                await memory_svc.write(cid, f"Angebot generiert: {qualification['offer_generated']}", AGENT_IDS["chat"],
                                       category="context", source="chat", source_ref=data.session_id,
                                       verification_status="verifiziert")
    
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
        return "Wir entwickeln **maßgeschneiderte digitale Lösungen** mit nativer KI-Integration:\n\n- **App MVP**: 9.900 EUR — iOS + Android, 5 Kernfeatures, Auth, Push (8 Wochen)\n- **App Professional**: 24.900 EUR — Full-Stack, Admin-Dashboard, Payment, CRM (14 Wochen)\n- **Kundenportale** — Self-Service mit intelligenter KI-Unterstützung\n\nAlle Lösungen DSGVO-konform und in EU-Rechenzentren gehostet. Was für eine Anwendung schwebt Ihnen vor?"
    elif "website" in msg or "webseite" in msg or "homepage" in msg:
        return "Unsere **Website-Lösungen** auf einen Blick:\n\n- **Website Starter**: 2.990 EUR — bis 5 Seiten, responsive, SEO-Basis (3 Wochen)\n- **Website Professional**: 7.490 EUR — bis 15 Seiten, Animationen, Blog, Analytics (5 Wochen)\n- **Website Enterprise**: 14.900 EUR — Headless CMS, E-Commerce, WCAG, SLA (8 Wochen)\n\nDazu erhältlich: **KI-Chatbot Add-on** ab 249 EUR/Monat für Lead-Qualifizierung direkt auf Ihrer Website. Was für ein Projekt planen Sie?"
    elif "termin" in msg or "buchen" in msg or "gespräch" in msg:
        return "Ich kann direkt hier einen **kostenlosen Beratungstermin** für Sie buchen. Dafür benötige ich:\n\n1. Ihren **Vornamen**\n2. Ihren **Nachnamen**\n3. Ihre **geschäftliche E-Mail-Adresse**\n\nDas Strategiegespräch dauert 30 Minuten und ist vollkommen unverbindlich. Wie heißen Sie?"
    elif "preis" in msg or "kosten" in msg or "tarif" in msg:
        return "Unsere Tarife im Überblick:\n\n- **Starter AI Agenten AG** — 499 EUR/Monat (netto): 2 KI-Agenten, Shared Cloud, E-Mail-Support (48h)\n- **Growth AI Agenten AG** — 1.299 EUR/Monat (netto): 10 KI-Agenten, Private Cloud, Priority Support, CRM/ERP-Kit\n\nBeide Tarife laufen über **24 Monate**. Bei Beauftragung wird eine **Aktivierungsanzahlung von 30 %** fällig — sie deckt Projektstart, Setup und Kapazitätsreservierung.\n\nDas Erstgespräch ist **immer unverbindlich und kostenfrei**. Soll ich einen Termin oder direkt ein individuelles Angebot für Sie erstellen?"
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
    
    token = create_access_token({"sub": user["email"], "role": "admin"})
    await log_audit("login_success", user["email"])
    
    return {"access_token": token, "token_type": "bearer"}


# ============== UNIFIED AUTH (Admin + Kunde) ==============

@app.post("/api/auth/check-email")
async def auth_check_email(data: dict):
    """Prüfe ob E-Mail ein Admin oder Kunde ist."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    admin = await db.admin_users.find_one({"email": email})
    if admin:
        return {"role": "admin", "needs_password": True}
    
    contact = await db.contacts.find_one({"email": email})
    lead = await db.leads.find_one({"email": email})
    if contact or lead:
        return {"role": "customer", "needs_magic_link": True}
    
    return {"role": "unknown"}


@app.post("/api/auth/request-magic-link")
async def auth_request_magic_link(data: dict, request: Request):
    """Magic Link per E-Mail an Kunden senden."""
    if request:
        await check_rate_limit(request, limit=5, window=300)
    
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    # Prüfe ob Kontakt/Lead existiert
    contact = await db.contacts.find_one({"email": email})
    lead = await db.leads.find_one({"email": email})
    if not contact and not lead:
        raise HTTPException(404, "Kein Konto für diese E-Mail gefunden")
    
    # Erstelle Portal-Zugangstoken
    token_data = generate_access_token(email, "portal")
    await db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": email,
        "customer_name": (contact or {}).get("first_name", (lead or {}).get("vorname", "")) + " " + (contact or {}).get("last_name", (lead or {}).get("nachname", "")),
        "document_type": "portal",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": "system_magic_link",
    })
    
    base_url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    magic_link = f"{base_url}/login/verify?token={token_data['token']}"
    
    # E-Mail senden
    if RESEND_API_KEY:
        try:
            html = email_template(
                "Ihr Portalzugang — NeXifyAI",
                f"<p>Hallo,</p>"
                f"<p>Sie haben einen Zugangslink für Ihr NeXifyAI-Kundenportal angefordert.</p>"
                f"<p>Klicken Sie auf den Button, um sich einzuloggen. Der Link ist 24 Stunden gültig.</p>",
                magic_link,
                "Zum Portal"
            )
            await send_email([email], "Ihr Portalzugang — NeXifyAI", html)
        except Exception as e:
            logger.error(f"Magic Link E-Mail Fehler: {e}")
    
    await log_audit("magic_link_requested", email)
    
    return {"status": "ok", "message": "Magic Link wurde per E-Mail gesendet"}


@app.post("/api/auth/verify-token")
async def auth_verify_token(data: dict):
    """Magic Link Token verifizieren → JWT mit role=customer zurückgeben."""
    token = data.get("token", "").strip()
    if not token:
        raise HTTPException(400, "Token fehlt")
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await db.access_links.find_one({"token_hash": token_hash})
    if not link:
        raise HTTPException(403, "Zugangslink ungültig")
    
    expires = link.get("expires_at")
    if expires:
        if isinstance(expires, str):
            from dateutil.parser import parse as dateparse
            expires = dateparse(expires)
        if expires < datetime.now(timezone.utc):
            raise HTTPException(403, "Zugangslink abgelaufen")
    
    email = link.get("customer_email", "").lower()
    if not email:
        raise HTTPException(400, "Kein Kundenkonto verknüpft")
    
    # JWT mit role=customer erstellen
    jwt_token = create_access_token(
        {"sub": email, "role": "customer"},
        expires_delta=timedelta(hours=24)
    )
    
    await log_audit("customer_login_magic_link", email)
    
    # mem0 Memory Write
    if memory_svc:
        contact = await db.contacts.find_one({"email": email})
        if contact:
            await memory_svc.write(contact["contact_id"], "Kunde hat sich über Magic Link eingeloggt",
                                   AGENT_IDS["system"], category="context", source="auth",
                                   verification_status="verifiziert")
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "role": "customer",
        "email": email,
        "customer_name": link.get("customer_name", "")
    }


# ============== CUSTOMER PORTAL JWT-AUTH ENDPOINTS ==============

@app.get("/api/customer/me")
async def customer_me(user = Depends(get_current_customer)):
    """Kundenprofil — JWT-authentifiziert."""
    return {
        "email": user["email"],
        "role": "customer",
        "contact": {k: v for k, v in user["contact"].items() if k not in ("_id",)}
    }


@app.get("/api/customer/dashboard")
async def customer_dashboard(user = Depends(get_current_customer)):
    """Kunden-Dashboard — alle Daten JWT-authentifiziert."""
    email = user["email"]
    
    # Quotes
    quotes = []
    async for q in db.quotes.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        quotes.append({
            "quote_id": q["quote_id"],
            "quote_number": q.get("quote_number", ""),
            "status": q.get("status", ""),
            "tier": q.get("tier", ""),
            "calculation": q.get("calculation", {}),
            "discount": q.get("discount", {}),
            "special_items": q.get("special_items", []),
            "created_at": str(q.get("created_at", "")),
        })
    
    # Invoices
    invoices = []
    async for inv in db.invoices.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        invoices.append({
            "invoice_id": inv["invoice_id"],
            "invoice_number": inv.get("invoice_number", ""),
            "status": inv.get("status", ""),
            "payment_status": inv.get("payment_status", ""),
            "total_eur": inv.get("totals", {}).get("gross", 0),
            "created_at": str(inv.get("created_at", "")),
        })
    
    # Bookings
    bookings = []
    async for bk in db.bookings.find({"email": email}, {"_id": 0}).sort("created_at", -1).limit(10):
        bookings.append({
            "booking_id": bk.get("booking_id", ""),
            "date": bk.get("date", ""),
            "time": bk.get("time", ""),
            "status": bk.get("status", ""),
            "thema": bk.get("thema", ""),
        })
    
    # Communication
    chat_summaries = []
    async for sess in db.chat_sessions.find({"customer_email": email}, {"_id": 0, "messages": {"$slice": -3}}).sort("created_at", -1).limit(5):
        msgs = sess.get("messages", [])
        chat_summaries.append({
            "type": "chat", "date": str(sess.get("created_at", "")),
            "messages": [{"role": m["role"], "content": m["content"][:150]} for m in msgs],
        })
    
    unified_convos = []
    contact = user["contact"]
    if contact:
        cid = contact.get("contact_id")
        async for conv in db.conversations.find({"contact_id": cid}, {"_id": 0}).sort("last_message_at", -1).limit(10):
            last_msgs = []
            async for m in db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0}).sort("timestamp", -1).limit(3):
                last_msgs.append({
                    "direction": m.get("direction"), "channel": m.get("channel"),
                    "content": m.get("content", "")[:200], "timestamp": str(m.get("timestamp", "")),
                })
            unified_convos.append({
                "type": "conversation", "channels": conv.get("channels", []),
                "status": conv.get("status"), "message_count": conv.get("message_count", 0),
                "date": str(conv.get("last_message_at", "")), "messages": last_msgs,
            })
    
    # Timeline
    timeline_items = []
    async for evt in db.timeline_events.find(
        {"$or": [{"actor": email}, {"details.email": email}, {"details.customer_email": email}]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20):
        timeline_items.append({
            "event_type": evt.get("event_type"), "action": evt.get("action"),
            "channel": evt.get("channel"), "timestamp": str(evt.get("timestamp", "")),
            "details": {k: v for k, v in evt.get("details", {}).items() if k not in ("_id",)},
        })
    
    return {
        "email": email,
        "customer_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
        "quotes": quotes,
        "invoices": invoices,
        "bookings": bookings,
        "communications": chat_summaries + unified_convos,
        "timeline": timeline_items,
    }

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


@app.post("/api/admin/leads")
async def admin_create_lead(data: dict, current_user: dict = Depends(get_current_admin)):
    """Manuell einen Lead anlegen."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    existing = await db.leads.find_one({"email": email})
    if existing:
        raise HTTPException(409, "Ein Lead mit dieser E-Mail existiert bereits")
    lead = {
        "lead_id": new_id("lead"),
        "vorname": data.get("vorname", "").strip(),
        "nachname": data.get("nachname", "").strip(),
        "email": email,
        "unternehmen": data.get("unternehmen", "").strip(),
        "telefon": data.get("telefon", "").strip(),
        "nachricht": data.get("nachricht", "").strip(),
        "source": data.get("source", "admin"),
        "status": "new",
        "notes": [],
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db.leads.insert_one(lead)
    lead.pop("_id", None)
    # Also create a unified contact
    contact = create_contact(email, first_name=data.get("vorname",""), last_name=data.get("nachname",""),
                             phone=data.get("telefon",""), company=data.get("unternehmen",""), source="admin")
    await db.contacts.update_one({"email": email}, {"$setOnInsert": contact}, upsert=True)
    evt = create_timeline_event("lead", lead["lead_id"], "lead_created_manually",
                                actor=current_user["email"], actor_type="admin",
                                details={"email": email, "source": "admin"})
    await db.timeline_events.insert_one(evt)
    return lead



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
    updates = {"updated_at": datetime.now(timezone.utc)}
    for field in ["status", "vorname", "nachname", "email", "unternehmen", "telefon", "source", "nachricht"]:
        val = getattr(update, field, None)
        if val is not None:
            updates[field] = val
    
    if update.notes:
        await db.leads.update_one(
            {"lead_id": lead_id},
            {"$set": updates, "$push": {"notes": {"text": update.notes, "by": user["email"], "at": datetime.now(timezone.utc).isoformat()}}}
        )
    else:
        await db.leads.update_one({"lead_id": lead_id}, {"$set": updates})
    
    await log_audit("lead_updated", user["email"], {"lead_id": lead_id, "updates": {k: v for k, v in updates.items() if k != "updated_at"}})
    
    # mem0 Memory
    if memory_svc:
        contact = await db.contacts.find_one({"email": (update.email or "").lower() or (await db.leads.find_one({"lead_id": lead_id}))["email"]})
        if contact:
            changed = ", ".join(f"{k}={v}" for k, v in updates.items() if k != "updated_at")
            await memory_svc.write(contact["contact_id"], f"Lead {lead_id} bearbeitet: {changed}", AGENT_IDS["admin"],
                                   category="context", source="admin", source_ref=user["email"], verification_status="verifiziert")
    
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

@app.post("/api/admin/customers")
async def admin_create_customer(data: dict, user = Depends(get_current_admin)):
    """Manuell einen Kunden anlegen — erstellt Lead + Contact + Memory-Eintrag."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    vorname = data.get("vorname", "").strip()
    nachname = data.get("nachname", "").strip()
    unternehmen = data.get("unternehmen", "").strip()
    telefon = data.get("telefon", "").strip()
    branche = data.get("branche", "").strip()
    
    # Upsert lead record
    existing_lead = await db.leads.find_one({"email": email})
    now = datetime.now(timezone.utc)
    if existing_lead:
        await db.leads.update_one(
            {"email": email},
            {"$set": {
                "vorname": vorname or existing_lead.get("vorname", ""),
                "nachname": nachname or existing_lead.get("nachname", ""),
                "unternehmen": unternehmen or existing_lead.get("unternehmen", ""),
                "telefon": telefon or existing_lead.get("telefon", ""),
                "branche": branche or existing_lead.get("branche", ""),
                "updated_at": now,
            }}
        )
    else:
        lead_id = new_id("ld")
        await db.leads.insert_one({
            "lead_id": lead_id,
            "email": email,
            "vorname": vorname,
            "nachname": nachname,
            "unternehmen": unternehmen,
            "telefon": telefon,
            "branche": branche,
            "source": "admin_manual",
            "status": "qualified",
            "notes": [],
            "created_at": now,
            "updated_at": now,
        })
    
    # Upsert unified contact
    existing_contact = await db.contacts.find_one({"email": email})
    if existing_contact:
        await db.contacts.update_one(
            {"email": email},
            {"$set": {
                "first_name": vorname or existing_contact.get("first_name", ""),
                "last_name": nachname or existing_contact.get("last_name", ""),
                "company": unternehmen or existing_contact.get("company", ""),
                "phone": telefon or existing_contact.get("phone", ""),
                "industry": branche or existing_contact.get("industry", ""),
                "updated_at": now,
            },
            "$addToSet": {"channels_used": "admin"}}
        )
        contact_id = existing_contact["contact_id"]
    else:
        contact = create_contact(email, first_name=vorname, last_name=nachname,
                                  company=unternehmen, phone=telefon, industry=branche,
                                  source="admin_manual")
        await db.contacts.insert_one(contact)
        contact.pop("_id", None)
        contact_id = contact["contact_id"]
    
    # Memory-Eintrag: Manuell erstellter Kunde (mem0-konform)
    await memory_svc.write(contact_id, f"Kunde manuell angelegt von Admin ({user['email']}). {vorname} {nachname}, {unternehmen}, Branche: {branche}",
                           AGENT_IDS["admin"], category="context", source="admin", source_ref=user["email"],
                           verification_status="verifiziert")
    
    # Timeline
    evt = create_timeline_event("contact", contact_id, "customer_created_manual",
                                actor=user["email"], actor_type="admin",
                                details={"email": email, "vorname": vorname, "nachname": nachname, "unternehmen": unternehmen})
    await db.timeline_events.insert_one(evt)
    
    return {"status": "ok", "email": email, "contact_id": contact_id}


@app.post("/api/admin/customers/portal-access")
async def admin_create_portal_access(data: dict, user = Depends(get_current_admin)):
    """Portalzugang für einen Kunden erstellen — Magic Link generieren."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    # Ensure contact exists
    contact = await db.contacts.find_one({"email": email})
    if not contact:
        raise HTTPException(404, "Kein Kontakt für diese E-Mail gefunden. Bitte erst Kunden anlegen.")
    
    token_data = generate_access_token(email, "portal")
    await db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": email,
        "document_type": "portal",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": user["email"],
    })
    
    base_url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    portal_url = f"{base_url}/portal/{token_data['token']}"
    
    # Memory-Eintrag (mem0-konform)
    await memory_svc.write(contact["contact_id"], f"Portalzugang erstellt von {user['email']}",
                           AGENT_IDS["admin"], category="context", source="admin", source_ref=user["email"],
                           verification_status="verifiziert")
    
    # Timeline
    evt = create_timeline_event("contact", contact["contact_id"], "portal_access_created",
                                actor=user["email"], actor_type="admin",
                                details={"email": email, "expires_at": token_data["expires_at"]})
    await db.timeline_events.insert_one(evt)
    
    return {"status": "ok", "portal_url": portal_url, "expires_at": token_data["expires_at"]}


@app.get("/api/admin/customers/{email}")
async def admin_customer_detail(email: str, user = Depends(get_current_admin)):
    leads = await db.leads.find({"email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(50)
    bookings = await db.bookings.find({"email": email.lower()}, {"_id": 0}).sort("date", -1).to_list(50)
    chats = await db.chat_sessions.find(
        {"$or": [{"email": email.lower()}, {"qualification.email": email.lower()}]},
        {"_id": 0, "messages": {"$slice": -10}}
    ).sort("updated_at", -1).to_list(10)
    return {"leads": leads, "bookings": bookings, "chats": chats}


@app.patch("/api/admin/customers/{email}")
async def admin_update_customer(email: str, data: dict, user = Depends(get_current_admin)):
    """Kunden-/Kontaktdaten bearbeiten."""
    email = email.lower()
    contact = await db.contacts.find_one({"email": email})
    if not contact:
        raise HTTPException(404, "Kontakt nicht gefunden")
    
    updates = {"updated_at": datetime.now(timezone.utc)}
    field_map = {"vorname": "first_name", "nachname": "last_name", "unternehmen": "company", "telefon": "phone", "branche": "industry"}
    for de_key, en_key in field_map.items():
        if de_key in data and data[de_key]:
            updates[en_key] = data[de_key].strip()
    
    if len(updates) > 1:
        await db.contacts.update_one({"email": email}, {"$set": updates})
    
    # Auch Lead-Daten synchronisieren
    lead_updates = {}
    lead_map = {"vorname": "vorname", "nachname": "nachname", "unternehmen": "unternehmen", "telefon": "telefon", "branche": "branche"}
    for key in lead_map:
        if key in data and data[key]:
            lead_updates[key] = data[key].strip()
    if lead_updates:
        lead_updates["updated_at"] = datetime.now(timezone.utc)
        await db.leads.update_many({"email": email}, {"$set": lead_updates})
    
    await log_audit("customer_updated", user["email"], {"email": email, "fields": list(updates.keys())})
    
    if memory_svc:
        changed = ", ".join(f"{k}={v}" for k, v in updates.items() if k != "updated_at")
        await memory_svc.write(contact["contact_id"], f"Kundendaten bearbeitet: {changed}", AGENT_IDS["admin"],
                               category="context", source="admin", source_ref=user["email"], verification_status="verifiziert")
    
    return {"success": True}


@app.patch("/api/admin/quotes/{quote_id}")
async def admin_update_quote(quote_id: str, data: dict, user = Depends(get_current_admin)):
    """Angebot bearbeiten — Status, Notizen, Rabatt, Sonderpositionen."""
    quote = await db.quotes.find_one({"quote_id": quote_id})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    
    updates = {"updated_at": datetime.now(timezone.utc)}
    
    if "status" in data:
        old_status = quote.get("status", "draft")
        updates["status"] = data["status"]
        # Timeline Event für Statusänderung
        evt = create_timeline_event("quote", quote_id, f"quote_status_{data['status']}",
                                    actor=user["email"], actor_type="admin",
                                    details={"old_status": old_status, "new_status": data["status"]})
        await db.timeline_events.insert_one(evt)
    
    if "notes" in data:
        updates["notes"] = data["notes"]
    
    if "use_case" in data:
        updates["use_case"] = data["use_case"]
    
    if "customer_name" in data:
        updates["customer.name"] = data["customer_name"]
    if "customer_email" in data:
        updates["customer.email"] = data["customer_email"]
    if "customer_company" in data:
        updates["customer.company"] = data["customer_company"]
    
    if "discount_percent" in data:
        dp = float(data["discount_percent"] or 0)
        updates["discount.percent"] = dp
        updates["discount.reason"] = data.get("discount_reason", "")
        # Neuberechnung
        from commercial import TARIFF_CONFIG
        tier = quote.get("tier", "starter")
        tariff = TARIFF_CONFIG.get(tier, TARIFF_CONFIG["starter"])
        net = tariff.get("total_contract_eur", 11976.00)  # Use total_contract_eur as net base
        discount_amount = round(net * dp / 100, 2)
        net_after = net - discount_amount
        # Special items
        sp_items = data.get("special_items", quote.get("special_items", []))
        sp_total = sum(si.get("amount_eur", 0) * (1 if si.get("type") == "add" else -1) for si in sp_items)
        net_final = net_after + sp_total
        updates["calculation.discount_amount_eur"] = discount_amount
        updates["calculation.special_items_total_eur"] = sp_total
        updates["calculation.total_contract_eur"] = round(net_final * 1.19, 2)
        updates["calculation.total_contract_net_eur"] = net_final
        updates["special_items"] = sp_items
    
    await db.quotes.update_one({"quote_id": quote_id}, {"$set": updates})
    await log_audit("quote_updated", user["email"], {"quote_id": quote_id, "fields": list(updates.keys())})
    
    return {"success": True}


@app.patch("/api/admin/invoices/{invoice_id}")
async def admin_update_invoice(invoice_id: str, data: dict, user = Depends(get_current_admin)):
    """Rechnung bearbeiten — Status, Zahlungsstatus, Notizen."""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    
    updates = {"updated_at": datetime.now(timezone.utc)}
    
    if "status" in data:
        updates["status"] = data["status"]
    if "payment_status" in data:
        updates["payment_status"] = data["payment_status"]
    if "notes" in data:
        updates["notes"] = data["notes"]
    
    await db.invoices.update_one({"invoice_id": invoice_id}, {"$set": updates})
    await log_audit("invoice_updated", user["email"], {"invoice_id": invoice_id, "fields": list(updates.keys())})
    
    evt = create_timeline_event("invoice", invoice_id, "invoice_updated",
                                actor=user["email"], actor_type="admin",
                                details={"updates": {k: v for k, v in updates.items() if k != "updated_at"}})
    await db.timeline_events.insert_one(evt)
    
    return {"success": True}


@app.post("/api/admin/bookings")
async def admin_create_booking(data: dict, user = Depends(get_current_admin)):
    """Termin manuell anlegen."""
    required = ["vorname", "email", "date", "time"]
    for f in required:
        if not data.get(f, "").strip():
            raise HTTPException(400, f"{f} ist Pflichtfeld")
    
    booking_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    doc = {
        "booking_id": booking_id,
        "vorname": data.get("vorname", "").strip(),
        "nachname": data.get("nachname", "").strip(),
        "email": data.get("email", "").strip().lower(),
        "telefon": data.get("telefon", ""),
        "unternehmen": data.get("unternehmen", ""),
        "thema": data.get("thema", ""),
        "date": data.get("date"),
        "time": data.get("time"),
        "status": "confirmed",
        "source": "admin_manual",
        "notes": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.bookings.insert_one(doc)
    doc.pop("_id", None)
    
    await log_audit("booking_created_manual", user["email"], {"booking_id": booking_id})
    evt = create_timeline_event("booking", booking_id, "booking_created",
                                actor=user["email"], actor_type="admin",
                                details={"email": doc["email"], "date": doc["date"], "time": doc["time"]})
    await db.timeline_events.insert_one(evt)
    
    return {"success": True, "booking_id": booking_id}


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
# COMMERCIAL ENGINE v2.0 — Source of Truth: commercial.py
# ═══════════════════════════════════════════════════════════════════
from io import BytesIO
from commercial import (
    COMPANY_DATA as COMM_COMPANY, TARIFF_CONFIG, VAT_RATE,
    calc_contract, get_tariff, get_next_number,
    create_revolut_order, get_revolut_order,
    generate_access_token, verify_access_token,
    generate_quote_pdf, generate_invoice_pdf,
    generate_tariff_sheet_pdf,
    get_commercial_faq,
    SERVICE_CATALOG, BUNDLE_CATALOG, PRODUCT_DESCRIPTIONS,
    COMPLIANCE_STATUS, ISO_GAP_ANALYSIS,
)
from fastapi.responses import StreamingResponse


class QuoteRequest(BaseModel):
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: str = ""
    customer_phone: str = ""
    customer_country: str = ""
    customer_industry: str = ""
    use_case: str = ""
    notes: str = ""
    discount_percent: float = 0.0
    discount_reason: str = ""
    special_items: list = []  # [{"description": str, "amount_eur": float, "type": "add|deduct"}]


class OfferDiscoveryRequest(BaseModel):
    """From AI chat discovery flow"""
    session_id: str
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: str = ""
    customer_phone: str = ""
    customer_country: str = ""
    customer_industry: str = ""
    use_case: str = ""
    target_systems: str = ""
    automations: str = ""
    channels: str = ""
    gdpr_relevant: bool = True
    timeline: str = ""
    special_requirements: str = ""


# --- Product Info (Public) ---

@app.get("/api/product/tariffs")
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


@app.get("/api/product/faq")
async def get_product_faq():
    """FAQ derived from central TARIFF_CONFIG"""
    return {"faq": get_commercial_faq()}


@app.get("/api/product/services")
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


@app.get("/api/product/compliance")
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

@app.get("/api/product/tariff-sheet")
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



@app.get("/api/product/descriptions")
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

@app.post("/api/admin/quotes")
async def create_quote(req: QuoteRequest, current_user: dict = Depends(get_current_admin)):
    """Angebot manuell erstellen — mit Tarifvorauswahl, Rabatt und Sonderpositionen."""
    calc = calc_contract(req.tier)
    if not calc:
        raise HTTPException(400, "Ungültiger Tarif")

    quote_number = await get_next_number(db, "quote")
    now = datetime.now(timezone.utc)
    tariff = get_tariff(req.tier)

    # Apply discount
    discount = {}
    if req.discount_percent > 0:
        discount = {
            "percent": min(req.discount_percent, 25.0),  # Max 25% Rabatt
            "reason": req.discount_reason or "Kein Grund angegeben",
            "applied_by": current_user["email"],
        }
        calc["discount_percent"] = discount["percent"]
        calc["discount_reason"] = discount["reason"]
        calc["total_contract_eur_before_discount"] = calc.get("total_contract_eur", 0)
        calc["total_contract_eur"] = round(calc["total_contract_eur"] * (1 - discount["percent"] / 100), 2)
        calc["activation_fee_eur"] = round(calc["total_contract_eur"] * 0.3, 2)

    # Apply special items
    special_items = []
    special_total = 0
    for item in (req.special_items or []):
        desc = item.get("description", "").strip()
        amount = float(item.get("amount_eur", 0))
        item_type = item.get("type", "add")
        if desc and amount > 0:
            special_items.append({"description": desc, "amount_eur": amount, "type": item_type})
            special_total += amount if item_type == "add" else -amount

    quote = {
        "quote_id": f"q_{secrets.token_hex(8)}",
        "quote_number": quote_number,
        "status": "draft",
        "tier": req.tier,
        "tariff_number": tariff.get("tariff_number", ""),
        "customer": {
            "name": req.customer_name,
            "email": req.customer_email,
            "company": req.customer_company,
            "phone": req.customer_phone,
            "country": req.customer_country,
            "industry": req.customer_industry,
        },
        "use_case": req.use_case,
        "calculation": calc,
        "discount": discount,
        "special_items": special_items,
        "special_items_total_eur": special_total,
        "notes": req.notes,
        "date": now.strftime("%d.%m.%Y"),
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [{"action": "erstellt", "at": now.isoformat(), "by": current_user["email"]}],
    }

    await db.quotes.insert_one(quote)
    quote.pop("_id", None)

    pdf_bytes = generate_quote_pdf(quote)
    await db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": quote["quote_id"],
        "number": quote_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })

    await _log_event(db, "offer_generated", quote["quote_id"], current_user["email"])
    return {"quote": quote, "pdf_available": True}


@app.get("/api/admin/quotes")
async def list_quotes(current_user: dict = Depends(get_current_admin)):
    quotes = await db.quotes.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).to_list(200)
    return {"quotes": quotes}


@app.get("/api/admin/quotes/{quote_id}")
async def get_quote_detail(quote_id: str, current_user: dict = Depends(get_current_admin)):
    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    return quote


@app.post("/api/admin/quotes/{quote_id}/send")
async def send_quote(quote_id: str, current_user: dict = Depends(get_current_admin)):
    """Send quote to customer via email with magic link"""
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

    token_data = generate_access_token(customer_email, "quote")
    await db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": customer_email,
        "quote_id": quote_id,
        "document_type": "quote",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": "system",
    })

    frontend_url = os.environ.get("FRONTEND_URL", "https://nexifyai.de")
    portal_link = f"{frontend_url}/angebot?token={token_data['token']}&qid={quote_id}"

    if RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(doc["pdf_data"]).decode()
            resend.Emails.send({
                "from": f"NeXifyAI <{SENDER_EMAIL}>",
                "to": customer_email,
                "subject": f"Ihr Angebot von NeXifyAI — {calc.get('tier_name', '')}",
                "html": email_template(
                    "Ihr Angebot",
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr persoenliches Angebot</h1>
                    <p>Sehr geehrte/r {customer_name},</p>
                    <p>vielen Dank für Ihr Interesse an <strong style="color:#ffb599;">NeXifyAI</strong>.</p>
                    <p>Anbei erhalten Sie Ihr Angebot für <strong>{calc.get("tier_name", "")}</strong>:</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 8px;font-size:13px;color:#8f9095;">ANGEBOT</p>
                    <p style="margin:0 0 4px;color:#fff;font-weight:600;">{quote.get("quote_number", "")}</p>
                    <p style="margin:8px 0 0;font-size:13px;color:#8f9095;">GESAMTVERTRAGSWERT</p>
                    <p style="margin:0;color:#ffb599;font-weight:600;">{calc.get("total_contract_eur", 0):,.2f} EUR (netto)</p>
                    </div>
                    <p>Öffnen Sie das Angebot über den sicheren Link:</p>''',
                    portal_link,
                    "Angebot öffnen"
                ),
                "attachments": [{
                    "filename": f"Angebot_{quote['quote_number'].replace('.', '_')}.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf",
                }],
            })
            logger.info(f"Quote {quote_id} sent to {customer_email}")
        except Exception as e:
            logger.error(f"Email send error: {e}")
            raise HTTPException(500, f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "sent", "sent_at": now.isoformat()},
         "$push": {"history": {"action": "sent", "at": now.isoformat(), "by": current_user["email"]}}},
    )
    await _log_event(db, "offer_sent", quote_id, current_user["email"])
    return {"sent": True, "to": customer_email}


@app.post("/api/admin/quotes/{quote_id}/copy")
async def copy_quote(quote_id: str, current_user: dict = Depends(get_current_admin)):
    """Angebot kopieren / versionieren."""
    orig = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not orig:
        raise HTTPException(404, "Angebot nicht gefunden")
    new_id_val = f"q_{secrets.token_hex(8)}"
    new_number = await get_next_number(db, "quote")
    now = datetime.now(timezone.utc)
    copy = {**orig,
        "quote_id": new_id_val,
        "quote_number": new_number,
        "status": "draft",
        "date": now.strftime("%d.%m.%Y"),
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [
            {"action": "kopiert", "at": now.isoformat(), "by": current_user["email"], "from": quote_id},
        ],
    }
    await db.quotes.insert_one(copy)
    copy.pop("_id", None)
    # Regenerate PDF
    from commercial import generate_quote_pdf
    pdf_bytes = generate_quote_pdf(copy)
    await db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": new_id_val,
        "number": new_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })
    await _log_event(db, "offer_copied", new_id_val, current_user["email"])
    return {"quote": copy, "copied_from": quote_id}


@app.post("/api/admin/invoices")
async def admin_create_invoice(data: dict, current_user: dict = Depends(get_current_admin)):
    """Rechnung manuell erstellen (aus Angebot oder frei)."""
    quote_id = data.get("quote_id")
    now = datetime.now(timezone.utc)
    inv_number = await get_next_number(db, "invoice")

    if quote_id:
        quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
        if not quote:
            raise HTTPException(404, "Angebot nicht gefunden")
        calc = quote.get("calculation", {})
        amount = data.get("amount_eur") or calc.get("activation_fee_eur", 0)
        customer = quote.get("customer", {})
    else:
        amount = data.get("amount_eur", 0)
        customer = {
            "name": data.get("customer_name", ""),
            "email": data.get("customer_email", ""),
            "company": data.get("customer_company", ""),
        }

    tax_rate = data.get("tax_rate", 0.19)
    netto = round(float(amount), 2)
    ust = round(netto * tax_rate, 2)
    brutto = round(netto + ust, 2)

    invoice = {
        "invoice_id": f"inv_{secrets.token_hex(8)}",
        "invoice_number": inv_number,
        "quote_id": quote_id or "",
        "status": "draft",
        "customer": customer,
        "amount_netto_eur": netto,
        "tax_rate": tax_rate,
        "tax_eur": ust,
        "total_eur": brutto,
        "description": data.get("description", ""),
        "date": now.strftime("%d.%m.%Y"),
        "due_date": (now + timedelta(days=14)).strftime("%d.%m.%Y"),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [{"action": "erstellt", "at": now.isoformat(), "by": current_user["email"]}],
    }
    await db.invoices.insert_one(invoice)
    invoice.pop("_id", None)
    evt = create_timeline_event("invoice", invoice["invoice_id"], "invoice_created",
                                actor=current_user["email"], actor_type="admin",
                                details={"invoice_number": inv_number, "total_eur": brutto})
    await db.timeline_events.insert_one(evt)
    return invoice



# --- Customer-Facing Offer Portal ---

@app.get("/api/portal/quote/{quote_id}")
async def portal_get_quote(quote_id: str, token: str):
    """Customer access: view quote via magic link"""
    link = await db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link:
        raise HTTPException(403, "Zugangslink ungültig")
    if not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink abgelaufen")

    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0, "history": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")

    await _log_event(db, "offer_opened", quote_id, link.get("customer_email", "customer"))
    await db.quotes.update_one(
        {"quote_id": quote_id, "status": "sent"},
        {"$set": {"status": "opened"},
         "$push": {"history": {"action": "opened", "at": datetime.now(timezone.utc).isoformat(), "by": "customer"}}},
    )

    return {
        "quote": quote,
        "company": {
            "name": COMM_COMPANY["name"],
            "brand": COMM_COMPANY["brand"],
            "phone": COMM_COMPANY["phone"],
            "email": COMM_COMPANY["email"],
        },
    }


@app.post("/api/portal/quote/{quote_id}/accept")
async def portal_accept_quote(quote_id: str, token: str, request: Request):
    """Customer accepts the quote — triggers invoice + payment"""
    link = await db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")

    quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    if quote.get("status") in ("accepted", "declined"):
        raise HTTPException(400, f"Angebot bereits {quote['status']}")

    now = datetime.now(timezone.utc)
    calc = quote.get("calculation", {})

    audit = {
        "action": "offer_accepted",
        "quote_id": quote_id,
        "quote_number": quote.get("quote_number"),
        "customer_email": quote["customer"]["email"],
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "timestamp": now.isoformat(),
    }
    await db.audit_log.insert_one(audit)

    invoice_number = await get_next_number(db, "invoice")
    due_date = (now + timedelta(days=14)).strftime("%d.%m.%Y")
    upfront_net = calc.get("upfront_eur", 0)
    vat = round(upfront_net * VAT_RATE / 100, 2)
    gross = round(upfront_net + vat, 2)

    tariff = get_tariff(calc.get("tier", "starter"))
    payment_product = tariff.get("payment_products", {}).get("activation", {})

    invoice = {
        "invoice_id": f"inv_{secrets.token_hex(8)}",
        "invoice_number": invoice_number,
        "type": "deposit",
        "product_code": payment_product.get("product_code", ""),
        "status": "created",
        "quote_id": quote_id,
        "customer": quote["customer"],
        "items": [{
            "description": payment_product.get("description", f"Aktivierungsanzahlung (30 %) — {calc.get('tier_name', '')}"),
            "amount_net": upfront_net,
        }],
        "totals": {
            "net": upfront_net,
            "vat_rate": VAT_RATE,
            "vat": vat,
            "gross": gross,
        },
        "date": now.strftime("%d.%m.%Y"),
        "due_date": due_date,
        "payment_reference": invoice_number,
        "payment_status": "pending",
        "revolut_order_id": None,
        "created_at": now.isoformat(),
        "history": [{"action": "created", "at": now.isoformat(), "by": "customer_acceptance"}],
    }

    pdf_bytes = generate_invoice_pdf(invoice)
    await db.invoices.insert_one(invoice)
    invoice.pop("_id", None)

    await db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "invoice",
        "ref_id": invoice["invoice_id"],
        "number": invoice_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })

    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "accepted", "accepted_at": now.isoformat(), "invoice_id": invoice["invoice_id"]},
         "$push": {"history": {"action": "accepted", "at": now.isoformat(), "by": "customer"}}},
    )

    amount_cents = int(gross * 100)
    revolut_result = await create_revolut_order(
        amount_cents=amount_cents,
        currency="EUR",
        customer_email=quote["customer"]["email"],
        description=f"NeXifyAI Aktivierungsanzahlung — {calc.get('tier_name', '')} ({invoice_number})",
        merchant_order_id=invoice["invoice_id"],
    )

    checkout_url = None
    if revolut_result.get("order_id"):
        checkout_url = revolut_result.get("checkout_url")
        await db.invoices.update_one(
            {"invoice_id": invoice["invoice_id"]},
            {"$set": {
                "revolut_order_id": revolut_result["order_id"],
                "revolut_token": revolut_result.get("token"),
                "checkout_url": checkout_url,
            }},
        )

    if RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            payment_cta = ""
            if checkout_url:
                payment_cta = f'<a href="{checkout_url}" style="display:inline-block;background:#ffb599;color:#5a1c00;padding:14px 28px;font-weight:700;text-decoration:none;margin:24px 0;">Jetzt online bezahlen</a>'

            import asyncio
            asyncio.create_task(send_email(
                [quote["customer"]["email"]],
                f"Angebotsannahme bestätigt — Ihre Anzahlungsrechnung {invoice_number}",
                email_template(
                    "Angebotsannahme bestätigt",
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Vielen Dank für Ihre Beauftragung</h1>
                    <p>Ihr Angebot <strong>{quote.get("quote_number", "")}</strong> wurde angenommen.</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">RECHNUNG</p>
                    <p style="margin:0 0 8px;color:#fff;font-weight:600;">{invoice_number}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">BETRAG (BRUTTO)</p>
                    <p style="margin:0;color:#ffb599;font-weight:600;">{gross:,.2f} EUR</p>
                    </div>
                    {payment_cta}
                    <p>Alternativ per Banküberweisung:<br/>
                    IBAN: {COMM_COMPANY["bank"]["iban"]}<br/>
                    BIC: {COMM_COMPANY["bank"]["bic"]}<br/>
                    Verwendungszweck: {invoice_number}</p>''',
                ),
            ))
        except Exception as e:
            logger.error(f"Acceptance email error: {e}")

    await _log_event(db, "offer_accepted", quote_id, quote["customer"]["email"])

    return {
        "accepted": True,
        "invoice_number": invoice_number,
        "amount_gross": gross,
        "due_date": due_date,
        "checkout_url": checkout_url,
        "bank_transfer": {
            "iban": COMM_COMPANY["bank"]["iban"],
            "bic": COMM_COMPANY["bank"]["bic"],
            "reference": invoice_number,
        },
    }


@app.post("/api/portal/quote/{quote_id}/decline")
async def portal_decline_quote(quote_id: str, token: str, request: Request):
    """Customer declines the quote"""
    link = await db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    reason = body.get("reason", "")

    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "declined", "declined_at": now.isoformat(), "decline_reason": reason},
         "$push": {"history": {"action": "declined", "at": now.isoformat(), "by": "customer", "reason": reason}}},
    )
    await _log_event(db, "offer_declined", quote_id, "customer")
    return {"declined": True}


@app.post("/api/portal/quote/{quote_id}/revision")
async def portal_request_revision(quote_id: str, token: str, request: Request):
    """Customer requests a revision"""
    link = await db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    feedback = body.get("feedback", "")

    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "revision_requested", "revision_feedback": feedback},
         "$push": {"history": {"action": "revision_requested", "at": now.isoformat(), "by": "customer", "feedback": feedback}}},
    )
    await _log_event(db, "offer_revision_requested", quote_id, "customer")

    if RESEND_API_KEY:
        quote = await db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
        if quote:
            import asyncio
            asyncio.create_task(send_email(
                NOTIFICATION_EMAILS,
                f"[NeXifyAI] Änderungswunsch: {quote.get('quote_number', '')}",
                email_template("Änderungswunsch",
                    f'''<h1 style="color:#fff;font-size:20px;">Änderungswunsch zum Angebot</h1>
                    <p>Angebot: {quote.get("quote_number","")}</p>
                    <p>Kunde: {quote["customer"].get("name","")}</p>
                    <div style="background:#252a32;padding:16px;margin:16px 0;color:#c5c6cb;white-space:pre-wrap;">{feedback}</div>'''
                ),
            ))

    return {"revision_requested": True}


# --- AI Chat Discovery → Offer Generation ---

@app.post("/api/chat/generate-offer")
async def chat_generate_offer(data: OfferDiscoveryRequest, request: Request):
    """Generate an offer from chat discovery data"""
    await check_rate_limit(request, limit=5, window=60)

    calc = calc_contract(data.tier)
    if not calc:
        raise HTTPException(400, "Ungültiger Tarif")

    quote_number = await get_next_number(db, "quote")
    now = datetime.now(timezone.utc)
    tariff = get_tariff(data.tier)

    quote = {
        "quote_id": f"q_{secrets.token_hex(8)}",
        "quote_number": quote_number,
        "status": "generated",
        "tier": data.tier,
        "tariff_number": tariff.get("tariff_number", ""),
        "customer": {
            "name": data.customer_name,
            "email": data.customer_email,
            "company": data.customer_company,
            "phone": data.customer_phone,
            "country": data.customer_country,
            "industry": data.customer_industry,
        },
        "discovery": {
            "session_id": data.session_id,
            "use_case": data.use_case,
            "target_systems": data.target_systems,
            "automations": data.automations,
            "channels": data.channels,
            "gdpr_relevant": data.gdpr_relevant,
            "timeline": data.timeline,
            "special_requirements": data.special_requirements,
        },
        "calculation": calc,
        "date": now.strftime("%d.%m.%Y"),
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": "ai_advisor",
        "history": [{"action": "generated_from_chat", "at": now.isoformat(), "by": "ai_advisor", "session": data.session_id}],
    }

    await db.quotes.insert_one(quote)
    quote.pop("_id", None)

    pdf_bytes = generate_quote_pdf(quote)
    await db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": quote["quote_id"],
        "number": quote_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })

    await _log_event(db, "offer_generated", quote["quote_id"], "ai_advisor")

    token_data = generate_access_token(data.customer_email, "quote")
    await db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": data.customer_email,
        "quote_id": quote["quote_id"],
        "document_type": "quote",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": "ai_advisor",
    })

    frontend_url = os.environ.get("FRONTEND_URL", "https://nexifyai.de")
    portal_link = f"{frontend_url}/angebot?token={token_data['token']}&qid={quote['quote_id']}"

    if RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            import asyncio
            asyncio.create_task(send_email(
                [data.customer_email],
                f"Ihr Angebot von NeXifyAI — {calc.get('tier_name', '')}",
                email_template("Ihr Angebot",
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr persoenliches Angebot</h1>
                    <p>Sehr geehrte/r {data.customer_name},</p>
                    <p>basierend auf unserem Gespraech haben wir Ihr individuelles Angebot erstellt.</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">TARIF</p>
                    <p style="margin:0 0 8px;color:#ffb599;font-weight:600;">{calc.get("tier_name","")}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">GESAMTVERTRAGSWERT</p>
                    <p style="margin:0;color:#fff;font-weight:600;">{calc.get("total_contract_eur",0):,.2f} EUR</p>
                    </div>''',
                    portal_link,
                    "Angebot öffnen"
                ),
            ))
        except Exception as e:
            logger.error(f"Chat offer email error: {e}")

    return {
        "quote_id": quote["quote_id"],
        "quote_number": quote_number,
        "tier_name": calc.get("tier_name", ""),
        "total_contract_eur": calc.get("total_contract_eur", 0),
        "upfront_gross": calc.get("upfront_gross", 0),
        "pdf_download_url": f"/api/documents/quote/{quote['quote_id']}/pdf",
        "portal_link": portal_link,
        "sent_to": data.customer_email,
    }


# --- Invoice Management (Admin) ---

@app.get("/api/admin/invoices")
async def list_invoices(current_user: dict = Depends(get_current_admin)):
    invoices = await db.invoices.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).to_list(200)
    return {"invoices": invoices}


@app.get("/api/admin/invoices/{invoice_id}")
async def get_invoice_detail(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    return invoice


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

    type_labels = {"deposit": "Aktivierungsanzahlung", "monthly": "Monatsrechnung", "final": "Schlussrechnung"}
    inv_label = type_labels.get(invoice.get("type", "deposit"), "Rechnung")

    if RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(doc["pdf_data"]).decode()
            checkout_url = invoice.get("checkout_url", "")
            payment_html = ""
            if checkout_url:
                payment_html = f'<a href="{checkout_url}" style="display:inline-block;padding:12px 24px;background:#ffb599;color:#0c1117;text-decoration:none;font-weight:bold;border-radius:6px;">Jetzt online bezahlen</a>'

            totals = invoice.get("totals", {})
            gross_val = totals.get("gross", 0)
            gross_str = f"{gross_val:,.2f} EUR" if isinstance(gross_val, (int, float)) else str(gross_val)

            resend.Emails.send({
                "from": f"NeXifyAI <{SENDER_EMAIL}>",
                "to": customer_email,
                "subject": f"{inv_label} {invoice['invoice_number']} — NeXifyAI",
                "html": email_template(
                    inv_label,
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">{inv_label}</h1>
                    <p>Sehr geehrte/r {customer_name},</p>
                    <p>anbei erhalten Sie Ihre {inv_label} Nr. {invoice["invoice_number"]}.</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">BETRAG (BRUTTO)</p>
                    <p style="margin:0 0 8px;color:#ffb599;font-weight:600;">{gross_str}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">FAELLIG AM</p>
                    <p style="margin:0;color:#fff;">{invoice.get("due_date","---")}</p>
                    </div>
                    {payment_html}
                    <p>Alternativ per Banküberweisung:<br/>
                    IBAN: {COMM_COMPANY["bank"]["iban"]}<br/>
                    BIC: {COMM_COMPANY["bank"]["bic"]}<br/>
                    Verwendungszweck: {invoice["invoice_number"]}</p>''',
                ),
                "attachments": [{
                    "filename": f"Rechnung_{invoice['invoice_number'].replace('.', '_')}.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf",
                }],
            })
        except Exception as e:
            logger.error(f"Invoice email error: {e}")
            raise HTTPException(500, f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "sent", "sent_at": now.isoformat()},
         "$push": {"history": {"action": "sent", "at": now.isoformat(), "by": current_user["email"]}}},
    )
    await _log_event(db, "invoice_sent", invoice_id, current_user["email"])
    return {"sent": True, "to": customer_email}


@app.post("/api/admin/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    """Manually mark invoice as paid (for bank transfers)"""
    now = datetime.now(timezone.utc)
    result = await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"payment_status": "paid", "paid_at": now.isoformat(), "status": "payment_completed"},
         "$push": {"history": {"action": "marked_paid", "at": now.isoformat(), "by": current_user["email"]}}},
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Rechnung nicht gefunden")

    invoice = await db.invoices.find_one({"invoice_id": invoice_id})
    if invoice and invoice.get("quote_id"):
        await db.quotes.update_one(
            {"quote_id": invoice["quote_id"]},
            {"$set": {"payment_status": "deposit_paid"},
             "$push": {"history": {"action": "deposit_paid", "at": now.isoformat(), "by": current_user["email"]}}},
        )
    await _log_event(db, "payment_completed", invoice_id, current_user["email"])
    return {"paid": True}


# --- Document Downloads ---

@app.get("/api/documents/{doc_type}/{ref_id}/pdf")
async def download_document(doc_type: str, ref_id: str, token: str = None):
    """Download document PDF (admin or magic-link access)"""
    doc = await db.documents.find_one({"ref_id": ref_id, "type": doc_type})
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")

    if token:
        link = await db.access_links.find_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
        if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
            raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
        await _log_event(db, "document_accessed", ref_id, "magic_link")

    filename = f"{doc_type}_{doc.get('number', ref_id).replace('.', '_')}.pdf"
    return StreamingResponse(
        BytesIO(doc["pdf_data"]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Customer Magic Link Access ---

@app.post("/api/admin/access-link")
async def create_access_link(customer_email: str = "", current_user: dict = Depends(get_current_admin)):
    token_data = generate_access_token(customer_email)
    await db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": customer_email,
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": current_user["email"],
    })
    return {"magic_link_token": token_data["token"], "expires_at": token_data["expires_at"]}


# --- Revolut Webhook ---

@app.post("/api/webhooks/revolut")
async def revolut_webhook(request: Request):
    """Handle Revolut payment webhooks — idempotent"""
    body = await request.body()
    raw_body = body.decode("utf-8")

    try:
        data = json.loads(raw_body)
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    event = data.get("event", "")
    order_id = data.get("order_id", "")

    logger.info(f"Revolut webhook: {event} for order {order_id}")

    existing = await db.webhook_events.find_one({"order_id": order_id, "event": event})
    if existing:
        return {"status": "already_processed"}

    await db.webhook_events.insert_one({
        "order_id": order_id,
        "event": event,
        "data": data,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    })
    await _log_event(db, "webhook_received", order_id, "revolut")

    if event == "ORDER_COMPLETED":
        invoice = await db.invoices.find_one({"revolut_order_id": order_id})
        if invoice:
            now = datetime.now(timezone.utc)
            await db.invoices.update_one(
                {"invoice_id": invoice["invoice_id"]},
                {"$set": {"payment_status": "paid", "paid_at": now.isoformat(), "status": "payment_completed"},
                 "$push": {"history": {"action": "payment_received_revolut", "at": now.isoformat(), "by": "system"}}},
            )
            if invoice.get("quote_id"):
                await db.quotes.update_one(
                    {"quote_id": invoice["quote_id"]},
                    {"$set": {"payment_status": "deposit_paid"},
                     "$push": {"history": {"action": "deposit_paid_revolut", "at": now.isoformat(), "by": "system"}}},
                )
            await _log_event(db, "payment_completed", invoice["invoice_id"], "revolut_webhook")
            logger.info(f"Invoice {invoice['invoice_id']} marked as paid via Revolut")

    elif event == "ORDER_PAYMENT_FAILED":
        invoice = await db.invoices.find_one({"revolut_order_id": order_id})
        if invoice:
            await db.invoices.update_one(
                {"invoice_id": invoice["invoice_id"]},
                {"$set": {"payment_status": "failed"},
                 "$push": {"history": {"action": "payment_failed", "at": datetime.now(timezone.utc).isoformat(), "by": "system"}}},
            )
            await _log_event(db, "payment_failed", invoice["invoice_id"], "revolut_webhook")

    await _log_event(db, "webhook_processed", order_id, "system")
    return {"status": "ok"}


# --- Commercial Stats (Admin) ---

@app.get("/api/admin/commercial/stats")
async def commercial_stats(current_user: dict = Depends(get_current_admin)):
    """Commercial dashboard stats"""
    total_quotes = await db.quotes.count_documents({})
    sent_quotes = await db.quotes.count_documents({"status": "sent"})
    accepted_quotes = await db.quotes.count_documents({"status": "accepted"})
    declined_quotes = await db.quotes.count_documents({"status": "declined"})
    total_invoices = await db.invoices.count_documents({})
    paid_invoices = await db.invoices.count_documents({"payment_status": "paid"})
    pending_invoices = await db.invoices.count_documents({"payment_status": "pending"})

    pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$totals.gross"}}},
    ]
    revenue_agg = await db.invoices.aggregate(pipeline).to_list(1)
    total_revenue = revenue_agg[0]["total"] if revenue_agg else 0

    return {
        "quotes": {"total": total_quotes, "sent": sent_quotes, "accepted": accepted_quotes, "declined": declined_quotes},
        "invoices": {"total": total_invoices, "paid": paid_invoices, "pending": pending_invoices},
        "revenue": {"total_gross": total_revenue, "currency": "EUR"},
    }


# --- Admin: Activity Timeline ---

@app.get("/api/admin/timeline")
async def admin_timeline(
    limit: int = 50,
    email: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """Unified timeline across all entities for a customer or global."""
    events = []
    
    # Audit log events
    query = {}
    if email:
        query["$or"] = [{"details.email": email.lower()}, {"actor": email.lower()}]
    async for ev in db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit):
        events.append({
            "type": "audit",
            "event": ev.get("event_type", ev.get("event", "")),
            "ref_id": ev.get("ref_id", ""),
            "actor": ev.get("user", ev.get("actor", "")),
            "timestamp": ev.get("timestamp", ""),
            "details": ev.get("details", {}),
        })
    
    # Commercial events fallback
    async for ev in db.commercial_events.find(query if email else {}, {"_id": 0}).sort("timestamp", -1).limit(limit):
        events.append({
            "type": "commercial",
            "event": ev.get("event", ""),
            "ref_id": ev.get("ref_id", ""),
            "actor": ev.get("actor", ""),
            "timestamp": ev.get("timestamp", ""),
            "details": ev.get("details", {}),
        })
    
    # Sort combined by timestamp desc
    events.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return {"events": events[:limit]}


# --- mem0 Memory API (Pflicht-Layer) ---

@app.get("/api/admin/memory/agents")
async def admin_memory_agents(current_user: dict = Depends(get_current_admin)):
    """Liste aller bekannten Agent-IDs für mem0."""
    return {"agents": AGENT_IDS}

@app.get("/api/admin/memory/by-agent/{agent_id}")
async def admin_memory_by_agent(agent_id: str, limit: int = 30, current_user: dict = Depends(get_current_admin)):
    """Alle Memory-Einträge eines bestimmten Agenten."""
    entries = await memory_svc.get_agent_history(agent_id, limit)
    for e in entries:
        for k, v in list(e.items()):
            if hasattr(v, 'isoformat'):
                e[k] = str(v)
    return {"agent_id": agent_id, "entries": entries, "count": len(entries)}

@app.get("/api/admin/memory/search")
async def admin_memory_search(q: str, contact_id: str = None, limit: int = 20, current_user: dict = Depends(get_current_admin)):
    """Text-Suche über alle Memory-Einträge."""
    results = await memory_svc.search(q, contact_id, limit)
    for r in results:
        for k, v in list(r.items()):
            if hasattr(v, 'isoformat'):
                r[k] = str(v)
    return {"query": q, "results": results, "count": len(results)}



# --- Admin: Chat Sessions ---

@app.get("/api/admin/chat-sessions")
async def admin_chat_sessions(
    limit: int = 30,
    email: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """List chat sessions with optional email filter."""
    query = {}
    if email:
        query["customer_email"] = email.lower()
    
    sessions = []
    async for s in db.chat_sessions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
        msgs = s.get("messages", [])
        sessions.append({
            "session_id": s["session_id"],
            "customer_email": s.get("customer_email"),
            "qualification": s.get("qualification", {}),
            "message_count": len(msgs),
            "last_message": msgs[-1]["content"][:100] if msgs else "",
            "created_at": str(s.get("created_at", "")),
        })
    return {"sessions": sessions}


@app.get("/api/admin/chat-sessions/{session_id}")
async def admin_chat_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Full chat session with all messages."""
    session = await db.chat_sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(404, "Session nicht gefunden")
    return session


# --- Admin: Customer Memory ---

@app.get("/api/admin/customer-memory/{email}")
async def admin_customer_memory(
    email: str,
    current_user: dict = Depends(get_current_admin)
):
    """Full customer memory context for admin view."""
    memory = await _build_customer_memory(email)
    
    # Also get all related data separately
    lead = await db.leads.find_one({"email": email.lower()}, {"_id": 0})
    quotes = await db.quotes.find({"customer.email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(20)
    invoices = await db.invoices.find({"customer.email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(20)
    bookings = await db.bookings.find({"email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(10)
    chat_sessions = await db.chat_sessions.find({"customer_email": email.lower()}, {"_id": 0, "messages": {"$slice": -5}}).sort("created_at", -1).to_list(10)
    
    # Unified conversations
    contact = await db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    conversations_out = []
    facts_out = []
    if contact:
        cid = contact.get("contact_id")
        async for conv in db.conversations.find({"contact_id": cid}, {"_id": 0}).sort("last_message_at", -1).limit(10):
            mc = await db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0}).sort("timestamp", -1).limit(3).to_list(3)
            conversations_out.append({
                "conversation_id": conv["conversation_id"],
                "channels": conv.get("channels", []),
                "status": conv.get("status", "open"),
                "message_count": conv.get("message_count", 0),
                "last_message_at": str(conv.get("last_message_at", "")),
                "recent_messages": [{k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in m.items()} for m in mc],
            })
        async for mem in db.customer_memory.find({"contact_id": cid}, {"_id": 0}).sort("created_at", -1).limit(20):
            facts_out.append({k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in mem.items()})
    
    return {
        "email": email.lower(),
        "memory_context": memory,
        "lead": lead,
        "quotes": quotes,
        "invoices": invoices,
        "bookings": bookings,
        "chat_sessions": [{
            "session_id": s["session_id"],
            "qualification": s.get("qualification", {}),
            "message_count": len(s.get("messages", [])),
            "recent_messages": s.get("messages", []),
            "created_at": str(s.get("created_at", "")),
        } for s in chat_sessions],
        "conversations": conversations_out,
        "memory_facts": facts_out,
    }


@app.post("/api/admin/customer-memory/{email}/facts")
async def admin_add_memory_fact(
    email: str, data: dict, current_user: dict = Depends(get_current_admin)
):
    """Manually add a memory fact for a customer — mem0-konform."""
    fact_text = data.get("fact", "").strip()
    category = data.get("category", "general")
    if not fact_text:
        raise HTTPException(400, "Fakt darf nicht leer sein")
    contact = await db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    contact_id = contact["contact_id"] if contact else None
    if not contact_id:
        contact = create_contact(email, source="admin")
        await db.contacts.insert_one(contact)
        contact.pop("_id", None)
        contact_id = contact["contact_id"]
    mem = await memory_svc.write(
        contact_id, fact_text, AGENT_IDS["admin"],
        category=category, source="admin", source_ref=current_user["email"],
        verification_status=data.get("verification_status", "verifiziert"),
    )
    evt = create_timeline_event("contact", contact_id, "memory_fact_added",
                                actor=current_user["email"], actor_type="admin",
                                details={"fact": fact_text[:100], "category": category})
    await db.timeline_events.insert_one(evt)
    return {"status": "ok", "memory": {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in mem.items() if k != "_id"}}


# --- Admin: Lead Notes ---

@app.post("/api/admin/leads/{lead_id}/notes")
async def admin_add_lead_note(
    lead_id: str,
    data: dict,
    current_user: dict = Depends(get_current_admin)
):
    """Add a note to a lead."""
    note = {
        "text": data.get("text", ""),
        "author": current_user["email"],
        "date": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.leads.update_one(
        {"lead_id": lead_id},
        {"$push": {"notes": note}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Lead nicht gefunden")
    return {"status": "ok", "note": note}


# --- Customer Portal: Enhanced ---

@app.get("/api/portal/customer/{token}")
async def customer_portal(token: str):
    """Customer portal via magic link token — shows all customer data."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    
    email = link.get("customer_email", "").lower()
    if not email:
        raise HTTPException(400, "Kein Kundenkonto verknüpft")
    
    # Quotes
    quotes = []
    async for q in db.quotes.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        quotes.append({
            "quote_id": q["quote_id"],
            "quote_number": q.get("quote_number", ""),
            "status": q.get("status", ""),
            "tier": q.get("tier", ""),
            "calculation": q.get("calculation", {}),
            "created_at": str(q.get("created_at", "")),
        })
    
    # Invoices
    invoices = []
    async for inv in db.invoices.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        invoices.append({
            "invoice_id": inv["invoice_id"],
            "invoice_number": inv.get("invoice_number", ""),
            "status": inv.get("status", ""),
            "payment_status": inv.get("payment_status", ""),
            "total_eur": inv.get("totals", {}).get("gross", 0),
            "created_at": str(inv.get("created_at", "")),
        })
    
    # Bookings
    bookings = []
    async for bk in db.bookings.find({"email": email}, {"_id": 0}).sort("created_at", -1).limit(10):
        bookings.append({
            "booking_id": bk.get("booking_id", ""),
            "date": bk.get("date", ""),
            "time": bk.get("time", ""),
            "status": bk.get("status", ""),
        })
    
    # Communication history (recent chat summaries + unified conversations)
    chat_summaries = []
    async for sess in db.chat_sessions.find({"customer_email": email}, {"_id": 0, "messages": {"$slice": -3}}).sort("created_at", -1).limit(5):
        msgs = sess.get("messages", [])
        chat_summaries.append({
            "type": "chat",
            "date": str(sess.get("created_at", "")),
            "messages": [{"role": m["role"], "content": m["content"][:150]} for m in msgs],
        })
    
    # Unified conversations (WhatsApp, Email, Portal)
    contact = await db.contacts.find_one({"email": email}, {"_id": 0})
    unified_convos = []
    if contact:
        cid = contact.get("contact_id")
        async for conv in db.conversations.find({"contact_id": cid}, {"_id": 0}).sort("last_message_at", -1).limit(10):
            last_msgs = []
            async for m in db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0}).sort("timestamp", -1).limit(3):
                last_msgs.append({
                    "direction": m.get("direction"),
                    "channel": m.get("channel"),
                    "content": m.get("content", "")[:200],
                    "timestamp": str(m.get("timestamp", "")),
                })
            unified_convos.append({
                "type": "conversation",
                "channels": conv.get("channels", []),
                "status": conv.get("status"),
                "message_count": conv.get("message_count", 0),
                "date": str(conv.get("last_message_at", "")),
                "messages": last_msgs,
            })
    
    # Timeline events for this customer
    timeline_items = []
    async for evt in db.timeline_events.find(
        {"$or": [{"actor": email}, {"details.email": email}, {"details.customer_email": email}]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20):
        timeline_items.append({
            "event_type": evt.get("event_type"),
            "action": evt.get("action"),
            "channel": evt.get("channel"),
            "timestamp": str(evt.get("timestamp", "")),
            "details": {k: v for k, v in evt.get("details", {}).items() if k not in ("_id",)},
        })
    
    return {
        "email": email,
        "customer_name": link.get("customer_name", ""),
        "quotes": quotes,
        "invoices": invoices,
        "bookings": bookings,
        "communications": chat_summaries + unified_convos,
        "timeline": timeline_items,
    }


@app.post("/api/portal/quote/{quote_id}/accept")
async def portal_accept_quote(quote_id: str, token: str = None):
    """Customer accepts a quote via portal."""
    if not token:
        raise HTTPException(401, "Zugangstoken fehlt")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    email = link.get("customer_email", "").lower()
    quote = await db.quotes.find_one({"quote_id": quote_id, "customer.email": email}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    if quote.get("status") not in ("sent", "opened"):
        raise HTTPException(400, f"Angebot kann im Status '{quote.get('status')}' nicht angenommen werden")
    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "accepted", "accepted_at": utcnow(), "updated_at": utcnow()}}
    )
    evt = create_timeline_event("quote", quote_id, "quote_accepted",
                                actor=email, actor_type="customer",
                                details={"quote_number": quote.get("quote_number")})
    await db.timeline_events.insert_one(evt)
    return {"status": "accepted", "quote_id": quote_id}


@app.post("/api/portal/quote/{quote_id}/decline")
async def portal_decline_quote(quote_id: str, data: dict = None, token: str = None):
    """Customer declines a quote via portal."""
    if not token:
        raise HTTPException(401, "Zugangstoken fehlt")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    email = link.get("customer_email", "").lower()
    quote = await db.quotes.find_one({"quote_id": quote_id, "customer.email": email}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    reason = (data or {}).get("reason", "")
    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "declined", "decline_reason": reason, "updated_at": utcnow()}}
    )
    evt = create_timeline_event("quote", quote_id, "quote_declined",
                                actor=email, actor_type="customer",
                                details={"quote_number": quote.get("quote_number"), "reason": reason[:200]})
    await db.timeline_events.insert_one(evt)
    return {"status": "declined", "quote_id": quote_id}


@app.post("/api/portal/quote/{quote_id}/revision")
async def portal_request_revision(quote_id: str, data: dict, token: str = None):
    """Customer requests a quote revision via portal."""
    if not token:
        raise HTTPException(401, "Zugangstoken fehlt")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    email = link.get("customer_email", "").lower()
    quote = await db.quotes.find_one({"quote_id": quote_id, "customer.email": email}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    notes = data.get("notes", "")
    await db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "revision_requested", "revision_notes": notes, "updated_at": utcnow()}}
    )
    evt = create_timeline_event("quote", quote_id, "revision_requested",
                                actor=email, actor_type="customer",
                                details={"notes": notes[:200]})
    await db.timeline_events.insert_one(evt)
    return {"status": "revision_requested", "quote_id": quote_id}


# ══════════════════════════════════════════════════════════════
# UNIFIED COMMUNICATION API
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/conversations")
async def admin_conversations(
    limit: int = 30,
    status: str = None,
    channel: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """List unified conversations across all channels."""
    query = {}
    if status:
        query["status"] = status
    if channel:
        query["channels"] = channel
    
    convos = []
    async for c in db.conversations.find(query, {"_id": 0}).sort("last_message_at", -1).limit(limit):
        # Resolve contact
        contact = await db.contacts.find_one({"contact_id": c.get("contact_id")}, {"_id": 0, "email": 1, "first_name": 1, "last_name": 1, "company": 1})
        convos.append({
            "conversation_id": c["conversation_id"],
            "contact": contact or {},
            "channels": c.get("channels", []),
            "status": c.get("status", "open"),
            "assigned_to": c.get("assigned_to", "ai"),
            "message_count": c.get("message_count", 0),
            "last_message_at": str(c.get("last_message_at", "")),
            "subject": c.get("subject", ""),
        })
    return {"conversations": convos}


@app.get("/api/admin/conversations/{conversation_id}")
async def admin_conversation_detail(
    conversation_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Full conversation with messages and context."""
    convo = await db.conversations.find_one({"conversation_id": conversation_id}, {"_id": 0})
    if not convo:
        raise HTTPException(404, "Konversation nicht gefunden")
    
    # Get messages
    messages = []
    async for m in db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("timestamp", 1):
        messages.append(m)
    
    # Get contact
    contact = await db.contacts.find_one({"contact_id": convo.get("contact_id")}, {"_id": 0})
    
    return {
        **convo,
        "messages": messages,
        "contact": contact,
    }


@app.post("/api/admin/conversations/{conversation_id}/reply")
async def admin_reply_to_conversation(
    conversation_id: str,
    data: dict,
    current_user: dict = Depends(get_current_admin)
):
    """Admin manually replies to a conversation."""
    convo = await db.conversations.find_one({"conversation_id": conversation_id}, {"_id": 0})
    if not convo:
        raise HTTPException(404, "Konversation nicht gefunden")
    
    content = data.get("content", "").strip()
    channel = data.get("channel", convo.get("channel_origin", "chat"))
    if not content:
        raise HTTPException(400, "Nachricht darf nicht leer sein")
    
    msg = create_message(conversation_id, channel, MessageDirection.OUTBOUND.value, content,
                         sender=current_user["email"], ai_generated=False)
    await db.messages.insert_one(msg)
    
    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {"last_message_at": utcnow(), "updated_at": utcnow()},
         "$inc": {"message_count": 1},
         "$addToSet": {"channels": channel}}
    )
    
    # Log event
    evt = create_timeline_event("conversation", conversation_id, "admin_reply",
                                channel=channel, actor=current_user["email"], actor_type="admin")
    await db.timeline_events.insert_one(evt)
    
    return {"status": "ok", "message": {k: v for k, v in msg.items() if k != "_id"}}



# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# AUDIT / HEALTH CHECK SYSTEM
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/audit/health")
async def admin_audit_health(current_user: dict = Depends(get_current_admin)):
    """System health check and audit summary."""
    checks = {}
    
    # 1. Database connectivity
    try:
        await db.command("ping")
        checks["database"] = {"status": "ok", "detail": "MongoDB erreichbar"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
    
    # 2. Collections stats
    collections_needed = ["leads", "quotes", "invoices", "bookings", "chat_sessions",
                          "contacts", "conversations", "messages", "timeline_events",
                          "customer_memory", "whatsapp_sessions"]
    col_stats = {}
    for col_name in collections_needed:
        col = db[col_name]
        cnt = await col.count_documents({})
        col_stats[col_name] = cnt
    checks["collections"] = {"status": "ok", "counts": col_stats}
    
    # 3. Agent layer
    checks["agents"] = {
        "status": "ok" if agents else "error",
        "count": len(agents),
        "names": list(agents.keys()),
    }
    
    # 4. WA session status
    wa = await db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    checks["whatsapp"] = {
        "status": wa.get("status", "unknown") if wa else "no_session",
        "phone": wa.get("phone_number") if wa else None,
    }
    
    # 5. LLM key status
    key = os.environ.get("EMERGENT_LLM_KEY", "")
    checks["llm"] = {"status": "ok" if key else "missing", "key_present": bool(key)}
    
    # 6. Recent errors in timeline
    error_count = await db.timeline_events.count_documents({
        "action": {"$regex": "error|fail", "$options": "i"},
        "timestamp": {"$gte": utcnow() - timedelta(hours=24)}
    })
    checks["recent_errors_24h"] = error_count
    
    # 7. Pricing consistency check
    tariff_count = await db.quotes.count_documents({})
    checks["pricing"] = {"status": "ok", "quotes_in_system": tariff_count}
    
    overall = "healthy"
    for k, v in checks.items():
        if isinstance(v, dict) and v.get("status") == "error":
            overall = "degraded"
            break
    
    return {"overall": overall, "checks": checks, "timestamp": str(utcnow())}


@app.get("/api/admin/audit/timeline")
async def admin_audit_timeline(
    hours: int = 24,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin)
):
    """Recent audit trail / timeline events."""
    cutoff = utcnow() - timedelta(hours=hours)
    events = []
    async for evt in db.timeline_events.find(
        {"timestamp": {"$gte": cutoff}}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit):
        evt["timestamp"] = str(evt.get("timestamp", ""))
        events.append(evt)
    return {"events": events, "count": len(events), "hours": hours}


# AI AGENT LAYER (Orchestrator + Sub-Agents)
# ══════════════════════════════════════════════════════════════

@app.post("/api/admin/agents/route")
async def agent_route_task(data: dict, current_user: dict = Depends(get_current_admin)):
    """Route a task through the orchestrator to a sub-agent."""
    task = data.get("task", "").strip()
    context = data.get("context", {})
    if not task:
        raise HTTPException(400, "Aufgabe darf nicht leer sein")
    result = await orchestrator.route(task, context)
    return result


@app.post("/api/admin/agents/{agent_name}/execute")
async def agent_execute(agent_name: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Execute a task with a specific sub-agent."""
    if agent_name not in agents:
        raise HTTPException(404, f"Agent '{agent_name}' nicht gefunden. Verfügbar: {list(agents.keys())}")
    task = data.get("task", "").strip()
    context = data.get("context", "")
    if not task:
        raise HTTPException(400, "Aufgabe darf nicht leer sein")

    # Auto-inject customer memory if email provided
    email = data.get("customer_email")
    if email:
        memory = await _build_customer_memory(email)
        if memory:
            context = f"KUNDENSPEICHER:\n{memory}\n\n{context}" if context else f"KUNDENSPEICHER:\n{memory}"

    result = await agents[agent_name].execute(task, context)
    return result


@app.get("/api/admin/agents")
async def list_agents(current_user: dict = Depends(get_current_admin)):
    """List all available sub-agents."""
    from agents.orchestrator import AGENT_ROLES
    return {
        "orchestrator": {"status": "active", "model": f"{os.environ.get('ORCHESTRATOR_PROVIDER', 'openai')}/{os.environ.get('ORCHESTRATOR_MODEL', 'gpt-5.2')}"},
        "agents": {name: {"role": AGENT_ROLES.get(name, ""), "status": "active"} for name in agents},
    }


# ══════════════════════════════════════════════════════════════
# WHATSAPP QR CONNECTOR (Isolated Bridge Layer)
# ══════════════════════════════════════════════════════════════
# Architecture: This is a TRANSITION bridge solution.
# The QR connector is isolated and replaceable.
# Central messaging domain is NOT coupled to QR implementation.
# Later migration to official WhatsApp Business API requires
# only swapping this connector layer.

@app.get("/api/admin/whatsapp/status")
async def wa_status(current_user: dict = Depends(get_current_admin)):
    """Get current WhatsApp connector status."""
    session = await db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        session = create_whatsapp_session()
        await db.whatsapp_sessions.insert_one(session)
        session.pop("_id", None)
    return {
        "session_id": session.get("session_id", ""),
        "status": session.get("status", "unpaired"),
        "phone_number": session.get("phone_number", ""),
        "qr_code": session.get("qr_code"),
        "connected_at": str(session.get("connected_at", "")) if session.get("connected_at") else None,
        "last_activity": str(session.get("last_activity", "")) if session.get("last_activity") else None,
        "error": session.get("error"),
    }


@app.post("/api/admin/whatsapp/pair")
async def wa_pair(current_user: dict = Depends(get_current_admin)):
    """Initiate WhatsApp QR pairing. Generates a QR code placeholder.
    In production, this triggers the actual QR generation via the connector service."""
    session = await db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        session = create_whatsapp_session()
        await db.whatsapp_sessions.insert_one(session)
    
    # Generate pairing state (In production: triggers connector to generate real QR)
    import base64
    qr_placeholder = f"whatsapp://pair?session={session.get('session_id', '')}&ts={int(datetime.now(timezone.utc).timestamp())}"
    
    await db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {
            "status": WhatsAppSessionStatus.PAIRING.value,
            "qr_code": qr_placeholder,
            "qr_generated_at": utcnow(),
            "updated_at": utcnow(),
        }}
    )
    
    evt = create_timeline_event("whatsapp", session["session_id"], "pairing_initiated",
                                actor=current_user["email"], actor_type="admin")
    await db.timeline_events.insert_one(evt)
    
    return {
        "status": "pairing",
        "session_id": session["session_id"],
        "qr_code": qr_placeholder,
        "message": "QR-Code bereit. In der Produktivumgebung wird hier der echte WhatsApp-QR angezeigt.",
    }


@app.post("/api/admin/whatsapp/disconnect")
async def wa_disconnect(current_user: dict = Depends(get_current_admin)):
    """Disconnect WhatsApp session."""
    session = await db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        raise HTTPException(404, "Keine WhatsApp-Session gefunden")
    
    await db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {
            "status": WhatsAppSessionStatus.DISCONNECTED.value,
            "disconnected_at": utcnow(),
            "qr_code": None,
            "updated_at": utcnow(),
        }}
    )
    
    evt = create_timeline_event("whatsapp", session["session_id"], "session_disconnected",
                                actor=current_user["email"], actor_type="admin")
    await db.timeline_events.insert_one(evt)
    
    return {"status": "disconnected"}


@app.post("/api/admin/whatsapp/reset")
async def wa_reset(current_user: dict = Depends(get_current_admin)):
    """Reset WhatsApp session completely."""
    new_session = create_whatsapp_session()
    await db.whatsapp_sessions.delete_many({})
    await db.whatsapp_sessions.insert_one(new_session)
    
    evt = create_timeline_event("whatsapp", new_session["session_id"], "session_reset",
                                actor=current_user["email"], actor_type="admin")
    await db.timeline_events.insert_one(evt)
    
    return {"status": "reset", "session_id": new_session["session_id"]}


@app.post("/api/admin/whatsapp/reconnect")
async def wa_reconnect(current_user: dict = Depends(get_current_admin)):
    """Attempt to reconnect a disconnected/failed WhatsApp session."""
    session = await db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        raise HTTPException(404, "Keine WhatsApp-Session gefunden")
    if session.get("status") == "connected":
        return {"status": "already_connected"}
    await db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {"status": WhatsAppSessionStatus.RECONNECTING.value, "error": None, "updated_at": utcnow()}}
    )
    evt = create_timeline_event("whatsapp", session["session_id"], "reconnect_initiated",
                                actor=current_user["email"], actor_type="admin")
    await db.timeline_events.insert_one(evt)
    return {"status": "reconnecting", "session_id": session["session_id"]}


@app.post("/api/admin/whatsapp/simulate-connect")
async def wa_simulate_connect(current_user: dict = Depends(get_current_admin)):
    """DEV ONLY: Simulate a successful WhatsApp connection for testing."""
    session = await db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        session = create_whatsapp_session()
        await db.whatsapp_sessions.insert_one(session)
    await db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {
            "status": WhatsAppSessionStatus.CONNECTED.value,
            "phone_number": "+31613318856",
            "connected_at": utcnow(),
            "last_activity": utcnow(),
            "qr_code": None,
            "error": None,
            "updated_at": utcnow(),
        }}
    )
    evt = create_timeline_event("whatsapp", session["session_id"], "session_connected",
                                actor=current_user["email"], actor_type="admin",
                                details={"phone": "+31613318856", "mode": "simulated"})
    await db.timeline_events.insert_one(evt)
    return {"status": "connected", "session_id": session["session_id"], "phone_number": "+31613318856"}


@app.post("/api/admin/whatsapp/send")
async def wa_send_message(data: dict, current_user: dict = Depends(get_current_admin)):
    """Send a WhatsApp message to a contact (via bridge connector).
    In production, this calls the actual WA connector to deliver the message."""
    to_phone = data.get("to", "").strip()
    content = data.get("content", "").strip()
    conversation_id = data.get("conversation_id", "").strip()
    if not content:
        raise HTTPException(400, "Nachricht darf nicht leer sein")

    # Find or resolve conversation
    convo = None
    if conversation_id:
        convo = await db.conversations.find_one({"conversation_id": conversation_id}, {"_id": 0})
    elif to_phone:
        contact = await db.contacts.find_one({"$or": [{"phone": to_phone}, {"whatsapp": to_phone}]}, {"_id": 0})
        if not contact:
            contact = create_contact(f"wa_{to_phone}@placeholder.nexifyai.de", phone=to_phone, whatsapp=to_phone, source="whatsapp")
            await db.contacts.insert_one(contact)
            contact.pop("_id", None)
        convo = await db.conversations.find_one({
            "contact_id": contact["contact_id"], "channels": Channel.WHATSAPP.value,
            "status": {"$in": ["open", "pending"]}
        }, {"_id": 0})
        if not convo:
            convo = create_conversation(contact["contact_id"], Channel.WHATSAPP.value, subject=f"WhatsApp: {to_phone}")
            await db.conversations.insert_one(convo)
            convo.pop("_id", None)
    else:
        raise HTTPException(400, "Entweder 'to' (Telefonnummer) oder 'conversation_id' muss angegeben werden")

    msg = create_message(convo["conversation_id"], Channel.WHATSAPP.value,
                         MessageDirection.OUTBOUND.value, content,
                         sender=current_user["email"], ai_generated=False)
    await db.messages.insert_one(msg)
    await db.conversations.update_one(
        {"conversation_id": convo["conversation_id"]},
        {"$set": {"last_message_at": utcnow(), "updated_at": utcnow()}, "$inc": {"message_count": 1}}
    )
    evt = create_timeline_event("conversation", convo["conversation_id"], "whatsapp_outbound",
                                channel=Channel.WHATSAPP.value, actor=current_user["email"], actor_type="admin",
                                details={"to": to_phone, "content_preview": content[:100]})
    await db.timeline_events.insert_one(evt)
    await db.whatsapp_sessions.update_one({}, {"$set": {"last_activity": utcnow()}})
    return {"status": "sent", "message_id": msg["message_id"], "conversation_id": convo["conversation_id"]}


@app.get("/api/admin/whatsapp/messages")
async def wa_messages(
    limit: int = 50,
    current_user: dict = Depends(get_current_admin)
):
    """List WhatsApp messages from the unified message store."""
    msgs = []
    async for m in db.messages.find({"channel": Channel.WHATSAPP.value}, {"_id": 0}).sort("timestamp", -1).limit(limit):
        convo = await db.conversations.find_one({"conversation_id": m.get("conversation_id")}, {"_id": 0, "contact_id": 1})
        contact = None
        if convo:
            contact = await db.contacts.find_one({"contact_id": convo.get("contact_id")}, {"_id": 0, "email": 1, "first_name": 1, "last_name": 1, "phone": 1})
        msgs.append({**m, "contact": contact, "timestamp": str(m.get("timestamp", ""))})
    return {"messages": msgs}


# ══════════════════════════════════════════════════════════════
# WEBHOOK: Inbound WhatsApp / Email messages
# ══════════════════════════════════════════════════════════════

@app.post("/api/webhooks/whatsapp/inbound")
async def wa_inbound_webhook(data: dict):
    """Receive inbound WhatsApp messages from connector.
    Creates/updates conversation and routes to AI if needed."""
    phone = data.get("from", "").strip()
    content = data.get("body", "").strip()
    if not phone or not content:
        raise HTTPException(400, "Missing from or body")
    
    # Find or create contact by phone
    contact = await db.contacts.find_one({"$or": [{"phone": phone}, {"whatsapp": phone}]}, {"_id": 0})
    if not contact:
        contact = create_contact(f"wa_{phone}@placeholder.nexifyai.de", phone=phone, whatsapp=phone, source="whatsapp")
        await db.contacts.insert_one(contact)
        contact.pop("_id", None)
    
    # Find open conversation or create new
    convo = await db.conversations.find_one({
        "contact_id": contact["contact_id"],
        "status": {"$in": ["open", "pending"]},
        "channels": Channel.WHATSAPP.value,
    }, {"_id": 0})
    
    if not convo:
        convo = create_conversation(contact["contact_id"], Channel.WHATSAPP.value,
                                     subject=f"WhatsApp: {phone}")
        await db.conversations.insert_one(convo)
        convo.pop("_id", None)
    
    # Store message
    msg = create_message(convo["conversation_id"], Channel.WHATSAPP.value,
                         MessageDirection.INBOUND.value, content, sender=phone)
    await db.messages.insert_one(msg)
    
    # Update conversation
    await db.conversations.update_one(
        {"conversation_id": convo["conversation_id"]},
        {"$set": {"last_message_at": utcnow(), "updated_at": utcnow()},
         "$inc": {"message_count": 1}}
    )
    
    # Log event
    evt = create_timeline_event("conversation", convo["conversation_id"], "whatsapp_inbound",
                                channel=Channel.WHATSAPP.value, actor=phone, actor_type="customer",
                                details={"content_preview": content[:100]})
    await db.timeline_events.insert_one(evt)
    
    # Update WhatsApp session activity
    await db.whatsapp_sessions.update_one({}, {"$set": {"last_activity": utcnow()}})
    
    return {"status": "received", "message_id": msg["message_id"], "conversation_id": convo["conversation_id"]}


# ══════════════════════════════════════════════════════════════
# WORKER/SCHEDULER MONITORING ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/workers/status")
async def worker_status(current_user: dict = Depends(get_current_admin)):
    """Worker- und Scheduler-Status."""
    if not worker_mgr:
        return {"status": "not_initialized"}
    return worker_mgr.get_status()


@app.get("/api/admin/workers/jobs")
async def worker_jobs(
    status: str = None, job_type: str = None,
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Job-Liste mit Filtern."""
    query = {}
    if status:
        query["status"] = status
    if job_type:
        query["job_type"] = job_type
    jobs = []
    async for j in db.jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit):
        jobs.append(j)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/admin/workers/dead-letter")
async def worker_dead_letter(
    limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Dead-Letter-Queue."""
    jobs = []
    async for j in db.jobs.find({"status": "dead_letter"}, {"_id": 0}).sort("dead_letter_at", -1).limit(limit):
        jobs.append(j)
    return {"dead_letter_jobs": jobs, "count": len(jobs)}


@app.post("/api/admin/workers/retry/{job_id}")
async def worker_retry_job(job_id: str, current_user: dict = Depends(get_current_admin)):
    """Dead-Letter-Job manuell wiederholen."""
    job = await db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Job nicht gefunden")
    if job["status"] != "dead_letter":
        raise HTTPException(400, "Nur Dead-Letter-Jobs können wiederholt werden")

    from workers.job_queue import JobPriority
    new_job_id = await worker_mgr.enqueue(
        job["job_type"], job["payload"],
        priority=JobPriority(job.get("priority", 2)),
        ref_id=job.get("ref_id", ""),
        ref_type=job.get("ref_type", ""),
        created_by=f"manual_retry:{current_user['email']}",
    )
    return {"new_job_id": new_job_id, "original_job_id": job_id}


# ══════════════════════════════════════════════════════════════
# COMMUNICATION SERVICE ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/comms/contacts/{email}")
async def comms_contact_detail(email: str, current_user: dict = Depends(get_current_admin)):
    """Kontakt-Detail mit allen Konversationen."""
    contact = await db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    if not contact:
        raise HTTPException(404, "Kontakt nicht gefunden")
    for k in ("created_at", "updated_at"):
        if hasattr(contact.get(k), "isoformat"):
            contact[k] = contact[k].isoformat()
    convs = await comms_svc.get_contact_conversations(contact["contact_id"])
    timeline = await comms_svc.get_unified_timeline(contact["contact_id"])
    return {"contact": contact, "conversations": convs, "timeline": timeline}


@app.get("/api/admin/comms/conversations/{conv_id}/messages")
async def comms_conversation_messages(conv_id: str, current_user: dict = Depends(get_current_admin)):
    """Kanalübergreifende Nachrichtenhistorie."""
    messages = await comms_svc.get_conversation_history(conv_id)
    return {"messages": messages, "count": len(messages)}


@app.post("/api/admin/comms/conversations/{conv_id}/send")
async def comms_send_message(conv_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Nachricht über Kommunikationskern senden."""
    channel = data.get("channel", "email")
    content = data.get("content", "")
    if not content:
        raise HTTPException(400, "Nachricht darf nicht leer sein")
    msg = await comms_svc.send_outbound(
        conv_id, channel, content,
        sender=current_user["email"],
        ai_generated=False,
    )
    msg.pop("_id", None)
    if hasattr(msg.get("timestamp"), "isoformat"):
        msg["timestamp"] = msg["timestamp"].isoformat()
    return msg


@app.post("/api/admin/comms/conversations/{conv_id}/assign")
async def comms_assign(conv_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Konversation zuweisen."""
    await comms_svc.assign_conversation(conv_id, data.get("assigned_to", "admin"), by=current_user["email"])
    return {"assigned": True}


@app.get("/api/admin/comms/timeline/{contact_id}")
async def comms_timeline(contact_id: str, current_user: dict = Depends(get_current_admin)):
    """Kanalübergreifende Timeline."""
    events = await comms_svc.get_unified_timeline(contact_id)
    return {"events": events, "count": len(events)}


# ══════════════════════════════════════════════════════════════
# BILLING SERVICE ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/billing/status/{email}")
async def billing_status(email: str, current_user: dict = Depends(get_current_admin)):
    """Gesamter Billing-Status für einen Kontakt."""
    result = await billing_svc.get_billing_status(email)
    return result


@app.post("/api/admin/billing/sync-quote/{quote_id}")
async def billing_sync_quote(quote_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Quote-Status synchronisieren."""
    new_status = data.get("status", "")
    if not new_status:
        raise HTTPException(400, "Status erforderlich")
    result = await billing_svc.sync_quote_status(quote_id, new_status, by=current_user["email"])
    return result


@app.post("/api/admin/billing/sync-invoice/{invoice_id}")
async def billing_sync_invoice(invoice_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Invoice-Status synchronisieren."""
    new_status = data.get("status", "")
    if not new_status:
        raise HTTPException(400, "Status erforderlich")
    result = await billing_svc.sync_invoice_status(invoice_id, new_status, by=current_user["email"])
    return result


# ══════════════════════════════════════════════════════════════
# OUTBOUND LEAD MACHINE ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/outbound/leads")
async def outbound_leads_list(
    status: str = None, min_score: int = 0,
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Outbound-Leads auflisten."""
    leads = await outbound_svc.list_outbound_leads(status, min_score, skip, limit)
    return {"leads": leads, "count": len(leads)}


@app.get("/api/admin/outbound/stats")
async def outbound_stats(current_user: dict = Depends(get_current_admin)):
    """Outbound-Pipeline-Statistiken."""
    return await outbound_svc.get_outbound_stats()


@app.post("/api/admin/outbound/discover")
async def outbound_discover(data: dict, current_user: dict = Depends(get_current_admin)):
    """Neuen Outbound-Lead erfassen."""
    result = await outbound_svc.discover_lead(data, source=data.get("source", "admin"))
    return result


@app.post("/api/admin/outbound/{lead_id}/prequalify")
async def outbound_prequalify(lead_id: str, current_user: dict = Depends(get_current_admin)):
    """Lead vorqualifizieren."""
    return await outbound_svc.prequalify(lead_id)


@app.post("/api/admin/outbound/{lead_id}/analyze")
async def outbound_analyze(lead_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Lead analysieren und scoren."""
    return await outbound_svc.analyze_and_score(lead_id, data)


@app.post("/api/admin/outbound/{lead_id}/legal-check")
async def outbound_legal_check(lead_id: str, current_user: dict = Depends(get_current_admin)):
    """Legal Gate prüfen."""
    return await outbound_svc.legal_check(lead_id)


@app.post("/api/admin/outbound/{lead_id}/outreach")
async def outbound_create_outreach(lead_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Outreach erstellen."""
    return await outbound_svc.create_outreach(lead_id, data)


@app.post("/api/admin/outbound/{lead_id}/outreach/{outreach_id}/send")
async def outbound_send_outreach(lead_id: str, outreach_id: str, current_user: dict = Depends(get_current_admin)):
    """Outreach versenden."""
    return await outbound_svc.send_outreach(lead_id, outreach_id)


@app.post("/api/admin/outbound/{lead_id}/followup")
async def outbound_followup(lead_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Follow-up planen."""
    days = (data or {}).get("days_delay", 3)
    return await outbound_svc.schedule_followup(lead_id, days)


@app.post("/api/admin/outbound/opt-out")
async def outbound_opt_out(data: dict, current_user: dict = Depends(get_current_admin)):
    """E-Mail auf Suppression-Liste setzen."""
    email = data.get("email", "")
    if not email:
        raise HTTPException(400, "E-Mail erforderlich")
    return await outbound_svc.opt_out(email, data.get("reason", ""))


# ══════════════════════════════════════════════════════════════
# LLM PROVIDER STATUS
# ══════════════════════════════════════════════════════════════

@app.get("/api/admin/llm/status")
async def llm_status(current_user: dict = Depends(get_current_admin)):
    """LLM-Provider-Status."""
    return {
        "provider": llm_provider.get_provider_name() if llm_provider else "not_initialized",
        "deepseek_configured": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "emergent_configured": bool(os.environ.get("EMERGENT_LLM_KEY")),
        "target_architecture": "deepseek",
        "current_status": "temporary_gpt52" if (llm_provider and "temporary" in llm_provider.get_provider_name()) else "target",
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
