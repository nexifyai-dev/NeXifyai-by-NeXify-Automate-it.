# NeXifyAI — Changelog

## 2026-04-05

### NeXify AI Master Chat Interface — Vollständig implementiert (Iteration 65)
- **Neues Feature**: NeXify AI Master als zentrales Chat-Interface im Admin-Panel
  - Arcee AI (trinity-large-preview) als LLM mit SSE-Streaming
  - mem0 Brain-Integration: Kontextsuche vor jeder Antwort, asynchrones Speichern
  - Vollständiger System-Prompt: Orchestrator-Rolle, Hierarchien, Autonomie-Regeln, Brain-Protokoll, Unternehmenswissen, Tarife
  - Conversation-Persistenz in MongoDB (nexify_ai_conversations + nexify_ai_messages)
  - Admin-UI: Chat-Sidebar mit Konversationsliste, Brain-Toggle, Quick-Action-Buttons, Markdown-Rendering, Typing-Animation
- Neue Dateien: `/app/backend/routes/nexify_ai_routes.py`
- Neue CSS: `.nxai-*` Styles in Admin.css
- Tests: 15/15 Backend-Tests + alle Frontend-Elemente verifiziert

### External API v1 — Vollständig implementiert (Iteration 64)
- Externe API v1 mit API-Key-Authentifizierung (SHA-256 Hash, Rate-Limiting, Scopes)
- Endpoints: Contacts CRUD, Leads CRUD, Quotes/Contracts/Projects/Invoices Read, Stats, Webhooks, Health, Docs
- Admin-Panel: API-Zugang View mit Key-Verwaltung und cURL-Beispiele

### P1 Content & Copywriting Overhaul (Iteration 63)
- **BUGFIX**: TrustSection i18n — war immer Deutsch, jetzt korrekt DE/NL/EN via `useLanguage()` Hook
- Erweiterte Trust-Copy in 3 Sprachen (DSGVO, EU AI Act, ISO 27001/27701 Referenzen)

### P0 Rechtstexte — Verifizierung (Iteration 62)
- 21 Legal-Routen verifiziert (7 Dokumente x 3 Sprachen)
- Footer-Links, Legacy-Redirects, Sprachumschalter getestet

## 2026-04-03

### Admin Sidebar Harmonization (Iteration 60)
- Admin sidebar collapsed by default with CSS hover tooltips (::after)
- Customer Portal sidebar follows same pattern (Iteration 61)

### Customer Portal Active Features (Iteration 61)
- Added backend APIs for requests, bookings, messages, support tickets
- Full CRUD UI forms in Customer Portal
- Quote/Contract workflows functional

### Comprehensive Legal Texts Implementation
- LegalPages.js with 7 legal documents (Impressum, Datenschutz, AGB, KI-Hinweise, Widerruf, Cookies, AVV)
- Full translations for DE/NL/EN with proper URL slugs per language
- Footer updated with all 7 legal links
- LEGAL_PATHS in shared/index.js updated
