# NeXifyAI — Product Requirements Document

## Problem Statement
B2B-Plattform "Starter/Growth AI Agenten AG" mit API-First Architektur. Unified Communication Layer (Chat, Mail, WhatsApp, Portal), Deep Customer Memory (mem0), KI-Orchestrator mit 9 Sub-Agents, Automated B2B Outbound Lead Machine, Live Admin CRM mit Audit-System.

## Source of Truth — Gesamtkonzept
Drei Referenzdokumente definieren die Gesamtanforderung:
1. `NeXifyAI_Emergent_Auftrag_Premium_FineTuned_20260403.txt` — Auftragsspezifikation
2. `NeXifyAI_Gesamtkonzept_Premium_FineTuned_20260403 (1).md` — Architektur & Features
3. `NeXifyAI_Gesamtkonzept_Premium_FineTuned_20260403 (2).md` — Design System, Format, QA
4. `NeXifyAI_Emergent_Zusatzauftrag_Memory_Beweispflicht_20260403.txt` — Memory & Beweispflicht

## Architecture
- **API-First**: Domain Layer, Channel Layer, Connector Layer, Agent Layer, Event/Audit Layer
- **WhatsApp Bridge**: QR-Pairing als isolierter Connector, austauschbar gegen offizielle API
- **Unified Communications**: AI-Chat, Email, WhatsApp, Portal in einer Timeline/Identity
- **KI-Orchestrator**: GPT-5.2 via Emergent LLM Key mit 9 Sub-Agents
- **Audit System**: Health-Checks, Timeline, Self-Healing
- **mem0 Memory Layer**: Pflicht-Scoping mit user_id, agent_id, app_id, run_id

## Tech Stack
- Frontend: React 18 SPA
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- LLM: Emergent LLM Key (OpenAI GPT-5.2)
- Email: Resend API (nexifyai@nexifyai.de)
- Memory: mem0-konformer MemoryService (backend/memory_service.py)

## Agent Layer (9 Agenten + Emergent Build Agent)
1. Intake — Leadaufnahme, Discovery, Klassifikation (intake_agent)
2. Research — Firmenanalyse, Lead-Enrichment (research_agent)
3. Outreach — Personalisierte Erstansprache, Follow-ups (outreach_agent)
4. Offer — Angebotserstellung, Tarifberatung (offer_agent)
5. Planning — Projektplanung, Architektur, Build-Handover (planning_agent)
6. Finance — Rechnungsstellung, Zahlungen, Mahnwesen (finance_agent)
7. Support — Kundenbetreuung, Problemlösung (support_agent)
8. Design — Design-Konzeption, Content-Strategie, SEO (design_agent)
9. QA — Qualitätssicherung, Audit, Selbstheilung (qa_agent)
10. Emergent Build — Build-Agent-Identität (emergent_build_agent)

## Tariffs (Source of Truth)
- Starter AI Agenten AG: 499 EUR/Monat, 24 Mo, 30% Anzahlung (3.592,80 EUR)
- Growth AI Agenten AG: 1.299 EUR/Monat, 24 Mo, 30% Anzahlung (9.352,80 EUR)
- Websites: Starter 2.990, Professional 7.490, Enterprise 14.900
- Apps: MVP 9.900, Professional 24.900
- SEO: Starter 799/Mo (6 Mo), Growth 1.499/Mo (6 Mo)
- Bundles: Digital Starter 3.990, Growth Digital 17.490, Enterprise Digital ab 39.900

## What's Implemented

### WhatsApp Button (DONE)
- Desktop: Vertikal, flush links, Abrundung rechts, Rotation-kompensiert
- Tablet: Angepasste Größe, Content Safe Area
- Mobile: Horizontaler Pill → 48px Kreis, bottom:120px, side-by-side mit Chat
- Admin/Portal: Versteckt via body.hide-wa

### Mobile Floating Actions (DONE — 2026-04-03)
- WhatsApp + Chat side-by-side unten rechts auf Mobile (<768px)
- WA: right:72px, Chat: right:16px, bottom:120px
- z-index: 910 (über Cookie-Banner 300)
- Safe-Area-kompatibel (iOS)
- Keine Kollision mit Cookie-Banner, Browser-Toolbars
- Touch-optimiert: 48x48px Kreise

### Admin CRM (DONE)
- 11 Sidebar-Tabs: Dashboard, Commercial, Leads, Kommunikation, AI-Chats, WhatsApp, Timeline, Kalender, Kunden, KI-Agenten, Audit
- WhatsApp Connect mit QR-Pairing, Messaging, Session-Management
- Conversations View mit Inline-Reply
- KI-Agenten View mit Task-Execution, Memory-Injection
- Audit View mit Health-Checks, Timeline, Collection-Stats

### Manual CRM (DONE — 2026-04-03)
- POST /api/admin/customers — Manuell Kunden anlegen (Lead + Contact + Memory)
- POST /api/admin/customers/portal-access — Magic Link Portalzugang generieren
- POST /api/admin/leads — Manuell Leads anlegen
- POST /api/admin/quotes — Angebote erstellen (mit Rabatt + Sonderpositionen)
- Admin UI: Kunden-Tab mit Formular, Suche, Detail-Ansicht, Portal-Button

### mem0 Memory Layer (DONE — 2026-04-03)
- MemoryService (backend/memory_service.py) als zentraler Pflicht-Layer
- Pflicht-Scoping: user_id, agent_id, app_id, run_id pro Eintrag
- 13 definierte Agent-IDs (AGENT_IDS Dictionary)
- read/write/search/get_agent_history Methoden
- Automatische Memory-Writes im Chat-Flow (Interesse, Buchung, Angebot)
- Admin API: GET /api/admin/memory/agents, /by-agent/{id}, /search
- Beweispflicht: verification_status Feld (verifiziert/teilweise/nicht verifiziert/widerlegt)

### Customer Portal (DONE)
- 6 Tabs: Übersicht, Angebote, Rechnungen, Termine, Kommunikation, Aktivität
- Quote Accept/Decline/Revision via Magic Link
- Communication Tab (Chat + Unified Conversations)
- Timeline/Activity Tab
- PDF-Downloads

### KI-Orchestrator + 9 Sub-Agents (DONE)
- Orchestrator mit GPT-5.2 Routing
- 9 spezialisierte Agenten mit eigenem System-Prompt
- Audit Trail in Timeline Events
- Customer Memory Injection

### Premium Admin Login (DONE)
- Redesigned Login Screen
- Komplett auf Deutsch

## Pending / Upcoming Tasks
- P1: Kommerzielle Konsistenz (discount_percent + special_items in PDFs, Portal, Rechnungen)
- P1: Breakpoint-Testing über alle 11 Breakpoints (1920→360)
- P1: Email-Signatur-Standards & DSGVO-Footer
- P1: Rollentrennung Customer/Admin verifizieren
- P2: Outbound Lead Machine (Automatisiertes Lead-Enrichment, Scoring, Email-Outreach)
- P2: Email-Professionalisierung (Zentrale KI-Orchestrierung aller Emails)
- P2: Kanalübergreifender Kommunikationskern vollenden
- P2: Revolut/Billing/Status-Sync (Quote → Invoice → Payment → App-Status)
- P2: Responsive Fine-Tuning über alle Breakpoints
- P2: server.py Refactoring → modulare Struktur (/routes, /agents, /services)
