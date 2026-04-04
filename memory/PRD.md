# NeXifyAI — Product Requirements Document

## Originaler Auftrag
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium-Architektur mit absolutem Fokus auf Produktionsreife, Sicherheit und System-Konsistenz. Vollumfänglicher System-Audit mit 42-Sektionen-Systemprompt durchgeführt.

## Architektur
- **Frontend**: React 18 SPA, Framer Motion, i18n (DE/NL/EN), Shadcn-Style Dark Theme
- **Backend**: FastAPI (modular: 10 Route-Module), APScheduler, MongoDB
- **Workers**: In-process JobQueue (4 Workers, Retry + Dead-Letter), Cron-Scheduler (7 Jobs)
- **LLM**: DeepSeek (Primär, aktiv), GPT-5.2 Fallback via Emergent
- **Integrations**: Stripe, Object Storage, Resend (E-Mail)
- **Security**: JWT Auth, Rate Limiting (SlowAPI 200/min), Security Headers, CORS
- **Oracle**: Memory Service (178 Einträge), get_contact_oracle(), Snapshot

## Implementierte Features (kumulativ, verifiziert Iter. 48-50)

### Backend
- Modulare Route-Architektur (10 Route-Module: auth, public, admin, billing, portal, comms, contract, project, outbound, monitoring)
- Worker/Scheduler-Layer: 8 Handler, 7 Scheduler-Jobs
- Oracle/Memory Service: write_classified, get_contact_oracle(), Oracle Snapshot
- Billing Overview Dashboard, Outbound Campaigns, Monitoring Aliases, Memory Stats
- Rate Limiting (SlowAPI 200/min), Security Headers (CSP, X-Frame, XSS, Referrer, Permissions)
- Triple-secured action logic (MongoDB + Timeline + Memory Audit)
- QuoteRequest-Model (discount_percent, customer_industry, use_case, special_items)
- Invoice-aus-Quote (upfront_eur, auto-Beschreibung, Typ-Support activation/recurring)
- Contract-aus-Quote (auto-Populate Kundendaten, Tarif, Kalkulation)
- System Health Endpoint (Workers, Scheduler, Memory, DB, LLM, Agents)

### Frontend
- Landing Page: 12 Sektionen mit Premium Dark Theme
- Standalone Termin-Seite (/termin): 2-Spalten, Trust-Signale, i18n
- Unified Login: 2-Spalten, DSGVO-Checkbox, Trust-Row, Booking-CTA nach Registrierung
- BookingModal: 2-Step Premium
- LiveChat: KI-gestützt, responsive (Desktop + Mobile Full-Screen)
- Legal Pages: Impressum, Datenschutz, AGB, KI-Hinweise (DE/NL/EN)
- Animated Pricing mit Custom Quote Request
- Customer Portal: 8 Tabs (Übersicht, Verträge, Projekte, Angebote, Finanzen, Termine, Kommunikation, Aktivität), Mobile-optimierte Kurzlabels
- Admin Dashboard: System-Health-Panel (6 Karten), Lead-Management, Billing, CRM
- Quote Portal

## E2E-Prozesskette (verifiziert)
Lead → Booking → Quote → Invoice → Contract → Payment
- Contact-Formular → Lead ✅
- Termin-Buchung → Booking ✅
- KI-Chat → Response ✅
- Quote-Anfrage → Lead + Anfrage ✅
- Admin: Quote → Invoice (korrekte Beträge) ✅
- Admin: Quote → Contract (auto-populate) ✅

## Testing (3 Iterationen, alle 100%)
- Iteration 48: 30/30 Backend + Frontend ✅
- Iteration 49: 25/25 Backend + Frontend ✅
- Iteration 50: 35/35 Backend + Frontend ✅

## Dokumentation
- PRD.md (dieses Dokument)
- ROADMAP.md (Dynamische Bedarfsliste mit Prioritäten, Risiken, Monitoring-Status)
- DESIGN_SYSTEM.md (Farben, Typografie, Abstände, Radien, Motion, Breakpoints)
- test_credentials.md (Admin-Zugang)
- TECHNICAL_DOCS.md (Architektur-Details)

## Nächste Schritte (Backlog)
1. P0: Stripe Webhook-Integration, E-Mail-Benachrichtigungen, PDF-Generierung
2. P1: DeepSeek Live-Migration, Dunning Flow, Projekt-Chat mit Upload
3. P2: Content-Review, Onboarding-Flow, Umsatz-Charts
4. P3: Next.js Migration, PydanticAI, Database-Indexierung
5. P4: Legal Guardian, Cookie-Consent, AVV, Löschkonzept

## Credentials
- Admin: p.courbois@icloud.com / 1def!xO2022!!
