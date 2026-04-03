# NeXifyAI — Product Requirements Document

## Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator (DeepSeek Ziel), Manuelles CRM, Gemeinsamer Login-Stack, Dynamische Floating Actions, Worker/Scheduler-Layer, Kanalübergreifender Kommunikationskern, Outbound Lead Machine, Offer-to-Cash Billing-Sync.

## Architecture
- **API-First**: Domain → Channel → Connector → Agent → Event/Audit Layer
- **Unified Auth**: /login → Admin (Passwort) / Kunde (Magic Link) → Role-based JWT
- **mem0 Memory Layer**: Pflicht-Scoping (user_id, agent_id, app_id, run_id)
- **LLM-Abstraktionsschicht**: EmergentGPTProvider (TEMPORÄR) | DeepSeekProvider (ZIEL)
- **Worker/Scheduler**: asyncio JobQueue (4 Worker) + APScheduler (7 Cron-Jobs)
- **Services**: CommunicationService, BillingService, OutboundLeadMachine

## What's Implemented & Verified

### Auth & Login — VERIFIZIERT
- Login-Button im Public Header (Desktop/Tablet/Mobile, i18n DE/NL/EN)
- /login als allgemeine Auth-Seite (Home-Link, Legal: Impressum/Datenschutz/AGB)
- Admin-Flow (E-Mail → Rollen-Badge → Passwort → /admin)
- Kunden-Flow (E-Mail → Magic Link → /portal)
- JWT Rollentrennung (admin/customer), serverseitig + UI-seitig

### Admin CRM — VERIFIZIERT
- Vollständige Arbeitsoberfläche: Leads/Kunden/Angebote/Rechnungen/Termine CRUD
- Rabatt, Sonderpositionen, Status, Notizen, Audit-Trail
- KI-Agenten-Steuerung, Kommunikation, Timeline

### Customer Portal — VERIFIZIERT
- JWT-Auth + Legacy Magic Link, Dashboard mit Angeboten/Rechnungen/Terminen
- Logout, Login-Link bei Fehler

### Mobile Floating Actions — VERIFIZIERT
- Dynamisch: Cookie → bottom:120px, kein Cookie → bottom:24px (Delta 96px bewiesen)
- CSS transition 0.4s, z-index 910, Safe-Area iOS

### Kommerzielle Konsistenz — VERIFIZIERT (Code)
- Rabatt + Sonderpositionen in Quote-PDF und Invoice-PDF

### Email-Signatur & DSGVO — VERIFIZIERT
- Zentrale email_template() mit Signatur + DSGVO-Footer

### mem0 Memory Layer — VERIFIZIERT
- MemoryService, 13 Agent-IDs, Pflicht-Scoping

### P0: Worker/Scheduler-Layer — VERIFIZIERT (Iteration 25: 100%)
- **JobQueue**: asyncio PriorityQueue, 4 Worker, MongoDB-Persistenz
- **Retry**: Exponentieller Backoff (10s→5min), max 3 Versuche
- **Dead-Letter-Queue**: Nach 3 Fehlversuchen, manuelles Retry möglich
- **Crash-Recovery**: Unfertige Jobs aus DB wiederhergestellt bei Neustart
- **8 Handler**: send_email, payment_reminder, dunning_escalation, lead_followup, booking_reminder, quote_expiry, ai_task, status_transition
- **7 Scheduler-Jobs**: Zahlungsreminder (09:00), Mahnvorstufen (10:00), Lead-Follow-ups (08:30), Buchungserinnerungen (4h), Angebotsablauf (12h), Health-Check (30min), Dead-Letter-Alert (2h)
- **Monitoring**: /api/admin/workers/status, /jobs, /dead-letter, /retry/{id}
- Status: Alle Endpoints getestet, 401 ohne Auth, Business-Logik verifiziert

### P1: Kanalübergreifender Kommunikationskern — VERIFIZIERT (Iteration 25: 100%)
- **CommunicationService**: Single Source of Truth für alle Kanäle
- **Unified Identity**: Kontakt-Deduplizierung via E-Mail
- **Cross-Channel Threads**: Eine Konversation, mehrere Kanäle
- **Routing**: AI/Admin/Eskalation basierend auf Keywords und Kundenstatus
- **Entity-Verknüpfung**: Quote, Invoice, Booking, Project
- **API**: /api/admin/comms/contacts/{email}, conversations/{id}/messages, /send, /assign, /timeline

### P2: Outbound Lead Machine — VERIFIZIERT (Iteration 25: 100%)
- **Pipeline**: Discovery → Vorqualifizierung → Analyse → Scoring → Legal Gate → Outreach → Follow-up
- **Fit-Scoring**: Automatisch gegen Starter/Growth-Produkte, gewichtet
- **Legal Gate**: Opt-Out, Suppression, UWG § 7, DSGVO Art. 6 Abs. 1 lit. f
- **Suppression-Liste**: Opt-Out-Logik mit automatischer Lead-Sperrung
- **API**: discover, prequalify, analyze, legal-check, outreach, send, followup, opt-out, leads, stats

### P3: Billing/Status-Sync (Basis) — VERIFIZIERT (Iteration 25: 100%)
- **BillingService**: Quote→Invoice→Payment Status-Sync
- **Webhook-Verarbeitung**: Idempotent (Revolut, Stripe, manuell)
- **Reconciliation**: Gesamtbilling-Status pro Kontakt
- **API**: billing/status/{email}, sync-quote/{id}, sync-invoice/{id}

### P5: LLM-Abstraktionsschicht — VERIFIZIERT (Iteration 25: 100%)
- **Provider-agnostisch**: LLMProvider ABC → EmergentGPTProvider / DeepSeekProvider
- **Factory**: create_llm_provider() — automatische Erkennung via ENV
- **Migration**: DEEPSEEK_API_KEY + LLM_PROVIDER=deepseek in .env → sofort aktiv
- **Status**: /api/admin/llm/status zeigt Provider + Ziel-Architektur

## Testing Status
- Iteration 21-24: 100% (Auth, CRM, Portal, Floating, PDF)
- Iteration 25: 100% — 30/30 Tests (Worker, Comms, Outbound, Billing, LLM)

## Remaining Tasks
- P4: Projektchat/Handover-Kontext härten (Scope, Discovery, Status, Angebote, Rechnungen)
- P6: server.py Refactoring (>4100 Zeilen → modulare Routen/Services)
- Revolut-Webhook Live-Integration (braucht Live-Keys)
- Stripe-Integration (Keys vorhanden, Integration ausstehend)
- DeepSeek Live-Migration (Key vorhanden, Integration vorbereitet)
- Login-Page Security by Obscurity (Admin-Terminologie aus Public entfernen)
- Mobile Menu Overlay Fix (Backdrop-Blur, doppelter Language Switcher)

## Commercial Source of Truth
| Tarif | Kennung | Preis | Laufzeit | Anzahlung |
|-------|---------|-------|----------|-----------|
| Starter AI Agenten AG | NXA-SAA-24-499 | 499 EUR/Mo | 24 Mo | 30% = 3.592,80 EUR |
| Growth AI Agenten AG | NXA-GAA-24-1299 | 1.299 EUR/Mo | 24 Mo | 30% = 9.352,80 EUR |
