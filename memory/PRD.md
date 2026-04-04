# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium, hochsichere Architektur. Unified Login Stack, Worker/Scheduler Layer, Revolut-only Billing, Outbound Lead Machine, Contract OS. Autopilot-Direktive P0.10 bis P0.10.7 für vollumfängliche Produktion.

## Tech Stack
- **Frontend**: React 18 SPA (CRA), Shadcn/UI, ErrorBoundary
- **Backend**: FastAPI (Python), modular routing, Global Exception Handler
- **Database**: MongoDB (MONGO_URL) — 30+ optimierte Indexes
- **Auth**: JWT (24h), Dual-Role (Admin/Kundenportal), OAuth2 form-encoded
- **Workers**: APScheduler (8 Job-Typen, Dead-Letter Queue, 4 Worker-Threads)
- **Email**: Hostinger SMTP
- **LLM**: DeepSeek (Target) — routed through Emergent GPT-5.2 mock
- **Payments**: Revolut ONLY (Stripe komplett entfernt)
- **Storage**: emergentintegrations Object Storage
- **Security**: HSTS, X-Frame-Options DENY, CSP, Rate Limiting 200/min

## Architecture (Go-Live Verifiziert — Iteration 57)

### BLOCK A — Public Website (VERIFIZIERT)
3D Hero, Solutions, UseCases, Process, Governance, Pricing, FAQ, SEO, LiveChat, Booking, Cookie Consent, Legal Pages (Impressum, Datenschutz, AGB, KI-Hinweise), 3-Language Support (DE/NL/EN)

### BLOCK B — Customer Portal (VERIFIZIERT)
10 Tabs: Übersicht, Verträge, Projekte, Angebote, Finanzen, Dokumente, Termine, Kommunikation, Aktivität, Einstellungen. Profile-Bearbeitung, Dokumenten-Download, DSGVO-Einwilligungsverwaltung (Opt-In/Out), Contract Acceptance mit Digital Signature + Evidence Package

### BLOCK C — Admin Panel (VERIFIZIERT)
19 Navigation Views: Dashboard, Projekte, Verträge, Billing, Outbound, Legal, Angebote & Rechnungen, Leads, Kommunikation, KI-Chats, WhatsApp, Aktivitäten, Kalender, Kunden, KI-Agenten, Benutzer, Webhooks, Audit, Monitoring. Kunden-Fallakte mit Direct-Email

### BLOCK D — Admin Governance (VERIFIZIERT)
Admin User Management (CRUD, Selbstlöschung blockiert), Webhook Event Store (28+ Events), Audit Log, Legal & Compliance Guardian, System Monitoring (11 Subsysteme), Recovery & Self-Healing Panel

### BLOCK E — Outbound Lead Machine (VERIFIZIERT)
Full Pipeline: Discover → Prequalify → Analyze & Score → Legal-Check → Outreach → Send → Follow-up (3 Stufen) → Response → Handover (Angebot/Termin/Nurture). Bulk Import, Opt-Out, Pipeline-Visualisierung, Filter-System (35 Leads, 8.6% Conversion)

### BLOCK F — Backend Infrastructure (VERIFIZIERT)
10 Route-Module, 8 Worker-Job-Typen, Webhook Event Store, Timeline Events, Legal Audit, Customer Memory Service, Global Exception Handler (JSON statt HTML bei 500)

### BLOCK G — Production Hardening (VERIFIZIERT)
CORS Origins-Whitelist, HSTS (31536000s), X-Frame-Options DENY, X-Content-Type-Options nosniff, X-XSS-Protection, Permissions-Policy, Rate Limiting 200/min, MongoDB Sparse Indexes, React ErrorBoundary

## Key API Endpoints
POST /api/admin/login, GET /api/admin/stats, GET/POST /api/admin/users, DELETE /api/admin/users/{email}, GET /api/admin/webhooks/events, GET/POST /api/admin/outbound/*, GET/POST /api/admin/projects/*, GET/POST /api/admin/contracts/*, GET /api/admin/billing/status, GET /api/admin/legal/compliance, GET /api/admin/monitoring/status, GET/PATCH /api/customer/profile, GET /api/customer/documents, GET /api/customer/consents, POST /api/customer/consents/opt-out, POST /api/customer/consents/opt-in, GET /api/health

## DB Collections (22)
leads, contacts, customers, quotes, invoices, bookings, timeline_events, customer_memory, chat_sessions, outbound_leads, projects, project_sections, project_versions, project_chat, contracts, contract_appendices, contract_evidence, documents, admin_users, suppression_list, legal_audit, legal_risks, webhook_events, opt_outs, audit_log, analytics, messages, conversations, whatsapp_sessions

## Data Counts (Go-Live)
71 Leads, 27 Bookings, 3 Chat Sessions, 35 Outbound Leads, 7 Projekte, 43 Verträge, 1 Admin User, 28 Webhook Events

## Test Credentials
- Admin: p.courbois@icloud.com / 1def!xO2022!!

## Testing History
- Iteration 55: 100% (42/42)
- Iteration 56: 100% (23/23 backend, all frontend flows)
- Iteration 57: 100% — **FINAL GO-LIVE APPROVED** (20/20 backend, 19/19 admin views, all security verified)

## MOCKED: DeepSeek → Emergent GPT-5.2 Fallback

## Post-Go-Live Backlog
- [ ] DeepSeek Live-Migration (DEEPSEEK_API_KEY setzen)
- [ ] Content & Copywriting Overhaul
- [ ] E2E Browser Verifications (Quote → Invoice Durchlauf)
- [ ] server.py modular refactoring
- [ ] Next.js Migration
- [ ] PydanticAI + LiteLLM + Temporal
