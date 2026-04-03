# NeXifyAI — Product Requirements Document

## Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator, Manuelles CRM als vollständige Arbeitsoberfläche, Gemeinsamer Login-Stack mit Rollentrennung, Dynamische Mobile Floating Actions.

## Architecture
- **API-First**: Domain → Channel → Connector → Agent → Event/Audit Layer
- **Unified Auth**: /login → Admin (Passwort) / Kunde (Magic Link) → Role-based JWT
- **mem0 Memory Layer**: Pflicht-Scoping (user_id, agent_id, app_id, run_id)
- **KI-Orchestrator**: GPT-5.2 via Emergent LLM Key (MOCKED, temporär)

## What's Implemented (Verifiziert)

### Public Header Login-Button (2026-04-03) — VERIFIZIERT
- "Anmelden" mit Login-Icon zwischen Sprachumschalter und CTA
- Desktop: Text + Icon, Tablet: Text + Icon, Mobile: Icon-only + "Anmelden" im Burger-Menü
- i18n: DE=Anmelden, NL=Inloggen, EN=Login
- Keine Kollision mit Sprachumschalter/CTA/Burger

### Unified Login /login (2026-04-03) — VERIFIZIERT
- Allgemeine Auth-Seite (nicht mehr isolierter Admin-Login)
- NeXifyAI Home-Link oben links
- Legal-Links: Startseite, Impressum, Datenschutz, AGB
- Admin-Flow: E-Mail → Rollen-Badge "Interner Zugang" → Passwort → /admin
- Kunden-Flow: E-Mail → Magic Link per E-Mail → /portal
- Unbekannt: Fehlermeldung
- Session/Logout/Redirect sauber

### Rollentrennung (2026-04-03) — VERIFIZIERT
- Admin-JWT (role=admin) → Admin-Panel
- Customer-JWT (role=customer) → Kundenportal
- Customer-JWT → 403 auf Admin-Endpoints
- Serverseitig: get_current_admin vs get_current_customer
- UI-seitig: Separate Routen, Separate Views

### Admin CRM — Vollständige Arbeitsoberfläche — VERIFIZIERT
- Leads: CRUD, Kunden: CRUD, Angebote: CRUD (Rabatt/Sonderpositionen)
- Rechnungen: CRUD, Termine: CRUD, Slots blockieren
- Kommunikation, KI-Agenten, Audit, Timeline

### Dynamische Mobile Floating Actions — VERIFIZIERT
- Cookie-zustandsbasiert, smooth CSS transition, z-index 910, Safe-Area iOS

### Kommerzielle Konsistenz — PDFs — VERIFIZIERT (Code)
- Quote-PDF: Rabatt + Sonderpositionen
- Invoice-PDF: Rabatt + Sonderpositionen

### Customer Portal (JWT-Auth) — VERIFIZIERT
- Dashboard, Angebote, Rechnungen, Termine, Kommunikation, Timeline
- Logout-Button, Login-Link bei Fehler

### mem0 Memory Layer — VERIFIZIERT
- MemoryService, 13 Agent-IDs, automatische Writes

### KI-Orchestrator — VERIFIZIERT (MOCKED: GPT-5.2)

## Pending Tasks
- P1: Breakpoint-Testing (11 Breakpoints: 1920→360)
- P1: Worker/Monitoring/Alerting/Trigger nachweisen
- P1: Orchestrator-Architektur dokumentieren
- P1: Admin/Portal UX Feintuning
- P1: Email-Signatur & DSGVO-Footer
- P2: Outbound Lead Machine
- P2: server.py Refactoring

## Testing Status
- Iteration 21: 100% | Iteration 22: 100% | Iteration 23: 100% | Iteration 24: 100%
