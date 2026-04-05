# NeXifyAI — Setup & Deployment Guide

## Voraussetzungen
- Python 3.11+
- Node.js 18+
- MongoDB (lokal oder Atlas)
- Supabase-Projekt (PostgreSQL)

## 1. Environment einrichten

```bash
cp backend/.env.template backend/.env
# Trage alle API-Keys ein (siehe .env.template für Dokumentation)
```

### Kritische Keys (Backend startet nicht ohne):
| Key | Dienst | Bezugsquelle |
|-----|--------|-------------|
| `MONGO_URL` | MongoDB | mongodb.com oder lokal |
| `ALT_SUPABASE_POSTGRESQL` | Supabase PostgreSQL | supabase.com → Settings → Database |
| `ALT_SUPABASE_SERVICE_ROLE_KEY` | Supabase API | supabase.com → Settings → API |
| `DEEPSEEK_API_KEY` | DeepSeek LLM | platform.deepseek.com |
| `ARCEE_API_KEY` | Arcee AI Master | arcee.ai → Account |
| `MEM0_API_KEY` | mem0 Brain | app.mem0.ai → Settings |
| `SECRET_KEY` | JWT-Signierung | Selbst generieren (32+ Zeichen) |

### Optionale Keys:
| Key | Dienst | Bezugsquelle |
|-----|--------|-------------|
| `RESEND_API_KEY` | E-Mail-Versand | resend.com |
| `REVOLUT_SECRET_KEY` | Zahlungen | business.revolut.com → Developer |

## 2. Backend starten

```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

## 3. Frontend starten

```bash
cd frontend
yarn install
yarn start
```

## 4. Health-Check

```bash
curl http://localhost:8001/api/health
```

Erwartete Antwort:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": {"status": "ok"},
    "supabase": {"status": "ok"},
    "deepseek": {"status": "ok", "configured": true},
    "arcee": {"status": "ok", "configured": true},
    "mem0": {"status": "ok", "configured": true},
    "resend": {"status": "ok", "configured": true},
    "revolut": {"status": "ok", "configured": true},
    "workers": {"status": "ok", "active": 4},
    "oracle_engine": {"status": "ok", "cycle": 42}
  }
}
```

## 5. Coolify/Docker Deployment

### Umgebungsvariablen
Alle Keys aus `.env.template` als Environment Variables in Coolify setzen.

### Build
```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 6. Supabase-Schema

Die Supabase-Tabellen (`oracle_tasks`, `ai_agents`, `brain_notes`, `audit_logs`, `knowledge_base`) werden beim ersten Start automatisch geprüft. Falls Tabellen fehlen, müssen sie manuell über das Supabase-Dashboard erstellt werden.

### oracle_tasks Spalten:
- `id` (uuid, PK)
- `type` (varchar), `priority` (int), `status` (varchar(50))
- `title`, `description` (text)
- `loop_count` (int), `loop_reason`, `exit_condition` (text)
- `evidence`, `status_history` (jsonb)
- `verification_score` (numeric)
- `current_agent`, `escalation_reason` (text)
- `audit_log` (jsonb[]), `result` (jsonb)

### Status-Modell:
```
erkannt → eingeplant → gestartet → in_bearbeitung
  → wartet_auf_input | wartet_auf_freigabe | in_loop
  → erfolgreich_abgeschlossen → erfolgreich_validiert
  | fehlgeschlagen | blockiert | abgebrochen | eskaliert
```

## 7. Service-Architektur

```
Frontend (React 18) → Backend (FastAPI)
                        ├── MongoDB (CRM, Projekte, Leads)
                        ├── Supabase PostgreSQL (Oracle, Brain, Audit)
                        ├── DeepSeek API (Sub-Agenten)
                        ├── Arcee AI (Master Orchestrator)
                        ├── mem0 (Brain Memory)
                        ├── Resend (E-Mail)
                        └── Revolut (Zahlungen)
```
