# NeXifyAI — Product Requirements Document

## Produkt
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator (DeepSeek).

## Architektur
- **Frontend**: React 18 SPA
- **Backend**: FastAPI (Python 3.11) — Modular Route Architecture
- **Datenbank**: MongoDB (Motor async)
- **LLM**: DeepSeek (Primär), GPT-5.2 (Fallback via Emergent)
- **Object Storage**: Emergent Object Storage
- **Payments**: Stripe (via emergentintegrations)
- **E-Mail**: Resend (mit Audit-Trail)

## Modulare Backend-Architektur (v3.1)
```
server.py (Orchestrator)
routes/
├── shared.py (State Container S, Auth, Helpers)
├── auth_routes.py, public_routes.py, admin_routes.py
├── billing_routes.py, portal_routes.py, comms_routes.py
├── contract_routes.py, project_routes.py
├── outbound_routes.py, monitoring_routes.py
```

## Implementierungsstatus

### P0 — Backend Modular Refactoring (Abgeschlossen)
- 6530 Zeilen Monolith → 10 modulare Route-Dateien
- Testing Iteration 40: 100% Pass

### P1 — UnifiedLogin Premium (Abgeschlossen — 2026-02-04)
- 2-Spalten-Design, Framer-motion, Trust-Badges
- Testing Iteration 41: 100% Pass (14/14)

### P2 — Chat-Bug + Mobile Floating Buttons (Abgeschlossen — 2026-02-04)
- get_system_prompt() + generate_response_fallback() repariert
- body.chat-open Klasse für Mobile-Button-Steuerung
- Testing Iteration 42: 100% Pass

### P3 — Chat-Interface Premium Perfektionierung (Abgeschlossen — 2026-02-04)
- **Desktop**: 2-Spalten-Layout (260px Sidebar + Main), NeXifyAI Brand in Sidebar mit Logo + Rollenbezeichnung, Preset-Buttons, CTA-Buttons, "Neue Unterhaltung"-Button
- **Messages**: Assistant-Avatar (NeXifyAI Logo), Sender-Labels (KI-Berater / Sie), Timestamps, Markdown-Rendering
- **Input**: Disclaimer-Zeile "KI-gestützter Assistent. Keine rechtsverbindlichen Zusagen."
- **Mobile (Full-Screen)**: Eigener Header mit Zurück-Pfeil + Brand + Status-Dot, Pill-Input, runder Send-Button, safe-area-inset
- **Tablet**: Sauberer Breakpoint-Übergang bei 768px
- **Floating Buttons**: Ausblenden bei Chat-Öffnung auf Mobile (<767px)
- Custom Scrollbar für Chat-Messages
- Testing Iteration 43: 100% Pass (18/18)

### P4 — Rechtliche Vervollständigung (Abgeschlossen — 2026-02-04)
- Datenschutz: Doppelte Sektion 4 behoben (jetzt 4-Datensicherheit, 5-Ihre Rechte, 6-Cookies)
- LegalPages.js Syntax-Fehler (doppelte Zeilen am Ende) behoben
- Alle 4 Legal-Seiten verifiziert: Impressum, Datenschutz, AGB, KI-Hinweise (DE/NL/EN)
- Footer-Links zu allen 4 Legal-Seiten verifiziert
- Cookie-Banner Datenschutz-Link verifiziert
- Übersetzungskonsistenz: sidebarRole in DE→KI-Berater, NL→AI-Adviseur, EN→AI Advisor

## Offene Punkte
- Stripe Webhook Secret (benötigt Produktionskey vom Kunden)
- Master-Auftrag Items (P1 Upcoming)
- Next.js Migration, PydanticAI, LiteLLM, Temporal (Ziel-Stack)

## Admin Credentials
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!
