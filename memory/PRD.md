# NeXifyAI — Product Requirements Document

## Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator, Manuelles CRM als vollständige Arbeitsoberfläche, Gemeinsamer Login-Stack mit Rollentrennung, Dynamische Mobile Floating Actions.

## Architecture
- **API-First**: Domain Layer, Channel Layer, Connector Layer, Agent Layer, Event/Audit Layer
- **Unified Auth**: Gemeinsamer Login-Stack (/login) → Admin (Passwort) / Kunde (Magic Link) → Role-based JWT
- **mem0 Memory Layer**: Pflicht-Scoping (user_id, agent_id, app_id, run_id)
- **KI-Orchestrator**: GPT-5.2 via Emergent LLM Key mit 9 Sub-Agents (MOCKED)

## Tech Stack
- Frontend: React 18 SPA | Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB (nexifyai) | LLM: Emergent LLM Key (GPT-5.2)
- Email: Resend API | Memory: mem0-konformer MemoryService

## What's Implemented (Verifiziert)

### Unified Auth Stack (2026-04-03) — VERIFIZIERT
- **POST /api/auth/check-email** → role=admin/customer/unknown
- **POST /api/auth/request-magic-link** → E-Mail mit Magic Link
- **POST /api/auth/verify-token** → JWT mit role=customer
- **POST /api/admin/login** → JWT mit role=admin
- **Rollentrennung**: Customer-JWT ≠ Admin-JWT, serverseitig + UI-seitig
- **Unified Login Page** (/login): Admin-Passwort-Flow + Kunden-Magic-Link-Flow
- **Session-Ablauf**: JWT mit Ablaufzeit, Logout löscht localStorage

### Customer Portal — JWT-Auth (2026-04-03) — VERIFIZIERT
- **GET /api/customer/me** — Kundenprofil
- **GET /api/customer/dashboard** — Angebote, Rechnungen, Termine, Kommunikation, Timeline
- JWT + Legacy Magic Link Token Support
- Logout-Button → /login
- Ohne Auth → Fehlermeldung + Login-Link

### Admin CRM — Vollständige Arbeitsoberfläche (2026-04-03) — VERIFIZIERT
- Leads: CRUD (Anlegen, Bearbeiten, Status, Notizen)
- Kunden: CRUD (Anlegen, Bearbeiten, Portalzugang)
- Angebote: CRUD (Erstellen, Bearbeiten, Rabatt, Sonderpositionen, Versenden, Kopieren, PDF)
- Rechnungen: CRUD (Erstellen, Bearbeiten, Status, Als bezahlt, Versenden, PDF)
- Termine: CRUD (Manuell anlegen, Bearbeiten, Status)
- Slots blockieren, Kommunikation einsehen + antworten, KI-Agenten, Audit

### Dynamische Mobile Floating Actions (2026-04-03) — VERIFIZIERT
- Cookie sichtbar → bottom:120px, Cookie weg → bottom:24px
- Smooth CSS transition 0.4s cubic-bezier
- body.cookie-visible Klasse steuert Position
- z-index 910, Safe-Area iOS

### Kommerzielle Konsistenz — PDFs (2026-04-03) — TEILWEISE VERIFIZIERT
- Rabatt-Zeile in generate_quote_pdf (Codeebene verifiziert)
- Sonderpositionen in generate_quote_pdf (Codeebene verifiziert)
- Netto-Bereinigung nach Rabatt/Sonderpositionen
- Invoice PDF: noch zu prüfen (separate Funktion)

### mem0 Memory Layer (2026-04-03) — VERIFIZIERT
- MemoryService mit agent_id Scoping, 13 Agent-IDs
- Automatische Writes bei: Login, Kundenanlage, Portalzugang, Chat

### KI-Orchestrator + 9 Sub-Agents — VERIFIZIERT
- GPT-5.2 via Emergent LLM Key (MOCKED, nicht finaler Zielzustand)

## Key Endpoints
Auth: POST /api/auth/check-email, /api/auth/request-magic-link, /api/auth/verify-token
Admin: POST /api/admin/login, GET /api/admin/me, /leads, /customers, /quotes, /invoices, /bookings
Customer: GET /api/customer/me, /api/customer/dashboard
CRUD: PATCH /api/admin/leads/{id}, /customers/{email}, /quotes/{id}, /invoices/{id}

## Pending Tasks (nach Priorität)
- P1: Invoice PDF Rabatt/Sonderpositionen synchronisieren
- P1: Breakpoint-Testing (11 Breakpoints: 1920→360)
- P1: Worker/Monitoring/Alerting/Trigger nachweisen
- P1: Orchestrator-Architektur dokumentieren
- P1: Admin/Portal UX Feintuning
- P1: Email-Signatur & DSGVO-Footer
- P2: Outbound Lead Machine, server.py Refactoring

## Testing Status
- Iteration 21: 100% (19/19) — Customer/Portal/mem0
- Iteration 22: 100% (23/23) — Full CRUD + Dynamic Floating
- Iteration 23: 100% (20/20) — Unified Auth + Customer Portal + Role Separation
