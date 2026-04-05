# NeXifyAI — Product Requirements Document (PRD)

## Plattform
NeXifyAI by NeXify — B2B AI Agency Platform. API-First, Unified Communication, Deep Customer Memory (mem0), Supabase Oracle System, DeepSeek/Arcee AI Orchestrators.

## Architektur
- **Frontend**: React 18 SPA
- **Backend**: FastAPI (Python)
- **Datenbanken**: MongoDB (CRM, Projekte), Supabase PostgreSQL (Oracle Tasks, AI Agents, Brain Notes, Audit Logs)
- **AI**: DeepSeek (Primary Master + Sub-Agenten), Arcee AI (Fallback), mem0 (Brain Memory)
- **Intelligence**: Crawl4AI (Web-Crawling), Nutrient AI (Document Processing)
- **Workers**: APScheduler (24/7 autonome Task-Verarbeitung)

## Implementierte Module

### 1. Unified Login Stack
- 2-Schritt-Anmeldung, Admin/Kundenportal-Trennung, JWT Auth

### 2. Oracle System (Supabase)
- Autonome Task-Verarbeitung (alle 90s)
- 9 KI-Agenten: Nexus, Strategist, Forge, Lexi, Scout, Scribe, Pixel, Care, Rank
- Score-basierte Verifikation

### 3. Granulares Status-Modell (Zentrale Leitstelle)
- 13 definierte Status: erkannt bis eskaliert
- Loop-Tracking, Evidence-Pakete, Auto-Eskalation

### 4. Service-Boilerplate-System
- 9 Leistungskonzepte mit Template-Instanziierung

### 5. DeepSeek Live-Migration (NEU)
- Master Orchestrator migriert von Arcee AI zu DeepSeek
- DeepSeek = Primary, Arcee = Fallback
- Streaming-Chat, Tool-Execution, Follow-up alles auf DeepSeek
- Status-Endpoint zeigt master_llm='deepseek'

### 6. Intelligence Center (NEU)
- **Crawl4AI**: Web-Crawling, Firmen-Recherche, Wettbewerbsmonitoring
  - Live mit Playwright Chromium
  - Endpoints: /api/admin/intelligence/crawl, research-company, monitor-competitor
  - Master-AI Tools: crawl_url, research_company, monitor_competitor
- **Nutrient AI**: PDF-Analyse, Vertrags-Risikoscoring, Dokumenten-Chat
  - Endpoints: /api/admin/intelligence/analyze-document, contract-risk, document-chat
  - Benötigt NUTRIENT_API_KEY (nutrient.io/sdk/try)
- Frontend: Intelligence-Tab mit Status-Cards und Crawl-Interface

### 7. Platform-Härtung
- .env.template, Health-Check (8 Services), Startup-Key-Validierung
- Sub-Agenten auf LLMProvider migriert, Status-Migration EN->DE
- Stripe entfernt, Revolut aktiv

### 8. NeXify AI Master Chat
- DeepSeek-powered Konversationen mit mem0 Brain
- Intelligence-Tools direkt im Chat verfügbar
- Schnellaktionen, Proaktiver Modus

## API Endpoints (Aktuell)
- `GET /api/health` — 8 Services Health-Check
- `GET /api/admin/nexify-ai/status` — Master LLM Status (DeepSeek/Arcee)
- `GET /api/admin/oracle/leitstelle` — Live-Statusübersicht
- `GET /api/admin/service-templates` — 9 Boilerplates
- `POST /api/admin/intelligence/crawl` — Web-Crawling
- `POST /api/admin/intelligence/research-company` — Firmen-Recherche
- `POST /api/admin/intelligence/monitor-competitor` — Monitoring
- `POST /api/admin/intelligence/analyze-document` — PDF-Analyse
- `POST /api/admin/intelligence/contract-risk` — Risikoscoring
- `GET /api/admin/intelligence/status` — Intelligence Status

## Testing: Iteration 79, 100% Pass (Backend 9/9, Frontend 100%)

## Backlog
- P1: Legal & Compliance Guardian (operative Verdrahtung)
- NUTRIENT_API_KEY konfigurieren (nutrient.io/sdk/try)
- server.py Refactoring (nach Stabilisierung)
- Next.js Migration, PydanticAI + LiteLLM + Temporal
