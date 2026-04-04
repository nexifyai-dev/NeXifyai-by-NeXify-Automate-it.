# NeXifyAI — Product Requirements Document

## Produkt
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator (DeepSeek).

## System-Architektur
| Schicht | Technologie | Status |
|---------|------------|--------|
| Frontend | React 18 SPA, Three.js, Framer Motion | Produktiv |
| Backend | FastAPI 3.11, 10 modulare Route-Dateien | Produktiv |
| Datenbank | MongoDB (Motor async, 35 Collections) | Produktiv |
| LLM | DeepSeek (Primär), GPT-5.2 Fallback (Emergent) | Produktiv |
| Object Storage | Emergent Object Storage | Produktiv |
| Payments | Stripe (emergentintegrations) | Konfiguriert, Webhook Secret fehlt |
| E-Mail | Resend | Konfiguriert, 24 gesendet |
| Background Jobs | APScheduler + Job Queue + DLQ | Aktiv |

## IST/SOLL/GAP-Analyse (2026-02-04)

### Frontend
| Bereich | IST | SOLL | GAP | Priorität |
|---------|-----|------|-----|-----------|
| Hero | 3D-Szene, 3 CTAs, Stats | Produktionsreif | Keiner | - |
| Chat | Premium-UI, Avatare, Timestamps, Mobile | Produktionsreif | Keiner | - |
| Booking | 2-Step Premium Modal, Direkt-Zugang | Produktionsreif | Keiner | - |
| Login | 2-Spalten Premium, 4 Flows | Produktionsreif | Keiner | - |
| Contact | Dual-CTA, Formular mit Validierung | Produktionsreif | Keiner | - |
| Legal | 4 Seiten x 3 Sprachen | Produktionsreif | Keiner | - |
| Admin | 16 Views, Sidebar-Nav | Funktionsfähig | Design-Refresh (Ist Legacy-CSS) | MITTEL |
| Portal | Dashboard, Projekte, Finanzen | Funktionsfähig | Nur mit Magic-Link erreichbar | MITTEL |

### Backend/APIs (26 Endpoints verifiziert)
| Bereich | IST | SOLL | GAP | Priorität |
|---------|-----|------|-----|-----------|
| Auth | Admin-Login, Magic-Link | Multi-Faktor | 2FA fehlt | NIEDRIG |
| CRM | 49 Leads, 18 Buchungen | Produktionsreif | Keiner | - |
| Billing | Stripe konfiguriert | Webhook-Loop geschlossen | Webhook Secret fehlt | HOCH (extern) |
| E-Mail | Resend aktiv, 24 gesendet | Produktionsreif | 1 Fehlsendung im Log | NIEDRIG |
| LLM | DeepSeek aktiv | Produktionsreif | Keiner | - |
| Workers | APScheduler + Queue aktiv | Produktionsreif | Keiner | - |
| Monitoring | 12 Subsysteme | Produktionsreif | Keiner | - |

### Daten
| Bereich | IST | SOLL | GAP |
|---------|-----|------|-----|
| Lead-Status | Einheitlich DE (neu/qualifiziert/termin_gebucht) | ✅ Normalisiert | Keiner |
| Timeline | 341 Events | ✅ Audit-Trail | Keiner |
| Memory | 173 Einträge | ✅ Persistent | Keiner |
| Legal Audit | 39 Einträge | ✅ Compliance-Trail | Keiner |

### Offene externe Abhängigkeiten (nicht durch Agent lösbar)
| Abhängigkeit | Benötigt von | Risiko | Maßnahme |
|---|---|---|---|
| Stripe Webhook Secret | Zahlungskreislauf | Keine Zahlungsbestätigung | Kunde muss Key bereitstellen |
| DEEPSEEK_API_KEY Produktionskey | LLM in Produktion | Aktuell via Emergent-Fallback gesichert | Kunde muss Key bereitstellen |
| Resend Domain-Verifizierung | E-Mail-Zustellung | Spam-Risiko | Kunde muss DNS konfigurieren |
| Custom Domain | SEO, Branding | Aktuell auf preview.emergentagent.com | Deployment auf eigene Infra |

## Implementierte Maßnahmen (Session 2026-02-04)
1. Backend Modular Refactoring (6530→10 Module) — verifiziert
2. Domain Layer Hardening (17 Modelle) — verifiziert
3. Memory/Audit Systematik — verifiziert
4. Legacy MongoDB→Object Storage Migration (29 Dokumente) — verifiziert
5. UnifiedLogin Premium 2-Spalten — verifiziert (Iter. 41)
6. Chat-Endpoint Reparatur (generate_response_fallback) — verifiziert (Iter. 42)
7. Chat Premium (Avatare, Timestamps, Disclaimer, Mobile) — verifiziert (Iter. 43)
8. Booking Premium Redesign (2-Step, Progress, Mobile) — verifiziert (Iter. 44)
9. Legal-Seiten Korrekturen (Datenschutz, Syntax) — verifiziert (Iter. 44)
10. Contact Form source+language Fix — verifiziert (Iter. 44)
11. System-Audit (26 APIs, 12 Subsysteme) — verifiziert (Iter. 45)
12. Lead-Status Normalisierung (EN→DE, 15 Records) — verifiziert (Iter. 46)
13. Direkter Booking-Zugang (Hero + Contact CTAs) — verifiziert (Iter. 46)

## Nächste Maßnahmen (nach Priorität)
1. **HOCH**: Master-Auftrag Restpunkte
2. **HOCH**: Stripe Webhook Secret + Live-Zahlungskreislauf
3. **MITTEL**: Admin-Panel Design-Refresh
4. **MITTEL**: Customer Portal UX-Verbesserung
5. **NIEDRIG**: Next.js Migration (eigene Infrastruktur)
6. **NIEDRIG**: PydanticAI + LiteLLM + Temporal

## Admin Credentials
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!
