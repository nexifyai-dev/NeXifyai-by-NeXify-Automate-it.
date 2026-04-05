# NeXifyAI — Product Requirements Document (PRD)

## Plattform
NeXifyAI by NeXify — B2B AI Agency Platform. API-First, Unified Communication, Deep Customer Memory (mem0), Supabase Oracle System, DeepSeek/Arcee AI Orchestrators.

## Architektur
- **Frontend**: React 18 SPA
- **Backend**: FastAPI (Python)
- **Datenbanken**: MongoDB (CRM, Projekte), Supabase PostgreSQL (Oracle Tasks, AI Agents, Brain Notes, Audit Logs)
- **AI**: Arcee AI (Master Orchestrator), DeepSeek (Sub-Agenten), mem0 (Brain Memory)
- **Workers**: APScheduler (24/7 autonome Task-Verarbeitung)

## Kernmodule

### 1. Unified Login Stack
- 2-Schritt-Anmeldung (E-Mail → Rollenauswahl → Passwort)
- Admin- und Kundenportal-Trennung
- JWT-basierte Authentifizierung

### 2. Oracle System (Supabase)
- Autonome Task-Verarbeitung (alle 90s)
- KI-Agenten: Nexus, Strategist, Forge, Lexi, Scout, Scribe, Pixel, Care, Rank
- Brain-Notes & Knowledge-Base
- Score-basierte Verifikation (DeepSeek → Verifier)

### 3. Granulares Status-Modell (Zentrale Leitstelle) ✅ NEU
- 13 definierte Status: erkannt, eingeplant, gestartet, in_bearbeitung, wartet_auf_input, wartet_auf_freigabe, in_loop, erfolgreich_abgeschlossen, erfolgreich_validiert, fehlgeschlagen, blockiert, abgebrochen, eskaliert
- Loop-Tracking: Iteration-Zähler, Loop-Begründung, Exit-Condition
- Evidence-Pakete: Executor, Verifier, Score, Zeitstempel
- Klare Trennung: "abgeschlossen" ≠ "validiert/bewiesen"
- Automatische Eskalation nach MAX_LOOP_ITERATIONS
- Status-History (JSONB) für vollständigen Audit-Trail

### 4. Zentrale Leitstelle (Command Center) ✅ NEU
- Live-Pipeline-Status: Erkannt, In Arbeit, Wartend, In Loop, Validiert, Fehlgeschlagen, Eskaliert
- Aktive Agenten mit aktuellem Task und Status
- Loop-Monitor: Warum loopt ein Task, Iteration, Exit-Bedingung
- Eskalations-Dashboard
- Letzte Validierungen mit Score-Anzeige
- Manuelle Task-Eskalation und -Abbruch

### 5. Service-Boilerplate-System ✅ NEU
- 9 vorgefertigte Leistungskonzepte:
  - Starter AI Agenten AG (499 EUR/Monat)
  - Growth AI Agenten AG (1.299 EUR/Monat)
  - SEO Starter (799 EUR/Monat)
  - SEO Growth (1.499 EUR/Monat)
  - Website Starter (2.990 EUR)
  - Website Professional (7.490 EUR)
  - Website Enterprise (14.900 EUR)
  - App MVP (9.900 EUR)
  - App Professional (24.900 EUR)
- Jedes Template enthält: Milestones, Deliverables, Agenten-Zuweisungen, Standard-Content, Automationsregeln
- Template-Instanziierung: Sofortige Projekterstellung mit Tasks aus Boilerplate
- Ziel: Kundenbestellungen in unter 3 Stunden abwickelbar

### 6. NeXify AI Master Chat
- Kontextbewusste KI-Konversationen (Arcee AI)
- Brain-Integration (mem0)
- Direkte Tools: Kontakte, Leads, Statistiken, Brain, Web-Suche
- Schnellaktionen: Morgen-Briefing, Lead-Analyse, System-Check

### 7. CRM & Pipeline
- Leads, Kontakte, Angebote, Verträge, Rechnungen
- Timeline-Events pro Entität
- Pipeline-Visualisierung

## API Endpoints

### Oracle Leitstelle
- `GET /api/admin/oracle/leitstelle` — Live-Statusübersicht
- `GET /api/admin/oracle/tasks/{id}/transitions` — Task-Statusübergänge
- `POST /api/admin/oracle/tasks/{id}/escalate` — Manuelle Eskalation
- `POST /api/admin/oracle/tasks/{id}/cancel` — Manueller Abbruch

### Service Templates
- `GET /api/admin/service-templates` — Alle Boilerplates
- `GET /api/admin/service-templates/{key}` — Template-Detail
- `POST /api/admin/service-templates/instantiate` — Projekt aus Template erstellen

## Supabase DB Schema (oracle_tasks)
- id, type, priority, status (13 granulare DE-Status), title, description
- assigned_to, owner_agent, current_agent
- loop_count, loop_reason, exit_condition
- evidence (JSONB), status_history (JSONB), verification_score
- escalation_reason, error_message
- audit_log (JSONB[]), result (JSONB)
- created_at, started_at, completed_at, retry_count

## Testing: Iteration 77, 100% Pass (Backend 22/22, Frontend 100%)

## Backlog
- P1: Legal & Compliance Guardian (operative Verdrahtung)
- P2: DeepSeek Live-Migration für Master Orchestrator
- Backlog: server.py Refactoring (nach Stabilisierung)
- Backlog: Next.js Migration
- Backlog: PydanticAI + LiteLLM + Temporal
