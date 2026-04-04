# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Fully premium, highly secure architecture with D/A/CH localization (EUR only, no $). CI design system relying strictly on "Dutch Orange" (#FF6B00) and White.

## Core Requirements
- Unified Login Stack with strict role separation (Admin/Customer)
- Contract Operating System (master contracts, modular appendices, digital acceptance)
- Unified Communication (LiveChat, Booking, Contact Forms)
- Background Worker/Scheduler Layer (APScheduler)
- KI-Orchestrator (Target: DeepSeek, Current Mock: Emergent GPT-5.2)
- Multi-language support: DE/NL/EN
- Legal compliance: D/A/CH (Impressum, Datenschutz, AGB, KI-Hinweise, Widerruf, Cookies, AVV)

## Architecture
- Frontend: React 18 SPA
- Backend: FastAPI (Python) with modular routes
- Database: MongoDB
- Auth: JWT + Magic Links
- Workers: APScheduler
- CI: Dutch Orange (#FF6B00) and White only, no blue/coral/cheap SVGs

## What's Been Implemented

### Completed (verified via testing)
- [x] Worker/Scheduler-Layer (APScheduler, Queue, Dead-letter)
- [x] Services scaffolding (comms.py, outbound.py, billing.py, llm_provider.py)
- [x] Public Auth Security (Neutralizing /login, redirecting unauth /admin)
- [x] Mobile Menu Overlay & Floating Actions State Logic
- [x] Hero 3D Scene
- [x] System-wide Design/Brand Harmonization (all breakpoints)
- [x] Admin Sidebar (collapsed default, hover tooltips, CSS ::after)
- [x] Customer Portal Sidebar (collapsed default, hover tooltips)
- [x] Customer Portal Active Features (Requests, Bookings, Messages, Support Tickets)
- [x] P0 Comprehensive Legal Texts (7 docs x 3 langs = 21 routes) — Verified Iteration 62
- [x] P1 Content/Copywriting: TrustSection i18n bug fix + enhanced copy — Verified Iteration 63

### In Progress
- [ ] P2: DeepSeek Live-Migration (requires DEEPSEEK_API_KEY from user)

### Backlog
- [ ] Projektchat / Build-Handover-Kontext harten
- [ ] Revolut/Stripe Live-Webhooks & Billing-Status-Sync
- [ ] Legal & Compliance Guardian (operative wiring)
- [ ] Outbound Lead Machine (production readiness)
- [ ] server.py modular refactoring (AFTER all features stable)
- [ ] Next.js Migration (target architecture)
- [ ] PydanticAI + LiteLLM + Temporal Adoption

## Key DB Collections
projects, contracts, documents, webhook_events, outbound_leads, contacts

## Key API Endpoints
- /api/auth/login, /api/auth/verify-token, /api/auth/request-magic-link
- /api/customer/dashboard, /api/customer/requests, /api/customer/bookings
- /api/customer/messages, /api/customer/tickets, /api/customer/contracts
- /api/admin/* (protected)

## 3rd Party Integrations
- DeepSeek (Target Orchestrator) — requires User API Key
- Revolut (Payments/Webhooks) — requires User API Key
- Hostinger SMTP (Emails) — configured in .env
- Emergent GPT-5.2 (Current Mock) — uses EMERGENT_LLM_KEY

## Testing History
- Iteration 60: Admin Sidebar (100% Pass)
- Iteration 61: Customer Portal (100% Pass)
- Iteration 62: Legal Pages (100% Pass)
- Iteration 63: TrustSection i18n Fix (100% Pass)
