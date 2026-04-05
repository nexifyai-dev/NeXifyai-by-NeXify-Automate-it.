# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Fully premium, highly secure architecture with D/A/CH localization (EUR only, no $). CI design system: Coral accent (#FE9B7B) + White on dark background (#0c1117).

## Architecture
- Frontend: React 18 SPA | Backend: FastAPI (Python) | DB: MongoDB
- Auth: JWT + Magic Links (internal), API Keys (external)
- LLM: Arcee AI (trinity-large-preview) via OpenAI-compatible API
- Memory: mem0 Brain (pascal-courbois / nexify-ai-master / nexify-automate-core)
- Workers: APScheduler | Font: Manrope (primary) | CI: #FE9B7B + White

## What's Been Implemented

### Completed (all verified)
- [x] Worker/Scheduler-Layer (APScheduler)
- [x] Services scaffolding (comms, outbound, billing, llm_provider)
- [x] Public Auth Security + Hero 3D Scene
- [x] Design/Brand Harmonization — all breakpoints, Manrope font
- [x] Admin + Customer Portal Sidebars (collapsed, tooltips)
- [x] Customer Portal Active Features
- [x] Comprehensive Legal Texts (21 routes)
- [x] TrustSection i18n Fix
- [x] External API v1 (API Keys, 18+ endpoints)
- [x] NeXify AI Master Chat Interface (Arcee AI + mem0)
- [x] Color change #FF6B00 -> #FE9B7B
- [x] NeXify AI 37 operative Tools (CLI-first)
- [x] Chat Scroll Containment (adm-content--fullbleed, no outer scroll)
- [x] Chat Flickering Fix (Ref-based DOM streaming, no React state re-renders)
- [x] Server-side Tool Execution Loop (backend extracts/runs tools, streams follow-up)
- [x] Smart Scroll (auto-scroll only when near bottom)
- [x] Agent Settings UI (CRUD for all KI-Agenten)
- [x] Proactive/Autonomous Mode (4 scheduled tasks, manual trigger)
- [x] CSS Design Harmonization (unified h2/h3, tables, buttons, topbar, badges, spacing)

### Backlog
- [ ] DeepSeek Live-Migration (P1)
- [ ] Legal & Compliance Guardian (P2)
- [ ] Outbound Lead Machine hardening (P3)
- [ ] server.py modular refactoring (after P1-P3 stable)
- [ ] Next.js Migration
- [ ] PydanticAI + LiteLLM + Temporal Adoption

## NeXify AI Tools (37 total, CLI-first)
execute_shell (primary), list_contacts, create_contact, list_leads, create_lead, list_quotes, list_contracts, list_projects, list_invoices, system_stats, send_email, search_brain, store_brain, list_conversations, audit_log, list_api_keys, db_query, db_write, worker_status, timeline, web_search, http_request, scrape_url, execute_python, list_agents, create_agent, update_agent, delete_agent, invoke_agent, schedule_task, list_scheduled_tasks, delete_scheduled_task, read_file, write_file, list_files, self_status, update_config

## Proactive Tasks
- morning_briefing: Tägliches Briefing (08:00)
- lead_analysis: Wöchentliche Pipeline-Analyse (Mo 10:00)
- brain_maintenance: Wöchentliche Brain-Wartung (Fr 22:00)
- health_check: 4-stündlicher System-Check

## Design Tokens (Harmonized)
- h2: 1.125rem / 700 | h3: .9375rem / 700
- Topbar: 64px fixed height
- Table th: --nx-dim color (gray), 12px 16px padding
- Table td: 12px 16px padding, --text-secondary color
- Buttons primary: inline-flex, 10px 20px, .8125rem
- Font: Manrope, Plus Jakarta Sans, Inter
- Stat values: 1.75rem / 800

## Testing History
- Iteration 62-66: All 100% Pass
- Iteration 67: Chat Bug Fixes — 100% Pass (9/9 backend)
- Iteration 68: Agent CRUD + Chat — 100% Pass (13/13 backend)
- Iteration 69: Full Suite — 100% Pass (15/15 backend + all UI flows)
