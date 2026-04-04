# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium, hochsichere Architektur. Autopilot-Direktive: Alle Vorgaben gesammelt, strukturiert, Gesamtbild verstanden, komplett umgesetzt.

## Tech Stack
- **Frontend**: React 18 SPA (CRA), ErrorBoundary, ContractAcceptance page
- **Backend**: FastAPI (Python), modular routing, Global Exception Handler
- **Database**: MongoDB — 30+ Indexes (inkl. sparse)
- **Auth**: JWT (24h), Dual-Role, OAuth2
- **Workers**: APScheduler (8 Job-Typen, Dead-Letter Queue)
- **Email**: Hostinger SMTP
- **LLM**: DeepSeek (Target) → Emergent GPT-5.2 mock (aktiv)
- **Payments**: Revolut ONLY
- **Security**: HSTS, X-Frame-Options DENY, Rate Limiting 200/min, CORS Origins

## Go-Live Status: APPROVED (Iteration 58)

### Vollständig Verifizierte Geschäftsprozesse

**E2E Outbound Pipeline:**
Discover → Prequalify → Analyze & Score → Legal-Check → Outreach → Send → Respond → Handover → CRM

**E2E Contract Lifecycle:**
Create (mit Titel + Kalkulation) → Add Appendix → Send (Magic Link) → Customer View → Legal Accept → Digital Signature → Evidence Package → Status: Accepted

**E2E Öffentliche Vertragsannahme:**
`/vertrag?token=xxx&cid=xxx` → Contract View → Legal Modules (4 Pflicht) → Signature (Name/Zeichnung) → Accept → Evidenzpaket (IP, UserAgent, DocHash, Timestamp)

### Architecture Blocks (Alle VERIFIZIERT)

| Block | Beschreibung | Status |
|-------|-------------|--------|
| A | Public Website (3D Hero, Services, Legal Pages, Booking) | VERIFIZIERT |
| B | Customer Portal (10 Tabs: Übersicht, Verträge, Projekte, Finanzen, Dokumente, Settings, Consents) | VERIFIZIERT |
| C | Admin Panel (19-21 Navigation Views, Full CRUD) | VERIFIZIERT |
| D | Admin Governance (User Mgmt, Webhook Store, Audit, Monitoring) | VERIFIZIERT |
| E | Outbound Lead Machine (Full Pipeline, Bulk Import, Filter) | VERIFIZIERT |
| F | Backend Infrastructure (10 Route-Module, Workers, Timeline, Legal Audit) | VERIFIZIERT |
| G | Production Hardening (CORS, HSTS, Rate Limiting, ErrorBoundary, Exception Handler) | VERIFIZIERT |

### Key API Endpoints
- POST /api/admin/login (OAuth2)
- GET/POST /api/admin/outbound/* (Full pipeline)
- GET/POST /api/admin/projects/*, /api/admin/contracts/*
- GET /api/admin/stats, /billing/status, /legal/compliance, /monitoring/status
- GET/POST /api/admin/users, DELETE /api/admin/users/{email}
- GET /api/admin/webhooks/events
- GET/PATCH /api/customer/profile, /documents, /consents
- **NEW: GET /api/public/contracts/view?token=&cid= (kein Auth)**
- **NEW: POST /api/public/contracts/accept (kein Auth, Token-basiert)**

### Testing History
- Iteration 55: 100% (Outbound, Projects, Contracts)
- Iteration 56: 100% (User Mgmt, Webhooks, Security)
- Iteration 57: 100% (ErrorBoundary, Exception Handler, Indexes)
- **Iteration 58: 100% (E2E Contract Acceptance, Kalkulation, Public Endpoints)**

## Test Credentials
- Admin: p.courbois@icloud.com / 1def!xO2022!!

## MOCKED: DeepSeek → Emergent GPT-5.2

## Post-Go-Live Backlog
- [ ] DeepSeek Live-Migration (DEEPSEEK_API_KEY)
- [ ] Content & Copywriting Overhaul
- [ ] server.py modular refactoring
- [ ] Next.js Migration
- [ ] PydanticAI + LiteLLM + Temporal
