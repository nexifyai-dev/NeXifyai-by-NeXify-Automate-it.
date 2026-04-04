# NeXifyAI — Product Requirements Document

## Produkt
B2B-Plattform "Starter/Growth AI Agenten AG" — API-First, Unified Communication, Deep Customer Memory (mem0), KI-Orchestrator (DeepSeek).

## System-Architektur
| Schicht | Technologie | Status |
|---------|------------|--------|
| Frontend | React 18, Three.js, Framer Motion | Produktiv |
| Backend | FastAPI 3.11, 10 Route-Module | Produktiv |
| Datenbank | MongoDB (Motor async, 35+ Collections) | Produktiv |
| LLM | DeepSeek + GPT-5.2 Fallback | Produktiv |
| Object Storage | Emergent Object Storage | Produktiv |
| Payments | Stripe (Webhook Secret fehlt) | Konfiguriert |
| E-Mail | Resend | Konfiguriert |
| Background Jobs | APScheduler + Queue + DLQ | Aktiv |

## Implementierungsverlauf (2026-02-04)

### Backend
1. Modular Refactoring (6530→10 Module) ✅
2. Domain Layer (17 Modelle) ✅
3. Memory/Audit (write_classified, audit_action) ✅
4. Object Storage Migration (29 Dokumente) ✅
5. Chat-Endpoint (generate_response_fallback) ✅
6. Lead-Status Normalisierung (EN→DE, 16 Records) ✅
7. **Quote-Request API** — dreifach gesichert ✅
   - `/api/quote/request` → MongoDB (quote_requests) + Lead + Timeline + Memory
   - Idempotent: Duplikat-E-Mails aktualisieren statt duplizieren

### Frontend
8. UnifiedLogin Premium (2-Spalten, Framer-motion) ✅
9. Chat Premium (Avatare, Timestamps, Disclaimer, Mobile) ✅
10. Booking Premium (2-Step, Progress, Datums-Karten) ✅
11. Legal (Datenschutz-Fix, 4 Seiten x 3 Sprachen) ✅
12. **Pricing-Animationen** ✅
    - price-glow-ring (rotierende Conic-Gradient auf HL-Card)
    - price-badge-pulse (pulsierende Box-Shadow)
    - Hover: translateY + Border-Glow + Radial-Gradient
    - price-divider (Gradient-Trennlinie)
13. **Custom Quote Bar** ✅
    - "Individuelles Angebot" mit Icon, Beschreibung, 2 CTAs
    - "Individuell anfragen" → Chat mit Pre-Fill
    - "Beratung buchen" → Direct Booking Modal
14. **Direkter Booking-Zugang** ✅
    - Hero: 3 CTAs (Beratung + Termin + Leistungen)
    - Contact: 2 CTAs (Beratung + Termin)
    - Pricing: Custom Quote Bar (Angebot + Termin)
15. Service-/Bundle-Cards: Hover-Animationen ✅

### Daten (Audit)
| Sammlung | Anzahl | Status |
|----------|--------|--------|
| Leads | 49 | Normalisiert (nur DE-Status) |
| Buchungen | 18 | Aktiv |
| Timeline-Events | 346+ | Audit-Trail |
| Memory-Einträge | 173+ | Persistent |
| Legal-Audits | 39 | Compliance |
| Quote-Requests | 5+ | Dreifach gesichert |

### Testing (7 Iterationen)
| Iteration | Fokus | Ergebnis |
|-----------|-------|----------|
| 40 | Backend Refactoring | 100% |
| 41 | Login UI | 100% (14/14) |
| 42 | Chat-Bug | 100% |
| 43 | Chat Premium + Legal | 100% (18/18) |
| 44 | Booking + Contact | 100% (20/20) |
| 45 | System-Audit (26 APIs) | 100% |
| 46 | Lead-Status + Booking-Zugang | 100% |
| 47 | Pricing-Animation + Quote-API | 100% |

## Offene externe Abhängigkeiten
| Abhängigkeit | Risiko | Maßnahme |
|---|---|---|
| Stripe Webhook Secret | Zahlungskreislauf nicht geschlossen | Kunde muss Key bereitstellen |
| DEEPSEEK_API_KEY Produktionskey | Fallback via Emergent aktiv | Kunde muss Key bereitstellen |
| Resend Domain-Verifizierung | Spam-Risiko | DNS konfigurieren |
| Custom Domain | SEO/Branding | Deployment auf eigene Infra |

## Admin Credentials
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!
