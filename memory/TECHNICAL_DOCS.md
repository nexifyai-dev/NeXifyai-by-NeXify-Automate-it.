# NeXifyAI — Technische Architektur-Dokumentation

## 1. Worker, Trigger & Monitoring — Bestandsnachweis

### 1.1 Aktive Worker / Dienste

| Worker | Typ | Trigger | Retry/Fallback | Status |
|--------|-----|---------|----------------|--------|
| **FastAPI Backend** | Supervisor-managed | Auto-Start, Hot-Reload | supervisorctl restart | AKTIV |
| **React Frontend** | Supervisor-managed | Auto-Start, Hot-Reload | supervisorctl restart | AKTIV |
| **MongoDB** | System-Dienst | Container-Start | Automatisch | AKTIV |
| **Orchestrator** | In-Process (FastAPI) | API-Call `/api/admin/agents/execute` | try/except + Audit-Log | AKTIV |
| **MemoryService** | In-Process (FastAPI) | Jeder Chat/CRUD | Inline-Error-Handling | AKTIV |
| **Email-Worker** | ENTKOPPELT (JobQueue) | Job-Typ `send_email` | 3x Retry + Dead-Letter | AKTIV |
| **JobQueue** | In-Process (asyncio) | Lifespan-Start | 4 Worker, PriorityQueue, Crash-Recovery | AKTIV |
| **Scheduler** | APScheduler (asyncio) | Lifespan-Start | 7 Cron-/Interval-Jobs | AKTIV |
| **CommunicationService** | In-Process (Service-Layer) | API-Calls | Kanalübergreifend | AKTIV |
| **BillingService** | In-Process (Service-Layer) | API-Calls + Worker | Status-Sync | AKTIV |
| **OutboundLeadMachine** | In-Process (Service-Layer) | API-Calls + Worker | Legal Gate | AKTIV |

### 1.2 Job-Queue Architektur

```
Enqueue (API/Scheduler/Service)
    → asyncio.PriorityQueue (In-Memory)
    → MongoDB Persistenz (jobs Collection)
    → 4 Worker-Tasks (asyncio)
    → Handler (Business-Logik)
    → Retry (exp. Backoff: 10s→20s→40s...max 5min)
    → Dead-Letter nach 3 Versuchen
    → Timeline/Audit bei jedem Übergang
```

Registrierte Handler:
- `send_email` — E-Mail-Versand (Resend)
- `payment_reminder` — Zahlungserinnerung (Stufe 1-3)
- `dunning_escalation` — Mahnvorstufen (1-3)
- `lead_followup` — Lead-Follow-up-Markierung
- `booking_reminder` — Terminerinnerung
- `quote_expiry` — Angebotsablauf
- `ai_task` — KI-Aufgabe (entkoppelt)
- `status_transition` — Status-Folgelogik

### 1.3 Scheduler-Jobs

| Job | Trigger | Funktion |
|-----|---------|----------|
| `payment_reminders` | Täglich 09:00 | Überfällige Rechnungen prüfen, Reminder-Jobs erstellen |
| `dunning_stages` | Täglich 10:00 | Mahnstufen eskalieren (21/35/49 Tage) |
| `lead_followups` | Täglich 08:30 | Leads ohne Follow-up seit 3+ Tagen markieren |
| `booking_reminders` | Alle 4h | Termine in nächsten 24h erinnern |
| `quote_expiry` | Alle 12h | Abgelaufene Angebote markieren |
| `health_check` | Alle 30min | System-Health in Timeline schreiben |
| `dead_letter_alert` | Alle 2h | Dead-Letter-Alarm wenn > 0 |

### 1.4 Trigger-Matrix (erweitert)

| Flow | Trigger | Worker/Handler | Audit | Memory |
|------|---------|----------------|-------|--------|
| Login (Admin) | POST /api/admin/login | JWT-Generierung | `login_success`/`login_failed` | — |
| Login (Kunde) | POST /api/auth/verify-token | JWT-Generierung | `customer_login_magic_link` | Ja |
| Magic Link | POST /api/auth/request-magic-link | Worker: `send_email` | `magic_link_requested` | — |
| Lead-Erstellung | POST /api/contact | Lead-Insert + Worker: `send_email` | Timeline `lead_created` | — |
| Angebot versenden | POST /api/admin/quotes/{id}/send | Worker: `send_email` | `quote_sent` + Timeline | Ja |
| Rechnung bezahlt | POST /api/admin/invoices/{id}/mark-paid | BillingService Sync | `payment_completed` | Ja |
| Zahlungserinnerung | Scheduler 09:00 | Worker: `payment_reminder` | Timeline | — |
| Mahnstufe | Scheduler 10:00 | Worker: `dunning_escalation` | Timeline + Alert | — |
| Lead-Follow-up | Scheduler 08:30 | Worker: `lead_followup` | Timeline | — |
| Terminerinnerung | Scheduler 4h | Worker: `booking_reminder` | Timeline | — |
| Angebotsablauf | Scheduler 12h | Worker: `quote_expiry` | Timeline | — |
| Health-Check | Scheduler 30min | Timeline | Timeline | — |
| Outbound-Discover | POST /api/admin/outbound/discover | OutboundLeadMachine | Timeline | — |
| Outbound-Outreach | POST /api/admin/outbound/{id}/outreach/{id}/send | Worker: `send_email` | Timeline | — |
| Payment-Webhook | POST /api/webhooks/revolut | BillingService (idempotent) | Timeline | — |

### 1.5 Monitoring-Endpunkte

| Endpunkt | Funktion |
|----------|----------|
| `GET /api/health` | Basis-Healthcheck |
| `GET /api/admin/audit/health` | Erweiterter System-Health |
| `GET /api/admin/workers/status` | Worker-Queue + Scheduler Status |
| `GET /api/admin/workers/jobs` | Job-Liste mit Filter |
| `GET /api/admin/workers/dead-letter` | Dead-Letter-Queue |
| `POST /api/admin/workers/retry/{id}` | Dead-Letter-Job manuell wiederholen |
| `GET /api/admin/llm/status` | LLM-Provider-Status |
| `GET /api/admin/outbound/stats` | Outbound-Pipeline-Statistiken |

### 1.6 Self-Healing & Fallback

| Szenario | Verhalten |
|----------|-----------|
| Job fehlgeschlagen | 3x Retry mit exp. Backoff → Dead-Letter → Alert |
| Email-Versand fehlgeschlagen | Worker-Retry (3x) → Dead-Letter → Audit |
| LLM-Key fehlt | Health-Check meldet "missing", Chat-Fallback |
| MongoDB nicht erreichbar | Health-Check "error", Supervisor-Auto-Restart |
| Rate-Limit | HTTP 429, automatische Sperre |
| Token abgelaufen | HTTP 401/403, Client-Redirect zu /login |
| Scheduler-Fehler | Logger + Timeline `scheduler_error` |
| Dead-Letter-Häufung | Alert alle 2h in Timeline |

### 1.7 Behobene Restrisiken

| Restrisiko (vorher) | Lösung (jetzt) | Status |
|---------------------|-----------------|--------|
| Kein separater Background-Worker | JobQueue mit 4 asyncio-Workern, entkoppelt vom Request | VERIFIZIERT |
| Kein Mahnwesen-Cron | Scheduler: payment_reminders (09:00) + dunning_stages (10:00) | VERIFIZIERT |
| Kein Follow-up-Cron | Scheduler: lead_followups (08:30) | VERIFIZIERT |
| Kein Booking-Reminder | Scheduler: booking_reminders (alle 4h) | VERIFIZIERT |
| Email im Request-Thread | Über JobQueue Worker: `send_email` entkoppelt | VERIFIZIERT |

### 1.8 Verbleibende Restrisiken

- Worker-Pool läuft im selben Prozess (nicht multi-process) — für aktuelle Last ausreichend, bei Skalierung auf Redis/Celery migrieren
- Scheduler-State nicht persistent über Restart (APScheduler In-Memory) — Jobs werden bei Neustart sofort re-registriert
- Kein Webhook-Retry für eingehende WhatsApp-Messages

---

## 2. KI-Orchestrator — Architektur

### 2.1 LLM-Abstraktionsschicht (NEU)

```
LLMProvider (Abstract Base Class)
├── EmergentGPTProvider  (TEMPORÄR — AKTIV)
│   └── GPT-5.2 via Emergent LLM Key
└── DeepSeekProvider     (ZIEL — VORBEREITET)
    └── DeepSeek API (deepseek-chat)
```

**Migration zu DeepSeek:**
1. `DEEPSEEK_API_KEY` in `/app/backend/.env` setzen
2. `LLM_PROVIDER=deepseek` in `.env` setzen
3. System-Prompts optimieren
4. Regressionstests durchführen

**Status:** `GET /api/admin/llm/status` zeigt aktuellen Provider

### 2.2 Agent-Architektur

```
Orchestrator (via LLMProvider)
├── intake_agent      — Leadaufnahme, Discovery, Klassifikation
├── research_agent    — Firmenanalyse, Lead-Enrichment
├── outreach_agent    — Erstansprache, Follow-ups
├── offer_agent       — Angebotserstellung, Tarifberatung
├── planning_agent    — Projektplanung, Architektur
├── finance_agent     — Rechnungsstellung, Zahlungen
├── support_agent     — Kundenbetreuung, Problemlösung
├── design_agent      — Design-Konzeption, SEO
└── qa_agent          — Qualitätssicherung, Audit
```

### 2.3 Guardrails

- Dedizierter System-Prompt pro Agent (`/app/backend/agents/`)
- Routing-Logik im Orchestrator
- Memory-Pflicht: read() vor Arbeit, write() nach Änderung
- Audit-Trail pro Execution
- Agenten empfehlen Aktionen, Business-Logik liegt in API-Endpunkten
- Keine neue Fachlogik direkt an den temporären Provider koppeln

---

## 3. Kanalübergreifender Kommunikationskern (NEU)

### 3.1 Architektur

```
CommunicationService (Single Source of Truth)
├── Kontakt-Management (Unified Identity via E-Mail)
├── Konversation-Management (Cross-Channel Threads)
├── Message-Management (Kanalübergreifende Historisierung)
├── Cross-Channel Routing (AI/Admin/Eskalation)
├── Entity-Verknüpfung (Quote, Invoice, Booking, Project)
└── Kanalübergreifende Timeline
```

### 3.2 Kanäle

| Kanal | Direction | Routing | Format |
|-------|-----------|---------|--------|
| Website-Chat | Inbound/Outbound | AI → Admin Eskalation | Rich Text/Markdown |
| E-Mail | Inbound/Outbound | Worker-Queue | HTML |
| WhatsApp | Inbound/Outbound | QR-Bridge | Plain Text (max 4096) |
| Kundenportal | Inbound/Outbound | JWT-Auth | HTML |
| Admin | Outbound | Direkt | HTML |
| System | Outbound | Automatisch | HTML |

### 3.3 Routing-Regeln

- Bestehende Kunden → Hohe Priorität
- Eskalations-Keywords (beschwerde, inkasso, anwalt, kündigung) → Admin
- Standard → AI-Routing

### 3.4 API-Endpunkte

| Endpunkt | Funktion |
|----------|----------|
| `GET /api/admin/comms/contacts/{email}` | Kontakt + Konversationen + Timeline |
| `GET /api/admin/comms/conversations/{id}/messages` | Kanalübergreifende Nachrichten |
| `POST /api/admin/comms/conversations/{id}/send` | Nachricht senden |
| `POST /api/admin/comms/conversations/{id}/assign` | Konversation zuweisen |
| `GET /api/admin/comms/timeline/{contact_id}` | Kanalübergreifende Timeline |

---

## 4. Outbound Lead Machine (NEU)

### 4.1 Pipeline

```
Discovery → Vorqualifizierung → Analyse & Scoring →
Legal Gate → Outreach → Follow-up → Übergabe
```

### 4.2 Fit-Scoring

| Produkt | Kriterien | Score-Gewichtung |
|---------|-----------|-----------------|
| Starter AI Agenten AG | Handwerk, Beratung, Agentur; keine Website, kein CRM | 1.0x |
| Growth AI Agenten AG | Technologie, SaaS, E-Commerce; Skalierung, KI-Strategie | 1.5x |

### 4.3 Legal Gate

- Opt-Out/Suppression-Check
- Doppel-Check: bereits Kunde/Lead?
- UWG § 7: Industry + Fit-Score Minimum
- DSGVO Art. 6 Abs. 1 lit. f: Dokumentierte Analyse erforderlich
- Keine Ansprache ohne Analyse und Fit ≥ 40

### 4.4 API-Endpunkte

| Endpunkt | Funktion |
|----------|----------|
| `GET /api/admin/outbound/leads` | Outbound-Leads mit Filter |
| `GET /api/admin/outbound/stats` | Pipeline-Statistiken |
| `POST /api/admin/outbound/discover` | Lead erfassen |
| `POST /api/admin/outbound/{id}/prequalify` | Vorqualifizierung |
| `POST /api/admin/outbound/{id}/analyze` | Analyse + Scoring |
| `POST /api/admin/outbound/{id}/legal-check` | Legal Gate |
| `POST /api/admin/outbound/{id}/outreach` | Outreach erstellen |
| `POST /api/admin/outbound/{id}/outreach/{oid}/send` | Outreach versenden |
| `POST /api/admin/outbound/{id}/followup` | Follow-up planen |
| `POST /api/admin/outbound/opt-out` | Suppression-Liste |

---

## 5. Billing / Offer-to-Cash (NEU)

### 5.1 Status-Sync-Modell

```
Quote (draft→sent→viewed→accepted/declined/expired)
    ↓ (accepted)
Invoice (draft→sent→paid/overdue/cancelled)
    ↓ (sent)
Payment (unpaid→reminder_1→reminder_2→reminder_3→dunning_1→dunning_2→dunning_3)
    ↓ (webhook/manual)
Reconciliation (paid→synced)
```

### 5.2 API-Endpunkte

| Endpunkt | Funktion |
|----------|----------|
| `GET /api/admin/billing/status/{email}` | Gesamter Billing-Status |
| `POST /api/admin/billing/sync-quote/{id}` | Quote-Status synchronisieren |
| `POST /api/admin/billing/sync-invoice/{id}` | Invoice-Status synchronisieren |

---

## 6. Email-Signatur & DSGVO-Footer

(unverändert — zentral über `email_template()`)

---

## 7. Kommerzielle Source of Truth

| Tarif | Kennung | Preis | Laufzeit | Anzahlung |
|-------|---------|-------|----------|-----------|
| Starter AI Agenten AG | NXA-SAA-24-499 | 499 EUR/Mo | 24 Mo | 30% = 3.592,80 EUR |
| Growth AI Agenten AG | NXA-GAA-24-1299 | 1.299 EUR/Mo | 24 Mo | 30% = 9.352,80 EUR |

---

## 8. Code-Architektur

```
/app/backend/
├── server.py           (FastAPI, CRUD, Auth, >4100 Zeilen — Refactoring P6)
├── commercial.py       (PDF-Generierung, Tarif-Source-of-Truth)
├── domain.py           (Domain-Models, Enums)
├── memory_service.py   (mem0 Wrapper, Agent-IDs)
├── agents/             (9 Sub-Agenten + Orchestrator)
├── workers/            (NEU)
│   ├── __init__.py
│   ├── job_queue.py    (Async JobQueue, Retry, Dead-Letter)
│   ├── scheduler.py    (APScheduler Cron-Jobs)
│   ├── handlers.py     (Job-Handler Business-Logik)
│   └── manager.py      (WorkerManager Lifecycle)
├── services/           (NEU)
│   ├── __init__.py
│   ├── comms.py        (Kanalübergreifender Kommunikationskern)
│   ├── billing.py      (Offer-to-Cash Status-Sync)
│   ├── outbound.py     (Outbound Lead Machine + Legal Gate)
│   └── llm_provider.py (LLM-Abstraktionsschicht)
└── tests/
```
