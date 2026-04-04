"""
NeXifyAI Backend v3.1 - Modular Architecture
Thin orchestrator: lifespan, middleware, router mounting.
All route logic lives in /routes/*.py, shared state in routes/shared.py.
"""
import os
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import resend

from agents.orchestrator import Orchestrator
from agents.research import create_research_agent
from agents.outreach import create_outreach_agent
from agents.offer import create_offer_agent
from agents.support import create_support_agent
from agents.intake import create_intake_agent
from agents.planning import create_planning_agent
from agents.finance import create_finance_agent
from agents.design import create_design_agent
from agents.qa import create_qa_agent
from memory_service import MemoryService
from workers.manager import WorkerManager
from services.comms import CommunicationService
from services.billing import BillingService
from services.outbound import OutboundLeadMachine
from services.legal_guardian import LegalGuardian
from services.llm_provider import create_llm_provider

import routes.shared as shared

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nexifyai")

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "nexifyai")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "p.courbois@icloud.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# ══════════════════════════════════════════════════════════════
# ADVISOR SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════
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


# Password hashing
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


# ══════════════════════════════════════════════════════════════
# LIFESPAN — DB, Services, Agents, Shared State
# ══════════════════════════════════════════════════════════════
db_client: Optional[AsyncIOMotorClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client

    # --- Database ---
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]

    # --- Indexes ---
    await db.leads.create_index("email")
    await db.leads.create_index("created_at")
    await db.leads.create_index("status")
    await db.bookings.create_index("date")
    await db.chat_sessions.create_index("session_id")
    await db.analytics.create_index([("event", 1), ("timestamp", -1)])
    await db.admin_users.create_index("email", unique=True)
    await db.audit_log.create_index("timestamp")
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
    await db.legal_audit.create_index("type")
    await db.legal_audit.create_index("timestamp")
    await db.legal_risks.create_index([("entity_type", 1), ("entity_id", 1)])
    await db.legal_risks.create_index("resolved")
    await db.opt_outs.create_index("email", unique=True)
    await db.outbound_leads.create_index("outbound_lead_id", unique=True)
    await db.outbound_leads.create_index("status")
    await db.outbound_leads.create_index("score")
    await db.outbound_leads.create_index("contact_email")
    await db.suppression_list.create_index("email", unique=True)
    await db.projects.create_index("project_id", unique=True)
    await db.projects.create_index("customer_email")
    await db.projects.create_index("status")
    await db.project_sections.create_index([("project_id", 1), ("section_key", 1)])
    await db.project_chat.create_index("project_id")
    await db.project_versions.create_index([("project_id", 1), ("version", -1)])
    await db.contracts.create_index("contract_id", unique=True)
    await db.contracts.create_index("customer.email")
    await db.contracts.create_index("status")
    await db.contracts.create_index("quote_id")
    await db.contract_appendices.create_index("contract_id")
    await db.contract_evidence.create_index("contract_id")
    await db.webhook_events.create_index([("timestamp", -1)])
    await db.webhook_events.create_index("event")
    await db.webhook_events.create_index("order_id")
    await db.documents.create_index("document_id", unique=True, sparse=True)
    await db.documents.create_index("entity_id")

    # --- Admin User ---
    if ADMIN_PASSWORD:
        existing = await db.admin_users.find_one({"email": ADMIN_EMAIL})
        new_hash = hash_password(ADMIN_PASSWORD)
        if not existing:
            await db.admin_users.insert_one({
                "email": ADMIN_EMAIL,
                "password_hash": new_hash,
                "role": "admin",
                "created_at": datetime.now(timezone.utc)
            })
            logger.info(f"Admin user created: {ADMIN_EMAIL}")
        elif existing.get("password_hash") != new_hash:
            await db.admin_users.update_one(
                {"email": ADMIN_EMAIL},
                {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"Admin password updated: {ADMIN_EMAIL}")

    # --- Service Layer ---
    memory_svc = MemoryService(db)
    worker_mgr = WorkerManager(db, max_workers=4)
    await worker_mgr.start()
    llm_provider = create_llm_provider()
    comms_svc = CommunicationService(db, worker_manager=worker_mgr)
    billing_svc = BillingService(db, worker_manager=worker_mgr, comms_service=comms_svc)
    outbound_svc = OutboundLeadMachine(db, worker_manager=worker_mgr, comms_service=comms_svc)
    legal_svc = LegalGuardian(db, memory_svc=memory_svc)

    # --- Agent Layer ---
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

    # --- Object Storage ---
    from services.storage import init_storage
    try:
        init_storage()
    except Exception as e:
        logger.warning(f"Object Storage init: {e}")

    # ═══════════ POPULATE SHARED STATE ═══════════
    shared.S.db = db
    shared.S.worker_mgr = worker_mgr
    shared.S.comms_svc = comms_svc
    shared.S.billing_svc = billing_svc
    shared.S.outbound_svc = outbound_svc
    shared.S.legal_svc = legal_svc
    shared.S.llm_provider = llm_provider
    shared.S.orchestrator = orchestrator
    shared.S.agents = agents
    shared.S.memory_svc = memory_svc
    shared.init_config()
    shared.S.ADVISOR_SYSTEM_PROMPT = get_system_prompt()

    logger.info("NeXifyAI Backend v3.1 started — Modular Architecture aktiv")
    yield

    # --- Shutdown ---
    await worker_mgr.stop()
    db_client.close()


# ══════════════════════════════════════════════════════════════
# APP + MIDDLEWARE
# ══════════════════════════════════════════════════════════════
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app = FastAPI(title="NeXifyAI API", version="3.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: Unhandled Exceptions → strukturierter JSON-Error statt 500 HTML."""
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Interner Serverfehler", "path": request.url.path},
    )

CORS_ORIGINS = [
    os.environ.get("FRONTEND_URL", "").rstrip("/"),
    "https://contract-os.preview.emergentagent.com",
    "http://localhost:3000",
]
CORS_ORIGINS = [o for o in CORS_ORIGINS if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    if request.url.path.startswith("/api/portal/") or request.url.path.startswith("/api/documents/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


# ══════════════════════════════════════════════════════════════
# ROUTER MOUNTING
# ══════════════════════════════════════════════════════════════
from routes.auth_routes import router as auth_router
from routes.public_routes import router as public_router
from routes.admin_routes import router as admin_router
from routes.billing_routes import router as billing_router
from routes.portal_routes import router as portal_router
from routes.comms_routes import router as comms_router
from routes.contract_routes import router as contract_router
from routes.project_routes import router as project_router
from routes.outbound_routes import router as outbound_router
from routes.monitoring_routes import router as monitoring_router

app.include_router(auth_router)
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(billing_router)
app.include_router(portal_router)
app.include_router(comms_router)
app.include_router(contract_router)
app.include_router(project_router)
app.include_router(outbound_router)
app.include_router(monitoring_router)
