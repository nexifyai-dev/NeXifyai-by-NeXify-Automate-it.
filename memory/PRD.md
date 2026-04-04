# NeXifyAI — Product Requirements Document

## Originaler Auftrag
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium-Architektur mit absolutem Fokus auf Produktionsreife, Sicherheit und System-Konsistenz.

## Architektur
- **Frontend**: React 18 SPA, Framer Motion, i18n (DE/NL/EN), Shadcn-Style Dark Theme
- **Backend**: FastAPI (modular: 10 Route-Module), APScheduler, MongoDB
- **Workers**: In-process JobQueue (Retry + Dead-Letter), Cron-Scheduler (7 Jobs)
- **LLM**: DeepSeek (Primär), GPT-5.2 Fallback via Emergent
- **Integrations**: Stripe, Object Storage, Resend (E-Mail)
- **Security**: JWT Auth, Rate Limiting (SlowAPI), Security Headers, CORS

## Implementierte Features

### Backend
- Modulare Route-Architektur (auth, public, admin, billing, portal, comms, contract, project, outbound, monitoring)
- Worker/Scheduler-Layer: 8 Handler (email, payment_reminder, dunning, lead_followup, booking_reminder, quote_expiry, ai_task, status_transition)
- 7 Scheduler-Jobs (Cron: Zahlungsreminder, Mahnungen, Follow-ups, Buchungserinnerungen, Angebotsablauf, Health-Check, Dead-Letter-Alert)
- Oracle/Memory Service: write_classified, get_contact_oracle(), Oracle Snapshot
- Billing Overview Dashboard API
- Outbound Campaigns API
- Monitoring Aliases (health, workers)
- Memory Stats API
- Rate Limiting (SlowAPI 200/min global)
- Triple-secured action logic (MongoDB + Timeline + Memory Audit)

### Frontend
- Unified Login (2-Spalten Premium)
- Landing Page: 12 Sektionen (Hero, Solutions, UseCases, AppDev, Process, Integrations, Governance, Pricing, SEO, Services, Trust, FAQ, Contact)
- Standalone Termin-Seite (/termin) — Premium 2-Spalten-Layout mit Trust-Signalen
- BookingModal (2-Step: Datum → Details)
- LiveChat mit KI-Backend
- Legal Pages (Impressum, Datenschutz, AGB, KI-Hinweise) — 3 Sprachen
- Animated Pricing mit Custom Quote Request
- Customer Portal, Admin Dashboard, Quote Portal

## Key API Endpoints
- `/api/health` — System Health
- `/api/auth/login` — Admin JWT Login
- `/api/booking` — Terminbuchung
- `/api/contact` — Kontaktformular
- `/api/chat/message` — KI-Chat
- `/api/quote/request` — Custom Angebotsanfrage
- `/api/admin/billing/overview` — Billing-Dashboard
- `/api/admin/outbound/campaigns` — Outbound-Kampagnen
- `/api/admin/oracle/snapshot` — Oracle IST-Stand
- `/api/admin/oracle/contact/{id}` — Kontakt-Oracle
- `/api/admin/memory/stats` — Memory-Statistiken
- `/api/admin/monitoring/health` — System-Gesundheit
- `/api/admin/monitoring/workers` — Worker-Status

## DB-Schema
leads, customers, quotes, invoices, bookings, contracts, projects, timeline_events, customer_memory, messages, chat_sessions, conversations, documents, audit_log, legal_audit, webhook_events, jobs, outbound_leads

## Testing Status
- Iteration 48: 100% (30/30 Backend + Frontend) — verifiziert
- Alle Admin-Endpunkte: 200 ✅
- Worker: 4 aktiv, 7 Scheduler-Jobs ✅
- Oracle: Operational ✅
- Rate Limiting: Aktiv ✅

## Nächste Schritte (Backlog)
1. **P2**: Content & Copywriting Overhaul — perfektionierte Texte für alle Flows
2. **P3**: Security Hardening — CORS-Einschränkung, Firewall-Regeln, Secrets-Audit
3. **P4**: E2E Browser-Verifikation aller kritischen Pfade (Quote → Invoice → Payment)
4. **P5**: DeepSeek Live-Migration (Concrete Routing, Tools, Memory)
5. **P6**: Legal & Compliance Guardian (Operative Verdrahtung)
6. **P7**: Outbound Lead Machine Härtung
7. **P8**: Next.js Migration (Target-Architektur)
8. **P9**: PydanticAI + LiteLLM + Temporal Adoption

## Credentials
- Admin: p.courbois@icloud.com / 1def!xO2022!!
