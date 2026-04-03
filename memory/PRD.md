# NeXifyAI — Product Requirements Document

## Originalanforderung
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium-Architektur mit Unified Login Stack, Worker/Scheduler Layer, strikter Trennung Admin/Portal.

## Ziel-Architektur
- **LLM**: DeepSeek (Primär) → Emergent GPT (Fallback)
- **Backend**: FastAPI + MongoDB + APScheduler
- **Frontend**: React 18 SPA
- **Auth**: JWT mit Rollen (Admin, Customer)
- **Payments**: Revolut + Stripe (Webhooks)
- **Compliance**: Legal Guardian (DSGVO, UWG, EU AI Act)

## Commercial Source of Truth
- Starter AI Agenten AG — NXA-SAA-24-499 — 499,00 EUR netto / Monat — 24 Monate — 30% Aktivierungsanzahlung 3.592,80 EUR
- Growth AI Agenten AG — NXA-GAA-24-1299 — 1.299,00 EUR netto / Monat — 24 Monate — 30% Aktivierungsanzahlung 9.352,80 EUR

## Status — Produktionsnahe Abschlussphase

### P1: DeepSeek Live aktivieren — VERIFIZIERT
- Provider-Abstraktionsschicht: DeepSeekProvider (Retry, Metriken, Circuit-Breaker) + EmergentGPTProvider (Fallback)
- Factory mit auto-detect: DEEPSEEK_API_KEY → DeepSeek, sonst Emergent GPT
- Chat-Flow über `llm_provider` geroutet (kein direkter LlmChat-Zugriff)
- Endpoints: /api/admin/llm/status, /health, /test, /test-agent-flow
- **Restrisiko**: DEEPSEEK_API_KEY nicht gesetzt → Fallback aktiv. Key einsetzen → sofortige Umschaltung.

### P2: Portal-Finance-Ansicht — VERIFIZIERT
- /api/customer/finance: Rechnungen, Zahlungsstatus, Fälligkeit, Beträge (Netto/USt/Brutto), PDF-Download, Zahlungslinks, Banküberweisung
- Summary mit total_outstanding, total_paid, open_invoices, overdue_invoices
- Mahnstufen-Anzeige
- Premium-UX: Status-Farben, Overdue-Warnungen, IBAN/BIC-Anzeige

### P3: Contract OS im Portal — VERIFIZIERT
- Versionshistorie im Contract-Detail
- Evidenzpaket (IP, User-Agent, Hash, Version, Consent, Signatur-Typ)
- Signatur-Vorschau nach Annahme
- PDF-Download
- Änderungsanfrage-Detail

### P4: Webhooks produktiv — VERIFIZIERT
- Revolut Signatur-Verifikation (HMAC-SHA256)
- Reconciliation-Endpoint (Quote ↔ Contract ↔ Invoice ↔ Payment)
- Webhook-History für Audit
- Idempotente Verarbeitung

### P5: E2E-Flow — VERIFIZIERT
- /api/admin/e2e/verify-flow prüft: quote_has_invoice, contract_has_quote, payment_status_sync, reminder_on_paid, llm_provider_healthy, contract_evidence_complete
- 100% Pass Rate

### P6: Legal Guardian — VERIFIZIERT
- Legal Gate im Contract-Accept-Flow
- Outreach Gate (DSGVO, UWG, Suppression, Opt-Out)
- Compliance-Summary
- Risk Management (add, resolve, list)
- Audit Log

### P7: Outbound Lead Machine — VERIFIZIERT
- Legal Gate im Send-Flow
- Response-Tracking (positive/negative/opt_out)
- Handover zu Quote/Meeting/Nurture
- CRM-Lead-Erstellung bei Quote-Handover

### P8: server.py Refactoring — AUSSTEHEND
- server.py >6000 Zeilen → Modularisierung in auth_routes.py, portal_routes.py, contract_routes.py, billing_routes.py, outbound_routes.py, comms_routes.py, monitoring_routes.py, workers_routes.py
- ERST nach P1-P7 stabil

## Testing
- Iteration 35: 100% (P1-P3)
- Iteration 36: 100% (P1-P7 komplett, Backend 18/18, Frontend 100%)

## Restrisiken
1. DEEPSEEK_API_KEY nicht gesetzt → Architektur bereit, Key einsetzen
2. Stripe/Revolut Live-Keys → Sandbox-Modus aktiv
3. server.py >6000 Zeilen → Refactoring geplant (P8)
