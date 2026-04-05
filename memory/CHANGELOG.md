# NeXifyAI — Changelog

## 2026-04-05

### Iteration 70 — Vollständige Systemanalyse & Endkorrektur (100% Pass, 15/15)
- **FIX**: Webhooks View — Feldnamen korrigiert (processed_at, event, order_id statt timestamp, event_type, source). Status: "Verarbeitet"/"Fehler" statt "pending"
- **FIX**: View-Persistenz bei Browser-Reload via localStorage `nx_admin_view`
- **FIX**: Stats-API erweitert um contacts_total, quotes_total, contracts_total, invoices_total, projects_total
- **FEATURE**: Dashboard von 4 auf 8 Stat-Cards (+ Kontakte, Angebote, Verträge, Rechnungen)
- **FEATURE**: Chat Leitstelle (rechte Sidebar im Chat)
  - System-Status mit Echtzeit-Zahlen
  - KI-Agenten mit Status-Indikatoren
  - 6 Schnellaktionen (Morgen-Briefing, Lead-Analyse, System-Check, Brain, E-Mail, Angebot)
  - Proaktiv-Status mit Historie
  - Verbindungs-Indikatoren (Arcee AI, mem0 Brain, MongoDB)
- **FIX**: Quick-Action-Buttons senden direkt via sendNxMessage(text) statt nur Input-Fill

### Iteration 69 — Design-Harmonisierung + Autonomer Modus (100% Pass)
- Autonomer/Proaktiver Modus (4 Tasks: Briefing, Lead-Analyse, Brain-Wartung, Health-Check)
- Agent CRUD UI mit Master-Schutz
- CSS: Manrope Font, einheitliche h2/h3, Topbar 64px, Tabellen-Header muted gray

### Iteration 68 — Chat-Fixes (100% Pass)
- Chat-Scroll: adm-content--fullbleed, height:100%
- Chat-Flickering: Ref-basiertes DOM-Streaming (nxStreamRef)
- Server-seitige Tool-Ausführung mit Follow-up-Streaming
- System-Prompt: CLI-first, vollständige Plattform-Doku

### Iteration 67 — Chat Bug Fixes (100% Pass)
- CSS animation-iteration-count:1, stabile Message-Keys

## 2026-04-04
- External API v1 + Admin API-Key Management
- NeXify AI Master Chat (Arcee AI + mem0)
- Color change #FF6B00 -> #FE9B7B

## 2026-04-03
- Sidebar Harmonization
- Customer Portal Features
- Legal Texts (7 docs x 3 langs)
