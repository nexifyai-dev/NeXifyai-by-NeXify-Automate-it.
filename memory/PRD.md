# NeXifyAI — Product Requirements Document

## Originaler Auftrag
B2B-Plattform "Starter/Growth AI Agenten AG" (NeXifyAI) — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator. Premium-Architektur mit absolutem Fokus auf Produktionsreife, Sicherheit und System-Konsistenz.

## Architektur
- **Frontend**: React 18 SPA, Framer Motion, i18n (DE/NL/EN), Shadcn-Style Dark Theme
- **Backend**: FastAPI (modular: 10 Route-Module), APScheduler, MongoDB
- **Workers**: In-process JobQueue (4 Workers, Retry + Dead-Letter), Cron-Scheduler (7 Jobs)
- **LLM**: DeepSeek (Primär, aktiv), GPT-5.2 Fallback via Emergent
- **Payments**: Revolut (EINZIGER Provider — Stripe vollständig entfernt)
- **Storage**: Object Storage via emergentintegrations
- **Email**: Hostinger SMTP (aiosmtplib) — nexifyai@nexifyai.de
- **Security**: JWT Auth, Rate Limiting (SlowAPI 200/min), Security Headers, CORS
- **Oracle**: Memory Service, get_contact_oracle(), Snapshot
- **Design-System**: Vollständiges Token-System (CI-Gelb, CI-Blau, 3-Stufen-Schatten, 7-Stufen-Radien, Glass-Morphism)

## Implementierte Features

### Stripe-Entfernung (verifiziert Iteration 53)
- Alle Stripe-Endpoints entfernt (billing_routes.py)
- STRIPE_API_KEY und STRIPE_WEBHOOK_SECRET aus .env entfernt
- Monitoring zeigt nur Revolut als Payment Provider
- Admin-UI zeigt keine Stripe-Karte mehr

### Kunden-Fallakte (verifiziert Iteration 53)
- `/api/admin/customers/{email}/casefile` — Vollständige Aggregation (Kontakt, Leads, Buchungen, Angebote, Rechnungen, Verträge, Kommunikation, Timeline, E-Mails, Memory)
- `/api/admin/email/send` — Direkt-E-Mail-Versand aus Admin (SMTP)
- `/api/admin/customers/{email}/note` — Notizen zur Fallakte
- `/api/admin/customers/{email}/contact` — Kontaktdaten aktualisieren
- Frontend: 8-Tab Fallakte (Übersicht, Anfragen, Angebote, Rechnungen, Verträge, E-Mail, Notizen, Aktivität)
- Stat-Leiste mit 6 KPIs pro Kunde
- Direkt-E-Mail-Formular mit Empfänger, Betreff, Nachricht
- Gesendete-E-Mails-Log mit Timestamps und Status

### Design-System (verifiziert Iteration 52)
- Vollständiges CSS-Token-System in :root
- CI-Gelb (#ff9b7a) + CI-Blau (#6B8AFF)
- 9 Button-Typen, 5 Größen, Loading/Disabled States
- Unified Surface-System mit Glass-Morphism
- Systemweite Harmonisierung (Admin, Portal, Public identische Qualität)

### Backend (verifiziert)
- 10 modulare Route-Module
- Worker/Scheduler-Layer
- Oracle/Memory Service
- Dual-Role Auth (role:dual)
- Hostinger SMTP Integration

### Frontend (verifiziert)
- Landing Page (12 Sektionen), Unified Login (Dual-Role), Termin-Seite
- Admin Dashboard: Collapsible Sidebar, System-Health, Lead-Management, Kunden-Fallakte
- Customer Portal: 8 Tabs

## E2E-Prozesskette (verifiziert)
Lead → Booking → Quote → Invoice → Contract → Payment (Revolut)

## Testing (6 Iterationen, alle 100%)
- Iteration 48-50: Backend + Frontend
- Iteration 51: Dual-Role Login + Sidebar Collapse
- Iteration 52: Design-System Harmonisierung
- Iteration 53: Stripe Removal + Kunden-Fallakte + E-Mail + Notizen

## Nächste Schritte
1. Content & Copywriting Overhaul
2. Network, Security & Configuration Hardening
3. E2E Browser Verifications (Quote→Invoice)
4. DeepSeek Live-Migration
5. Next.js Migration, PydanticAI

## Credentials
- Admin: p.courbois@icloud.com / 1def!xO2022!!
