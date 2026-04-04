# NeXifyAI — ROADMAP & Dynamische Bedarfsliste

## Status: Produktionsreife-Tracking

### Verifiziert (Done)
- [x] Modulare Backend-Architektur (10 Route-Module)
- [x] Worker/Scheduler-Layer (4 Workers, 7 Cron-Jobs)
- [x] Oracle/Memory Service (write_classified, get_contact_oracle, Snapshot)
- [x] E2E-Prozesskette: Lead → Booking → Quote → Invoice → Contract
- [x] Rate Limiting (SlowAPI 200/min)
- [x] Security Headers (CSP, X-Frame-Options, XSS, Referrer-Policy)
- [x] Standalone Termin-Seite (/termin) mit Trust-Signalen
- [x] BookingModal (2-Step-Premium)
- [x] Unified Login (2-Spalten, DSGVO-Checkbox, Trust-Signale)
- [x] Admin System-Health-Panel
- [x] Customer Portal (8 Tabs: Übersicht, Verträge, Projekte, Angebote, Finanzen, Termine, Kommunikation, Aktivität)
- [x] Chat-UI Responsive (Full-Screen Mobile, safe-area, Touch-Targets)
- [x] Legal Pages (Impressum, Datenschutz, AGB, KI-Hinweise) — DE/NL/EN
- [x] Animated Pricing mit Custom Quote Request
- [x] QuoteRequest-Model gefixt (discount_percent, customer_industry)
- [x] Invoice-aus-Quote-Erstellung gefixt (upfront_eur)
- [x] Contract-aus-Quote-Erstellung gefixt (auto-populate)
- [x] Footer-Links vollständig und korrekt
- [x] Portal Mobile-Tabs optimiert

### P0 — Kritische Betriebsanforderungen
- [ ] Stripe Webhook-Integration (Live-Zahlungssynchronisation)
- [ ] E-Mail-Benachrichtigungen (Bestätigung, Erinnerung, Statuswechsel) — benötigt Resend API-Key
- [ ] PDF-Generierung für Quotes/Invoices/Contracts (Object Storage)
- [ ] Automatische Status-Übergänge (Quote sent → accepted → invoiced → paid)

### P1 — Betriebsoptimierung
- [ ] DeepSeek Live-Migration (ersetze GPT-5.2 Fallback) — benötigt DeepSeek API-Key
- [ ] Stripe Live-Webhooks für Zahlungsstatus-Sync
- [ ] Revolut-Integration als Zahlungsalternative
- [ ] Admin E-Mail-Dashboard (Send-Status, Delivery, Bounces)
- [ ] Automatische Mahnungssequenz (Dunning Flow: 7/14/30 Tage)
- [ ] Projekt-Chat mit Datei-Upload

### P2 — UX/Content-Perfektionierung
- [ ] Multi-Language Landing Page Content-Review (DE primär, NL/EN sekundär)
- [ ] Onboarding-Flow für neue Kunden nach Registrierung
- [ ] Admin-Dashboard: Umsatz-Charts (Monat/Quartal/Jahr)
- [ ] Kundenportal: Dokumenten-Download-Center
- [ ] Service-Level-Agreement-Anzeige im Portal

### P3 — Architektur-Evolution
- [ ] Next.js Migration (SSR, SEO-Optimierung, Performance)
- [ ] PydanticAI + LiteLLM + Temporal Adoption
- [ ] Database Indexierung für Performance (Queries > 100ms)
- [ ] CDN-Setup für Static Assets
- [ ] Backup-Strategie für MongoDB

### P4 — Compliance & Legal
- [ ] Legal & Compliance Guardian (operative Verdrahtung)
- [ ] Cookie-Consent-Management (TTDSG-konform)
- [ ] Auftragsverarbeitungsvertrag (AVV) automatisch generieren
- [ ] Löschkonzept nach DSGVO Art. 17 implementieren

### Offene Konfigurationsanforderungen
| Bereich | Benötigt | Status |
|---------|----------|--------|
| DeepSeek API Key | Benutzer muss bereitstellen | Ausstehend |
| Stripe Live Keys | Benutzer muss bereitstellen | Ausstehend |
| Revolut API | Benutzer muss bereitstellen | Ausstehend |
| Resend API Key | Benutzer muss bereitstellen | Ausstehend |
| Produktions-Domain | DNS-Konfiguration | Ausstehend |
| CORS Restriction | Domain muss feststehen | Ausstehend |

### Risiken & Restschulden
| Risiko | Kritikalität | Abhängigkeit | Maßnahme |
|--------|-------------|--------------|----------|
| Keine E-Mail-Zustellung | Hoch | Resend API Key | Fallback: Manual E-Mail |
| Keine Live-Zahlungen | Hoch | Stripe Live Keys | Aktuell: Manuelle Erfassung |
| DeepSeek nicht aktiv | Mittel | DeepSeek API Key | Fallback: GPT-5.2 via Emergent |
| CORS offen für alle Origins | Mittel | Produktions-Domain | Einschränkung bei Go-Live |
| Keine automatischen Backups | Mittel | Ops-Entscheidung | MongoDB Atlas Auto-Backup |

### Monitoring-Status
| Komponente | Status | Letzte Prüfung |
|-----------|--------|----------------|
| API Health | Operativ | Iteration 49 |
| Datenbank | Verbunden | Iteration 49 |
| Workers (4) | Aktiv | Iteration 49 |
| Scheduler (7 Jobs) | Läuft | Iteration 49 |
| KI-Engine | Aktiv (GPT-5.2 Fallback) | Iteration 49 |
| Memory/Oracle | Operativ | Iteration 49 |
| Rate Limiting | Aktiv (200/min) | Iteration 49 |
| Security Headers | Vollständig | Iteration 49 |
