# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Fully premium, highly secure architecture with D/A/CH localization (EUR only, no $). CI design system relying strictly on "Dutch Orange" (#FF6B00) and White.

## Core Requirements
- Unified Login Stack with strict role separation (Admin/Customer)
- Contract Operating System (master contracts, modular appendices, digital acceptance)
- Unified Communication (LiveChat, Booking, Contact Forms)
- Background Worker/Scheduler Layer (APScheduler)
- KI-Orchestrator: NeXify AI Master (Arcee trinity-large-preview + mem0 Brain)
- Multi-language support: DE/NL/EN
- Legal compliance: D/A/CH (7 docs x 3 langs = 21 routes)
- External API v1 with API-Key authentication

## Architecture
- Frontend: React 18 SPA
- Backend: FastAPI (Python) with modular routes
- Database: MongoDB
- Auth: JWT + Magic Links (internal), API Keys (external)
- LLM: Arcee AI (trinity-large-preview) via OpenAI-compatible API
- Memory: mem0 Brain (user_id: pascal-courbois, agent_id: nexify-ai-master)
- Workers: APScheduler
- CI: Dutch Orange (#FF6B00) and White only

## What's Been Implemented

### Completed (verified via testing)
- [x] Worker/Scheduler-Layer (APScheduler, Queue, Dead-letter)
- [x] Services scaffolding (comms, outbound, billing, llm_provider)
- [x] Public Auth Security
- [x] Hero 3D Scene + Design/Brand Harmonization
- [x] Admin Sidebar + Customer Portal Sidebar (collapsed, tooltips)
- [x] Customer Portal Active Features
- [x] P0 Comprehensive Legal Texts (21 routes) — Iter 62
- [x] P1 TrustSection i18n Bug Fix + enhanced copy — Iter 63
- [x] External API v1 with API-Key Authentication — Iter 64
- [x] NeXify AI Master Chat Interface — Iter 65
  - Arcee AI (trinity-large-preview) streaming SSE
  - mem0 Brain integration (search + store)
  - Full system prompt (Orchestrator, Company knowledge, Tarife)
  - Conversation persistence in MongoDB
  - Admin UI: Chat, Conversation sidebar, Brain toggle, Quick actions

### Backlog (Priority Order)
- [ ] DeepSeek Live-Migration (replace GPT-5.2 mock)
- [ ] Projektchat / Build-Handover-Kontext härten
- [ ] Revolut/Stripe Live-Webhooks & Billing-Status-Sync
- [ ] Legal & Compliance Guardian (operative wiring)
- [ ] Outbound Lead Machine (production readiness)
- [ ] server.py modular refactoring (AFTER all features stable)
- [ ] Next.js Migration (target architecture)
- [ ] PydanticAI + LiteLLM + Temporal Adoption

## External API v1
- Base URL: /api/v1, Auth: X-API-Key header
- Endpoints: /health, /docs, /stats, /contacts, /leads, /quotes, /contracts, /projects, /invoices, /webhooks

## NeXify AI Master
- Route: /api/admin/nexify-ai/chat (SSE streaming)
- LLM: Arcee AI trinity-large-preview
- Memory: mem0 Brain (pascal-courbois / nexify-ai-master / nexify-automate-core)
- Features: Conversations CRUD, Memory search/store, Brain toggle, Quick actions

## Key DB Collections
projects, contracts, documents, webhook_events, outbound_leads, contacts, api_keys, webhooks, nexify_ai_conversations, nexify_ai_messages

## Testing History
- Iteration 60: Admin Sidebar (100%)
- Iteration 61: Customer Portal (100%)
- Iteration 62: Legal Pages (100%)
- Iteration 63: TrustSection i18n Fix (100%)
- Iteration 64: External API v1 (100%, 24/24)
- Iteration 65: NeXify AI Master (100%, 15/15 backend + all frontend)
