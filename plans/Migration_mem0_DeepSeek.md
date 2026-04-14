# NeXifyAI — Migrations-Plan
## M1: mem0 Cloud → mem0 OSS
## M2: DeepSeek → MiniMax M2.7

**Erstellt:** 2026-04-14
**Status:** PLAN — noch nicht umgesetzt

---

## M1: mem0 Cloud → mem0 OSS

### Problem
```python
# nexify_ai_routes.py — NOCH AKTIV
MEM0_API_KEY = os.environ.get("MEM0_API_KEY", "")
MEM0_API_URL = "https://api.mem0.ai"  # CLOUD!
```

### mem0 OSS Konfiguration (bereits aktiv)
```yaml
# /opt/data/mem0.json
{
  "config": {
    "embedder": "fastembed",
    "model": "thenlper/gte-large",
    "llm": {
      "provider": "openrouter",
      "model": "deepseek/deepseek-chat",
      "api_key": "..."
    }
  }
}
```

### Migrations-Schritte

#### Schritt 1: mem0 Python Package prüfen
```bash
# Prüfen ob mem0 im Backend-Container verfügbar
docker exec nexifyai-backend pip list | grep mem0
```

#### Schritt 2: mem0_client.py erstellen
```python
# backend/services/mem0_client.py
"""
mem0 OSS Client — Ersatz für mem0 CLOUD
"""
import os
import json
from typing import List, Optional

# mem0 OSS Configuration
MEM0_CONFIG_PATH = os.environ.get("MEM0_CONFIG_PATH", "/opt/data/mem0.json")

class Mem0OSS:
    def __init__(self):
        with open(MEM0_CONFIG_PATH) as f:
            config = json.load(f)
        self.embedder = config["config"]["embedder"]
        self.model = config["config"]["model"]
        # ... rest of config
    
    async def search(self, query: str, top_k: int = 5, user_id: str = None) -> List[dict]:
        """Suche in lokaler pgvector DB"""
        # Nutze asyncpg oder psycopg2 für pgvector
        # Return format: [{"memory": "...", "score": 0.9, "id": "..."}]
    
    async def store(self, messages: List[dict], metadata: dict = None, user_id: str = None) -> dict:
        """Speichere in lokaler pgvector DB"""
        # Nutze asyncpg für INSERT
        # Return: {"id": "...", "status": "stored"}
```

#### Schritt 3: nexify_ai_routes.py updaten
```python
# VORHER
from routes.mem0_cloud import mem0_search, mem0_store

# NACHHER
from services.mem0_client import mem0_oss_search, mem0_oss_store
```

#### Schritt 4: Testen
```bash
# Lokaler Test
curl -X POST http://localhost:8000/api/admin/nexify-ai/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

---

## M2: DeepSeek → MiniMax M2.7

### Problem
```python
# nexify_ai_routes.py — NOCH AKTIV
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"

MASTER_LLM = "deepseek" if DEEPSEEK_API_KEY else "arcee"
```

### Ziel-Konfiguration
```python
# NACHHER
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "minimax/minimax-m2.7"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
```

### Migrations-Schritte

#### Schritt 1: OpenRouter Key prüfen
```bash
# Bereits vorhanden in secrets.env
OPENROUTER_API_KEY=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
```

#### Schritt 2: LLM-Config ersetzen
```python
# VORHER
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# NACHHER
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "minimax/minimax-m2.7"
```

#### Schritt 3: API-Call anpassen
```python
# VORHER
async with httpx.AsyncClient() as client:
    resp = await client.post(
        DEEPSEEK_CHAT_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={"model": DEEPSEEK_MODEL, "messages": messages}
    )

# NACHHER
async with httpx.AsyncClient() as client:
    resp = await client.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://nexifyai.de",
            "X-Title": "NeXifyAI"
        },
        json={"model": MODEL, "messages": messages}
    )
```

#### Schritt 4: Testen
```bash
curl -X POST http://localhost:8000/api/admin/nexify-ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test MiniMax M2.7"}'
```

---

## Beide Migrationen zusammen

### Reihenfolge
1. **M2 ZUERST** (MiniMax M2.7) — simpler, weniger Risiko
2. **M1 DANACH** (mem0 OSS) — komplexer, erfordert DB-Änderungen

### Risiken
| Migration | Risiko | Mitigierung |
|-----------|--------|-------------|
| M2: DeepSeek→MiniMax | NIEDRIG | Nur API-Endpoint + Key ändern |
| M1: mem0 Cloud→OSS | MITTEL | Backup der mem0 Cloud Daten vorher |

### Rollback
```bash
# Bei Problemen
git revert HEAD  # Letzten Commit rückgängig
```

---

## Checkpoint-Plan

```
PHASE 0: Backup
├── mem0 Cloud Export (falls möglich)
├── Git Commit (Backup-Punkt)
└── Docker Image Backup

PHASE 1: M2 (DeepSeek→MiniMax)
├── API-Keys ändern
├── Test: Chat funktioniert
└── Git Commit

PHASE 2: M1 (mem0 Cloud→OSS)
├── mem0_client.py erstellen
├── DB-Schema prüfen
├── Test: Search + Store funktionieren
└── Git Commit
```

---

## STATUS

| Migration | Status | Anmerkung |
|-----------|--------|-----------|
| M2: DeepSeek→MiniMax | ⬜ OFFEN | OpenRouter Key vorhanden |
| M1: mem0 Cloud→OSS | ⬜ OFFEN | mem0 OSS bereits aktiv (Hermes) |
