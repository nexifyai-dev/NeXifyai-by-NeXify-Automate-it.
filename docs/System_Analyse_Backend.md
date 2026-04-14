# NeXifyAI — Backend System-Analyse
## Stand: 2026-04-14

---

## ÜBERSICHT

| File | Zeilen | Funktion |
|------|--------|----------|
| `nexify_ai_routes.py` | 1827 | **HAUPT-CHAT-API** + Tools + mem0 |
| `admin_routes.py` | 961 | Admin Dashboard API |
| `billing_routes.py` | 1353 | Angebote + Rechnungen |
| `portal_routes.py` | 954 | Kunden-Self-Service |
| `contract_routes.py` | 687 | Vertragsmanagement |
| `outbound_routes.py` | 323 | Outbound Lead Maschine |
| `oracle_routes.py` | ~500 | Oracle Task API |
| `services/oracle_engine.py` | 815 | Oracle Engine |
| `services/supabase_client.py` | 206 | DB-Client |

**TOTAL: ~6000+ Zeilen Backend-Code**

---

## KRITISCHE BEFUNDE

### ❌ PROBLEM 1: mem0 CLOUD noch aktiv
**File:** `nexify_ai_routes.py` Zeilen 31-36
```python
MEM0_API_KEY=os.environ.get("MEM0_API_KEY", "")
MEM0_API_URL = os.environ.get("MEM0_API_URL", "https://api.mem0.ai")
```
**Status:** NOCH auf mem0 Cloud statt mem0 OSS!
**Must Fix:** Muss auf lokales mem0 OSS umgestellt werden.

### ❌ PROBLEM 2: DeepSeek als Primary
**File:** `nexify_ai_routes.py` Zeilen 18-25
```python
DEEPSEEK_API_KEY=os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_CHAT_URL = f"{DEEPSEEK_BASE_URL}/v1/chat/completions"
```
**Status:** DeepSeek ist Primary, soll aber MiniMax M2.7 sein!
**Arcee AI** ist Fallback (sollte MiniMax M2.7 sein).

### ⚠️ PROBLEM 3: Dual mem0 Implementation
- **nexify_ai_routes.py** nutzt mem0 CLOUD API
- **Hermes Plugin** nutzt mem0 OSS (pgvector)
- **Zwei verschiedene Systeme** parallel!

---

## nexify_ai_routes.py (1827 Z.)

### Hauptrouten
| Route | Zeile | Funktion |
|-------|-------|----------|
| `POST /api/admin/nexify-ai/chat` | 516 | **HAUPT-CHAT** |
| `GET /api/admin/nexify-ai/conversations` | 418 | Conversation-Liste |
| `DELETE /api/admin/nexify-ai/conversations/{id}` | 444 | Conversation löschen |
| `POST /api/admin/nexify-ai/memory/search` | 701 | mem0 Cloud Suche |
| `POST /api/admin/nexify-ai/memory/store` | 708 | mem0 Cloud Speicher |
| `GET /api/admin/nexify-ai/status` | 715 | Status DeepSeek/Arcee/mem0 |
| `GET /api/admin/nexify-ai/tools` | 879 | Verfügbare Tools |
| `POST /api/admin/nexify-ai/execute-tool` | 885 | Tool ausführen |
| `GET/POST/PUT/DELETE /api/admin/nexify-ai/agents` | 1594-1693 | Agent CRUD |
| `GET /api/admin/nexify-ai/proactive` | 1740 | Proaktiver Modus |

### Wichtige Klassen
```python
class ChatMessage(BaseModel):      # Chat-Nachricht
class ChatRequest(BaseModel):       # Chat-Request
class MemorySearchRequest(BaseModel): # mem0 Suche
class MemoryStoreRequest(BaseModel):  # mem0 Speicher
class ToolRequest(BaseModel):        # Tool-Execution
class AgentSettingsRequest(BaseModel): # Agent-Config
class ProactiveModeRequest(BaseModel): # Proaktive Tasks
```

### System-Prompt (Auszug)
```
SYSTEM PROMPT — NeXify AI (Operativer Assistent)
Du bist NeXify AI, der operative Assistent innerhalb der NeXifyAI-Plattform.
Du arbeitest 24/7 autonom, proaktiv und ergebnisorientiert.
...
Agent Zero ist die zentrale Leit-, Koordinations- und Entscheidungsinstanz.
Hierarchie: 1. Pascal, 2. Agent Zero, 3. NeXify AI, 4. Fachagenten
```

### LLM-Config
```python
MASTER_LLM = "deepseek" if DEEPSEEK_API_KEY else "arcee"
# DeepSeek Primary, Arcee Fallback
# SOLL: MiniMax M2.7 Primary
```

---

## admin_routes.py (961 Z.)

### Routen
| Route | Funktion |
|-------|----------|
| `GET /api/admin/stats` | Dashboard-Statistiken |
| `GET/POST /api/admin/leads` | Leads CRUD |
| `GET/PATCH /api/admin/leads/{id}` | Lead Details + Update |
| `GET/POST /api/admin/bookings` | Termine |
| `GET/PATCH/DELETE /api/admin/bookings/{id}` | Booking Details |
| `GET/POST/DELETE /api/admin/blocked-slots` | Blockierte Zeiten |
| `GET/POST /api/admin/customers` | Kunden |
| `POST /api/admin/customers/portal-access` | Portal-Zugang |
| `GET /api/admin/calendar-data` | Kalender-Daten |
| `GET /api/admin/timeline` | Timeline |
| `POST /api/admin/leads/{id}/notes` | Lead-Notizen |
| `GET /api/admin/customers/{email}/casefile` | Kundenakte |

---

## billing_routes.py (1353 Z.)

### Quotes (Angebote)
| Route | Funktion |
|-------|----------|
| `POST /api/admin/quotes` | Angebot erstellen |
| `GET /api/admin/quotes` | Liste |
| `GET /api/admin/quotes/{id}` | Detail |
| `PATCH /api/admin/quotes/{id}` | Update |
| `POST /api/admin/quotes/{id}/send` | Senden |
| `POST /api/admin/quotes/{id}/copy` | Kopieren |
| `POST /api/chat/generate-offer` | Chat-generiert |

### Invoices (Rechnungen)
| Route | Funktion |
|-------|----------|
| `POST /api/admin/invoices` | Erstellen |
| `GET /api/admin/invoices` | Liste |
| `GET /api/admin/invoices/{id}` | Detail |
| `PATCH /api/admin/invoices/{id}` | Update |
| `POST /api/admin/invoices/{id}/send` | Senden |
| `POST /api/admin/invoices/{id}/mark-paid` | Als bezahlt |
| `POST /api/admin/invoices/{id}/send-reminder` | Erinnerung |

### Documents & Webhooks
| Route | Funktion |
|-------|----------|
| `GET /api/documents/{type}/{id}/pdf` | PDF Download |
| `POST /api/admin/access-link` | Access-Link erstellen |
| `POST /api/webhooks/revolut` | Payment Webhook |
| `GET /api/admin/billing/status` | Billing Status |
| `POST /api/admin/billing/reconcile` | Reconciliation |

---

## portal_routes.py (954 Z.)

### Customer Dashboard
| Route | Funktion |
|-------|----------|
| `GET /api/customer/dashboard` | Kunden-Dashboard |
| `GET /api/customer/finance` | Eigene Finanzen |
| `GET /api/customer/profile` | Profil |
| `PATCH /api/customer/profile` | Profil updaten |
| `GET /api/customer/documents` | Eigene Dokumente |
| `GET /api/customer/consents` | Einwilligungen |
| `POST /api/customer/consents/opt-out` | Austragen |
| `POST /api/customer/consents/opt-in` | Eintragen |
| `POST /api/customer/requests` | Anfrage erstellen |
| `GET /api/customer/requests` | Eigene Anfragen |
| `POST /api/customer/bookings` | Termin buchen |
| `POST /api/customer/messages` | Nachricht senden |

### Quote Portal (Token-basiert)
| Route | Funktion |
|-------|----------|
| `GET /api/portal/quote/{id}` | Angebot ansehen |
| `POST /api/portal/quote/{id}/accept` | Annehmen |
| `POST /api/portal/quote/{id}/decline` | Ablehnen |
| `POST /api/portal/quote/{id}/revision` | Überarbeitung |

---

## contract_routes.py (687 Z.)

### Admin Contracts
| Route | Funktion |
|-------|----------|
| `POST /api/admin/contracts` | Erstellen |
| `GET /api/admin/contracts` | Liste |
| `GET /api/admin/contracts/{id}` | Detail |
| `PATCH /api/admin/contracts/{id}` | Update |
| `POST /api/admin/contracts/{id}/appendices` | Anhang |
| `POST /api/admin/contracts/{id}/send` | Senden |
| `GET /api/admin/contracts/{id}/evidence` | Signatur-Nachweis |
| `POST /api/admin/contracts/{id}/generate-pdf` | PDF |

### Customer Contracts
| Route | Funktion |
|-------|----------|
| `GET /api/customer/contracts` | Eigene Verträge |
| `GET /api/customer/contracts/{id}` | Detail |
| `POST /api/customer/contracts/{id}/accept` | Annehmen |
| `POST /api/customer/contracts/{id}/decline` | Ablehnen |
| `POST /api/customer/contracts/{id}/request-change` | Änderung |

### Public
| Route | Funktion |
|-------|----------|
| `GET /api/public/contracts/view` | Token-View |

---

## outbound_routes.py (323 Z.)

### Lead Pipeline
| Route | Funktion |
|-------|----------|
| `GET /api/admin/outbound/leads` | Lead-Liste |
| `GET /api/admin/outbound/stats` | Statistiken |
| `POST /api/admin/outbound/discover` | Neue Leads finden |
| `GET /api/admin/outbound/pipeline` | Pipeline |
| `GET /api/admin/outbound/campaigns` | Kampagnen |

### Lead Actions
| Route | Funktion |
|-------|----------|
| `POST /api/admin/outbound/{id}/prequalify` | Vorauswahl |
| `POST /api/admin/outbound/{id}/analyze` | Analyse |
| `POST /api/admin/outbound/{id}/legal-check` | DSGVO |
| `POST /api/admin/outbound/{id}/outreach` | Erstansprache |
| `POST /api/admin/outbound/{id}/outreach/{oid}/send` | Senden |
| `POST /api/admin/outbound/{id}/followup` | Nachfass |
| `POST /api/admin/outbound/opt-out` | Opt-Out |
| `POST /api/admin/outbound/{id}/respond` | Antwort |
| `POST /api/admin/outbound/{id}/handover` | An Sales |

---

## ARCHITEKTUR-ZUSAMMENHANG

```
                    ┌─────────────────────────────────────┐
                    │         LibreChat (Frontend)        │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────┐
│                      nexify_ai_routes.py                         │
│  POST /chat (DeepSeek/Arcee, mem0 CLOUD)                         │
│  POST /memory/search (mem0 CLOUD)                                │
│  POST /memory/store (mem0 CLOUD)                                 │
│  GET /tools, POST /execute-tool                                   │
│  GET/POST/PUT/DELETE /agents                                     │
└───────────────────────┬───────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌──────────┐    ┌──────────┐
   │ billing_ │    │  admin_  │    │  portal_ │
   │ routes   │    │  routes  │    │  routes  │
   └─────────┘    └──────────┘    └──────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
                   ┌──────────┐
                   │ Supabase │
                   │(MongoDB) │
                   └──────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Paperclip  │
                 │ (Control)  │
                 └─────────────┘
```

---

## MIGRATIONS-BEDARF

### Phase M1: mem0 Cloud → OSS
```python
# VORHER (nexify_ai_routes.py)
MEM0_API_KEY=os.environ.get("MEM0_API_KEY", "")
MEM0_API_URL = os.environ.get("MEM0_API_URL", "https://api.mem0.ai")

# NACHHER: Nutze lokales mem0 OSS
# config: /opt/data/mem0.json
# endpoint: mem0-postgres:5432
```

### Phase M2: DeepSeek → MiniMax M2.7
```python
# VORHER
DEEPSEEK_API_KEY=os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"

# NACHHER
OPENROUTER_API_KEY=os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "minimax/minimax-m2.7"
```

---

## FRONTEND-ANALOGIEN

| Backend Route | Frontend (React) | Funktion |
|---------------|------------------|----------|
| billing_routes | Admin.js (274KB) | Angebote/Rechnungen UI |
| admin_routes | Admin.js | Dashboard, Leads, Bookings |
| portal_routes | CustomerPortal.js (82KB) | Kunden-Self-Service |
| oracle_routes | OracleView.js (27KB) | Oracle Task View |
| contract_routes | LegalPages.js (95KB) | Verträge |

---

## NÄCHSTE SCHRITTE

1. **M1:** mem0 Cloud → OSS Migration starten
2. **M2:** DeepSeek → MiniMax M2.7 Migration
3. **Frontend:** Admin.js, CustomerPortal.js, OracleView.js analysieren
4. **Mandantentrennung:** tenant_id in alle Routes + DB

---

## STATUS

| Komponente | Status | Anmerkung |
|------------|--------|-----------|
| Oracle Engine | ⚠️ PARTIALLY | Nutzt DeepSeek |
| nexify_ai_routes | ❌ BUG | mem0 CLOUD aktiv |
| billing_routes | ✅ OK | Vollständig |
| admin_routes | ✅ OK | Vollständig |
| portal_routes | ✅ OK | Vollständig |
| contract_routes | ✅ OK | Vollständig |
| outbound_routes | ✅ OK | Vollständig |
| supabase_client | ✅ OK | Nutzt asyncpg Pool |

---

**Erstellt:** 2026-04-14
**Autor:** NeXifyAI Brain Analysis
