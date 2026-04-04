# NeXifyAI — Product Requirements Document

## Originaler Auftrag
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium-Architektur mit absolutem Fokus auf Produktionsreife, Sicherheit und System-Konsistenz. Vollumfänglicher System-Audit mit 42-Sektionen-Systemprompt durchgeführt.

## Architektur
- **Frontend**: React 18 SPA, Framer Motion, i18n (DE/NL/EN), Shadcn-Style Dark Theme
- **Backend**: FastAPI (modular: 10 Route-Module), APScheduler, MongoDB
- **Workers**: In-process JobQueue (4 Workers, Retry + Dead-Letter), Cron-Scheduler (7 Jobs)
- **LLM**: DeepSeek (Primär, aktiv), GPT-5.2 Fallback via Emergent
- **Integrations**: Stripe, Object Storage, Hostinger SMTP (aiosmtplib)
- **Security**: JWT Auth, Rate Limiting (SlowAPI 200/min), Security Headers, CORS
- **Oracle**: Memory Service (182 Einträge), get_contact_oracle(), Snapshot

## Implementierte Features (kumulativ, verifiziert bis Iter. 51)

### Backend
- Modulare Route-Architektur (10 Route-Module: auth, public, admin, billing, portal, comms, contract, project, outbound, monitoring)
- Worker/Scheduler-Layer: 8 Handler, 7 Scheduler-Jobs
- Oracle/Memory Service: write_classified, get_contact_oracle(), Oracle Snapshot
- Billing Overview Dashboard, Outbound Campaigns, Monitoring Aliases, Memory Stats
- Rate Limiting (SlowAPI 200/min), Security Headers (CSP, X-Frame, XSS, Referrer, Permissions)
- Triple-secured action logic (MongoDB + Timeline + Memory Audit)
- QuoteRequest-Model (discount_percent, customer_industry, use_case, special_items)
- Invoice-aus-Quote (upfront_eur, auto-Beschreibung, Typ-Support activation/recurring)
- Contract-aus-Quote (auto-Populate Kundendaten, Tarif, Kalkulation)
- System Health Endpoint (Workers, Scheduler, Memory, DB, LLM, Agents)
- Hostinger SMTP Integration (Booking, Registration, Quotes, Magic Links)
- Dual-Role Auth: check-email returns role:dual wenn User Admin + Kunde ist

### Frontend
- Landing Page: 12 Sektionen mit Premium Dark Theme
- Standalone Termin-Seite (/termin): 2-Spalten, Trust-Signale, i18n
- Unified Login: 2-Spalten, DSGVO-Checkbox, Trust-Row, Booking-CTA nach Registrierung
- Dual-Role Login: Rollenauswahl (Administration / Kundenportal) für Dual-User
- BookingModal: 2-Step Premium
- LiveChat: KI-gestützt, responsive (Desktop + Mobile Full-Screen)
- Legal Pages: Impressum, Datenschutz, AGB, KI-Hinweise (DE/NL/EN)
- Animated Pricing mit Custom Quote Request
- Customer Portal: 8 Tabs (Übersicht, Verträge, Projekte, Angebote, Finanzen, Termine, Kommunikation, Aktivität)
- Admin Dashboard: System-Health-Panel (6 Karten), Lead-Management, Billing, CRM
- Admin Sidebar: Collapsible (Logo sichtbar, Edge-Float Toggle, Icon-Only Navigation)
- Quote Portal

## E2E-Prozesskette (verifiziert)
Lead -> Booking -> Quote -> Invoice -> Contract -> Payment
- Contact-Formular -> Lead
- Termin-Buchung -> Booking
- KI-Chat -> Response
- Quote-Anfrage -> Lead + Anfrage
- Admin: Quote -> Invoice (korrekte Beträge)
- Admin: Quote -> Contract (auto-populate)

## Testing (4 Iterationen, alle 100%)
- Iteration 48: 30/30 Backend + Frontend
- Iteration 49: 25/25 Backend + Frontend
- Iteration 50: 35/35 Backend + Frontend
- Iteration 51: 7/7 Dual-Role Login + Sidebar Collapse

## Nächste Schritte (Backlog)
1. P2: Portal-Harmonisierung & Dynamische Bedarfsliste
2. P2: Content & Copywriting Overhaul
3. P3: Network, Security & Configuration Hardening (CORS, Rate Limiting, Firewall)
4. P3: E2E Browser Verifications (Quote to Invoice)
5. P4: DeepSeek Live-Migration
6. P5: Next.js Migration, PydanticAI

## Credentials
- Admin: p.courbois@icloud.com / 1def!xO2022!!
