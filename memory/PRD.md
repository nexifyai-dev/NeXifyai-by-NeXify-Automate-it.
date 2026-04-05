# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium, secure architecture. CI: #FE9B7B + White on #0c1117.

## Architecture
- Frontend: React 18 SPA | Backend: FastAPI | DB: MongoDB + Supabase PostgreSQL
- Auth: JWT + Magic Links + API Keys | LLM Master: Arcee AI (trinity-large-preview)
- LLM Sub-Agents: DeepSeek (deepseek-chat) | Memory: mem0 Brain
- Oracle System: Supabase PostgreSQL (Tasks, Brain, Knowledge, Agents)
- Workers: APScheduler | Font: Manrope
- Layout: height:100vh, overflow:hidden → no body scroll

## Completed (all verified via Testing Agent)
- [x] Worker/Scheduler-Layer, Services scaffolding, Auth Security, 3D Hero
- [x] Design/Brand Harmonization (all breakpoints, unified tokens)
- [x] Admin + Customer Portal, Legal Texts (21 routes), External API v1
- [x] NeXify AI Master Chat (37+ Tools, CLI-first, Arcee AI + mem0)
- [x] Chat Scroll Containment (height:100vh, overflow:hidden, min-height:0)
- [x] Chat Flickering Fix (Ref-based DOM streaming)
- [x] Server-side Tool Execution Loop
- [x] Agent Settings UI (CRUD) + Proactive Mode (4 scheduled tasks)
- [x] Chat Leitstelle (Right Panel: Stats, Agents, Quick Actions, Proactive, Connections)
- [x] Dashboard 8 Stat Cards
- [x] Webhooks field mapping fix
- [x] View persistence on reload (localStorage)
- [x] Systemweit kein Body-Scroll — nur Content-Bereiche scrollen
- [x] Echte Verbindungsprüfung: Arcee AI/mem0 mit API-Ping, WhatsApp/Revolut/Storage ehrlich
- [x] Monitoring mit WhatsApp-Card (NICHT VERBUNDEN), Revolut/Storage (CONFIGURED)
- [x] P0 Fix: Right Panel Scroll & Sticky Header Bug (CSS layout hardened)
- [x] P0 Fix: Chat Quick Action Buttons (typeof check, resp.ok guard, event fix)
- [x] Oracle Command Center: Supabase PostgreSQL Integration
  - 6 Tabs: Übersicht, Task-Queue, Agenten, Brain, Oracle-Tasks, Agent aufrufen
  - Live-Daten: 10.144 Brain-Notes, 2.624 Tasks, 33 AI-Agenten, 156 Knowledge
  - DeepSeek Sub-Agent Invocation (Strategist, Forge, Pixel etc.)
  - 8 neue Oracle-Tools im Master System Prompt
  - Task-Erstellung mit validen Typen (25 Kategorien)
  - Health-Check: Supabase + DeepSeek Connectivity

## Backlog
- [ ] Typography/DIN-Norm Harmonisierung (P1)
- [ ] NeXifyAI System Knowledge & Communication Guidelines Injection (P1)
- [ ] Full e2e UI Audit aller Views (P2)
- [ ] DeepSeek Live-Migration für Master (P3)
- [ ] Legal & Compliance Guardian (P4)
- [ ] server.py Refactoring (nach P1-P4)

## Testing: Iter 72-73 passed (93%→100% after fix)
