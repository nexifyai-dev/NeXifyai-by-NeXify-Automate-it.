# NeXifyAI by NeXify Automate it

Autonomes Multi-Agent-System für Marketing, Sales, Support und Operations.

## Architektur

```
LibreChat (Arbeitsplatz)
    ↓
Oracle Engine (24/7)
    ↓
┌─────────────────────────────────────────────────────┐
│ 10 Specialist Agents (intake, research, outreach,   │
│ offer, planning, finance, support, design, qa,     │
│ orchestrator)                                       │
└─────────────────────────────────────────────────────┘
    ↓
mem0 OSS (Brain) | Supabase (Daten) | MiniMax M2.7 (LLM)
```

## Tech Stack

- **LLM:** MiniMax M2.7 via OpenRouter
- **Brain:** mem0 OSS (pgvector + fastembed)
- **Control Plane:** Paperclip
- **Database:** Supabase (PostgreSQL)
- **Chat:** LibreChat
- **Infra:** Docker, Traefik

## Verzeichnis-Struktur

```
nexifyai/
├── backend/              # FastAPI Server
│   ├── agents/           # 10 Specialist Agents
│   ├── routes/           # 17 API-Routen
│   ├── services/         # Oracle Engine, etc.
│   └── server.py
├── frontend/             # React App
│   └── src/pages/        # Admin, CustomerPortal, OracleView
├── docs/                 # Operative Dokumente
│   ├── Master_Prompt_v2.md
│   ├── DOS_v2.md
│   ├── Projekt_Template_v2.md
│   ├── Oracle_Architektur.md
│   └── Specialist_Prompts.md
├── plans/                # Strategische Pläne
│   ├── Gesamtplan_Oracle_System.md
│   ├── Luecken_Analyse.md
│   └── Implementierungsplan_Schrittweise.md
├── specs/                # Technische Spezifikationen
├── prompts/              # Agent-Prompts
├── templates/            # Wiederverwendbare Vorlagen
└── tests/
```

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| `docs/Master_Prompt_v2.md` | Identity, Rollen, Qualitätsprinzipien |
| `docs/DOS_v2.md` | Digital Operating System, Guardrails |
| `docs/Projekt_Template_v2.md` | Projektstandards, Pflichtfelder |
| `docs/Oracle_Architektur.md` | Oracle-System Design |
| `docs/Specialist_Prompts.md` | Alle Agent-Prompt-Definitionen |
| `plans/Luecken_Analyse.md` | Analyse fehlender Komponenten |
| `plans/Implementierungsplan_Schrittweise.md` | 12-Phasen-Plan |

## Aktuelle Projekte

### Studienkolleg Aachen
- **Domain:** studienkolleg.nexifyai.de
- **Stack:** Next.js, Supabase, Paperclip, Oracle
- **Status:** In Entwicklung

## Schlüssel-Entscheidungen

1. **mem0 OSS** als Brain (keine Cloud-Abhängigkeit)
2. **MiniMax M2.7** als primäres LLM
3. **Mandantentrennung** in allen Komponenten
4. **Inkrementelle Entwicklung** — Phase für Phase

## Getting Started

```bash
# Backend starten
cd backend
docker compose up -d

# Frontend starten
cd frontend
npm run dev

# Oracle Engine (24/7)
# Läuft automatisch via Cron/Worker
```

## Keys

Keys werden zentral verwaltet in `/opt/data/keys/nexifyai/secrets.env`.
Niemals API-Keys im Code oder Repo committen.
