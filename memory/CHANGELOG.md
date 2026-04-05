# NeXifyAI — Changelog

## 2026-04-05

### Iteration 69 — Design-Harmonisierung + Autonomer Modus (100% Pass, 15/15 Backend + alle UI-Flows)
- **FEATURE**: Autonomer/Proaktiver Modus für NeXify AI Master
  - 4 geplante Aufgaben: Morgen-Briefing, Lead-Analyse, Brain-Wartung, System-Health-Check
  - Manueller Trigger über Admin UI oder automatisch per Cron
  - Jede Ausführung erstellt eine eigene Konversation in der Chat-Historie
  - API: GET/PUT /api/admin/nexify-ai/proactive, POST /api/admin/nexify-ai/proactive/trigger/{id}
- **FEATURE**: Agent-Einstellungen UI (CRUD)
  - Master Agent + alle Fachagenten konfigurierbar
  - Erstellen, Bearbeiten, Löschen von Agenten
  - Master-Agent ist lösch-geschützt (403)
- **DESIGN**: Globale CSS-Harmonisierung
  - Manrope als primäre Schriftart
  - Einheitliche Heading-Größen: h2=1.125rem, h3=.9375rem
  - Topbar fixe Höhe: 64px
  - Tabellen-Header: Muted Gray statt Coral
  - Tabellen-Zellen: Einheitliches Padding 12px 16px
  - Stat-Werte: 1.75rem statt 2rem
  - Buttons: inline-flex statt width:100%
  - Duplikat .adm-badge entfernt
  - Section-Header Gap: 12px statt 8px

### Iteration 68 — Chat-Fixes + Agent CRUD (100% Pass, 13/13 Backend)
- **BUGFIX**: Chat-Seite Scroll-Problem (gesamtes Portal scrollte)
  - Ursache: .adm-content hatte padding:24px + overflow-y:auto, nxai-chat sprengte Viewport
  - Fix: .adm-content--fullbleed (padding:0, overflow:hidden), .nxai-chat height:100%
- **BUGFIX**: Chat-Flickering bei jedem Streaming-Chunk
  - Ursache: setNxStreamText(state) triggerte Re-Render aller Messages inkl. dangerouslySetInnerHTML
  - Fix: nxStreamRef (DOM ref) + nxUpdateStream() schreibt direkt in DOM, kein React-State
- **BUGFIX**: CSS Animation nxaiFadeIn komplett entfernt (verursachte Blinken)
- **FEATURE**: Server-seitige Tool-Ausführung im Chat
  - Backend erkennt ```tool-Blöcke, führt bis zu 5 Tools pro Turn aus
  - Ergebnisse werden an AI zurückgesendet für natürliche Interpretation
  - Follow-up Response wird als separater Stream geliefert
- **FEATURE**: System-Prompt komplett überarbeitet
  - CLI-first Ansatz (execute_shell bevorzugt über execute_python)
  - Vollständige Plattform-Dokumentation (Architektur, Collections, Endpoints, Tarife)
  - Proaktive Arbeitsweise kodifiziert

## 2026-04-04
- External API v1 (api_v1_routes.py) + Admin API-Key Management
- NeXify AI Master Chat Integration (Arcee AI + mem0)
- Global Color Change (#FF6B00 -> #FE9B7B)
- Admin Topbar Logo + Chat flickering fix (Streaming plain text)

## 2026-04-03
- Admin + Customer Portal Sidebar Harmonization
- Customer Portal Active Features
- Comprehensive Legal Texts (7 documents x 3 languages)
