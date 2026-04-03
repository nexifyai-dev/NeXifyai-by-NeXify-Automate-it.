# NeXifyAI — Product Requirements Document

## Originalauftrag
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium, hochsichere Architektur. Unified Login Stack, Worker/Scheduler Layer, Admin/Agenten strikt nicht öffentlich. Ziel-LLM: DeepSeek.

## Architektur
```
/app/
├── backend/
│   ├── server.py (FastAPI, >5500 Zeilen)
│   ├── commercial.py (PDF-Generation, Tarife)
│   ├── domain.py (Datenmodelle, Enums, Factories)
│   ├── memory_service.py (mem0-Integration)
│   ├── services/
│   │   ├── billing.py (BillingService)
│   │   ├── comms.py (CommunicationService)
│   │   ├── outbound.py (OutboundLeadMachine)
│   │   ├── llm_provider.py (LLM-Abstraktionsschicht)
│   │   └── legal_guardian.py (Legal & Compliance Guardian)
│   ├── workers/
│   │   ├── manager.py
│   │   ├── job_queue.py
│   │   └── scheduler.py
├── frontend/
│   ├── src/
│   │   ├── App.js & App.css
│   │   ├── pages/Admin.js, CustomerPortal.js, UnifiedLogin.js
│   │   └── components/Scene3D.js
```

## Tarife (Commercial Source of Truth)
- Starter AI Agenten AG — NXA-SAA-24-499 — 499 EUR/Monat — 24 Monate — 30% Anzahlung 3.592,80 EUR
- Growth AI Agenten AG — NXA-GAA-24-1299 — 1.299 EUR/Monat — 24 Monate — 30% Anzahlung 9.352,80 EUR

## DB-Schema (MongoDB)
leads, customers, quotes, invoices, bookings, timeline_events, customer_memory, messages, conversations, projects, project_sections, project_chat, project_versions, contracts, contract_appendices, contract_evidence, webhook_events, legal_audit, legal_risks, opt_outs, suppression_list, outbound_leads, access_links, documents

## Implementiert (P0–P6)

### P0: Architektur & Design (verifiziert)
- Worker/Scheduler Layer (APScheduler)
- Services-Scaffolding
- Auth Security by Obscurity
- 3D Hero, Design-Harmonisierung

### P1: Projektchat / Build-Handover-Kontext (verifiziert — Iteration 28)
- 22 Pflicht-Sektionen mit Versionierung
- Projektchat (Admin + Kunden)
- Build-Ready-Markdown-Generierung
- Startprompt-Generierung aus Kontext (geheim)
- Vollständigkeits-Tracking (%)
- Memory/Audit-Integration

### P2: Contract Operating System v1 (verifiziert — Iteration 29)
- Mastervertrag + 7 Anlagetypen
- 3 Vertragstypen (Standard/Individual/Nachtrag)
- Digitale Annahme (Signatur + Namenseingabe)
- Evidenzpaket (Timestamp, IP, UA, Hash, Version, Consent)
- 6 Rechtsmodule (4 Pflicht, 2 optional)
- Ablehnung / Änderungsanfrage / Versionierung
- Admin-UI + Kunden-Portal

### P3: Billing/Webhooks produktionsnah (verifiziert — Iteration 30)
- Revolut + Stripe Webhooks (idempotent)
- Manuelle Zahlungsbestätigung
- Reminder/Mahnlogik (3 Eskalationsstufen)
- Billing-Status-Dashboard
- Status-Sync: Quote ↔ Invoice ↔ Contract ↔ Timeline

### P4: Legal & Compliance Guardian (verifiziert — Iteration 31)
- 10 Compliance-Checks (DSGVO, UWG, KI-Transparenz, etc.)
- 4 Gate-Prüfungen (Outreach, Vertrag, Kommunikation, Billing)
- Risikomanagement (Add/Resolve/List)
- Audit-Log
- Opt-Out (Admin + Public)
- Operativ an Vertragsversand gekoppelt

### P5: DeepSeek Live-Pfad (teilweise verifiziert — Iteration 32)
- DeepSeekProvider mit httpx, Fehlerbehandlung
- ENV-basierte Umschaltung (auto/deepseek/emergent)
- Provider-Status und Test-Endpoint
- Model-Auswahl (deepseek-chat, deepseek-reasoner)
- DEEPSEEK_API_KEY nicht gesetzt → Emergent-Fallback aktiv

### P6: Outbound Lead Machine (verifiziert — Iteration 32)
- 16-stufige Pipeline (Discovery → Handover)
- Legal-Guardian-Gate im Send-Flow
- Response-Tracking (positive/negative/opt_out)
- Handover (Quote/Meeting/Nurture)
- CRM-Lead-Erstellung bei Quote-Handover
- Pipeline-Übersicht mit Konversionsraten

## Nächste Schritte

### P7: server.py Modular Refactoring (ERST NACH P1–P6 STABIL)
- auth_routes.py, workers_routes.py, billing_routes.py, outbound_routes.py, comms_routes.py, portal_routes.py, contract_routes.py, monitoring_routes.py
- Keine Regression, bestehende APIs stabil halten
- Tests/Imports/Abhängigkeiten nachziehen

## Offene Punkte
- DEEPSEEK_API_KEY: Vom Kunden zu konfigurieren
- Revolut/Stripe Live-Keys: Benötigen Produktions-Credentials
- Resend E-Mail: Konfiguriert, funktioniert
- Kunden-Portal: Vertragsprüfung + Signatur-Canvas (Touch/Maus) noch zu implementieren
