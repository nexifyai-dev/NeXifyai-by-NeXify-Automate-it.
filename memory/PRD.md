# NeXifyAI — Product Requirements Document

## Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator (DeepSeek Ziel), CRM, Login-Stack, Worker/Scheduler, Kommunikationskern, Outbound Lead Machine, Billing-Sync.

## Architecture
- **API-First**: Domain → Channel → Connector → Agent → Event/Audit Layer
- **Unified Auth**: /login → Admin (Passwort) / Kunde (Magic Link) / Registrierung → Role-based JWT
- **Security by Obscurity**: /admin → /login redirect, keine internen Terminologien öffentlich
- **mem0 Memory Layer**: Pflicht-Scoping (user_id, agent_id, app_id, run_id)
- **LLM-Abstraktionsschicht**: EmergentGPTProvider (TEMPORÄR) | DeepSeekProvider (ZIEL)
- **Worker/Scheduler**: asyncio JobQueue (4 Worker) + APScheduler (7 Cron-Jobs)
- **Services**: CommunicationService, BillingService, OutboundLeadMachine

## What's Implemented & Verified

### P0: Security by Obscurity — VERIFIZIERT (Iteration 26: 100%)
- /login: Neutral "Sicherer Zugang", keine Admin/Operator/Agenten-Terminologie
- /admin ohne Auth → neutral redirect zu /login
- Admin-Login im Admin.js komplett entfernt (zeigt kein "9 KI-Agenten", "Interner Zugang" etc.)
- Rollen-Badge zeigt "Verifizierter Zugang" statt "Admin-Bereich"
- Registration-Step für unbekannte E-Mails (Angebotsanfragen)

### P1: Premium Login UX (Doppelspaltig) — VERIFIZIERT (Iteration 26: 100%)
- Linke Spalte: NEXIFYAI Brand-Visual mit Orb-Animationen, Grid-Pattern, Features (Verschlüsselt, Echtzeit, DSGVO)
- Rechte Spalte: Formular mit E-Mail-Check, Passwort-Step, Magic-Link-Step, Registration-Step
- Legal Links: Startseite, Impressum, Datenschutz, AGB
- Responsive: Desktop=Split, Tablet=vertikal, Mobile=kompakt
- Registration: Vorname*, Nachname*, Unternehmen, Telefon, Nachricht → POST /api/contact

### P2: Mobile Menu Overlay — VERIFIZIERT (Iteration 26: 100%)
- Vollständig opaker Hintergrund (#0a0e14), kein Content-Bleed-through
- position:absolute mit height:calc(100dvh - var(--nav-h)) (backdrop-filter Containing-Block-Fix)
- Kein doppelter Language Switcher
- Saubere Close-Animation (X)
- "Anmelden" Link + "Beratung starten" CTA im Menü

### P3: Dynamische Floating Actions — VERIFIZIERT (Iteration 26: 100%)
- body.mobile-menu-open → visibility:hidden für WA + Chat
- body.cookie-visible → bottom:120px
- Standard → bottom:24px
- Zustandsabhängig, keine Kollisionen, keine Geisterabstände

### P4: 3D-Szenen Verbesserung — VERIFIZIERT (Iteration 26: 100%)
- HeroScene: FloatingCore (Wireframe-Ikosaeder mit Orbits, glühender Kern), NetworkNodes (160 Partikel), NetworkEdges (200 Lines), DataStreams (600 Spiralpartikel), AccentGeometries (schwebende Kugeln, Tori, Oktaeder)
- IntegrationsGlobe: Wireframe-Kugel mit Äquatorial-/Polar-/Schrägringen, Connection-Arcs, Nodes
- ProcessScene: 4 Hubs mit Wireframe-Ikosaedern + Orbiting-Ringen, FlowStreams, FlowConnectors
- Stärkere Beleuchtung (4 Point-Lights), höhere Opazität, deutlich sichtbare 3D-Tiefe

### Auth & Login — VERIFIZIERT
- Admin-Flow: E-Mail → Passwort → /admin
- Kunden-Flow: E-Mail → Magic Link → /portal
- Registration-Flow: E-Mail → Formular → Account-Erstellung
- JWT Rollentrennung, Rate-Limiting

### Admin CRM — VERIFIZIERT
- Leads/Kunden/Angebote/Rechnungen/Termine CRUD
- Rabatt, Sonderpositionen, Status, Timeline

### Worker/Scheduler-Layer — VERIFIZIERT (Iteration 25: 100%)
- JobQueue: 4 Worker, PriorityQueue, MongoDB-Persistenz, Retry, Dead-Letter, Crash-Recovery
- 8 Handler: send_email, payment_reminder, dunning_escalation, lead_followup, booking_reminder, quote_expiry, ai_task, status_transition
- 7 Scheduler-Jobs: Zahlungsreminder, Mahnvorstufen, Lead-Follow-ups, Buchungserinnerungen, Angebotsablauf, Health-Check, Dead-Letter-Alert

### Kommunikationskern — VERIFIZIERT (Iteration 25: 100%)
- CommunicationService: Unified Identity, Cross-Channel Threads, Routing, Entity-Verknüpfung

### Outbound Lead Machine — VERIFIZIERT (Iteration 25: 100%)
- Pipeline: Discovery → Vorqualifizierung → Analyse → Scoring → Legal Gate → Outreach → Follow-up
- Suppression-Liste, DSGVO/UWG-Gate

### Billing Status-Sync — VERIFIZIERT (Iteration 25: 100%)
- BillingService: Quote→Invoice→Payment Sync, idempotente Webhooks

### LLM-Abstraktionsschicht — VERIFIZIERT (Iteration 25: 100%)
- Provider-agnostisch, Factory-Pattern, DeepSeek Migration via ENV

### E-Mail-Signatur / DSGVO-Footer — VERIFIZIERT (Code-Review)
- Zentrale email_template() mit konsistenter Signatur
- Impressum/Datenschutz/AGB Links korrekt
- DSGVO (EU) 2016/679 Hinweis
- Firmendaten: NeXify Automate, Venlo NL, KvK: 90483944

## Testing Status
- Iteration 25: 100% — 30/30 Backend-Tests
- Iteration 26: 100% — 11/11 Frontend-Tests

## Commercial Source of Truth
| Tarif | Kennung | Preis | Laufzeit | Anzahlung |
|-------|---------|-------|----------|-----------|
| Starter AI Agenten AG | NXA-SAA-24-499 | 499 EUR/Mo | 24 Mo | 30% = 3.592,80 EUR |
| Growth AI Agenten AG | NXA-GAA-24-1299 | 1.299 EUR/Mo | 24 Mo | 30% = 9.352,80 EUR |

## Remaining Tasks (Priorisiert)
1. **P1**: Projektchat/Handover-Kontext härten
2. **P2**: Contract Operating System v1 (Mastervertrag, Anlagen, digitale Signatur)
3. **P3**: Revolut/Stripe Live-Webhooks
4. **P4**: DeepSeek Live-Migration
5. **P5**: Legal & Compliance Guardian operativ verdrahten
6. **P6**: Outbound Lead Machine auf Produktionsnähe härten
7. **P7**: server.py Refactoring (>4200 Zeilen → modulare Routen)
