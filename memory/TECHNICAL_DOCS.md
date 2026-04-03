# NeXifyAI — Technische Dokumentation

## Architekturübersicht

### Frontend (React 18 SPA)
- **Einstiegspunkt**: `index.js` → BrowserRouter mit Sprach-Routing (`/:lang`)
- **Hauptkomponente**: `App.js` — Landing Page mit allen Sektionen
- **Sprachen**: DE (Standard), NL, EN — via `i18n/LanguageContext.js`
- **Styling**: CSS Custom Properties (Dark Theme) in `App.css`
- **3D**: Three.js Scenes via `components/Scene3D.js`

### Backend (FastAPI)
- **Einstiegspunkt**: `server.py` — Alle API-Routen, LLM-Chat, Auth
- **Commercial Engine**: `commercial.py` — Quotes, Invoices, PDFs, Tarife, Revolut
- **Datenbank**: MongoDB Atlas (EU, Frankfurt) via `MONGO_URL`

### Routing
| Route | Komponente | Beschreibung |
|-------|-----------|-------------|
| `/:lang` | App.js | Landing Page (de/nl/en) |
| `/:lang/impressum` | LegalPages.js | Impressum |
| `/:lang/datenschutz` | LegalPages.js | Datenschutzerklärung |
| `/:lang/agb` | LegalPages.js | AGB |
| `/:lang/ki-hinweise` | LegalPages.js | KI-Transparenzhinweise |
| `/integrationen/:slug` | IntegrationDetail.js | SEO Landing Pages |
| `/angebot` | QuotePortal.js | Magic Link Portal |
| `/admin` | Admin.js | Admin Dashboard |

## Tarifsystem

### Single Source of Truth
Alle Tarife werden zentral in `commercial.py` verwaltet:
- `TARIFF_CONFIG` — KI-Agenten (Starter/Growth)
- `SERVICE_CATALOG` — Websites, Apps, SEO, Add-ons
- `BUNDLE_CATALOG` — Cross-Sell-Bundles
- `PRODUCT_DESCRIPTIONS` — Marketing-/Rechtstexte

### Tarifnummern-Schema
| Prefix | Kategorie | Beispiel |
|--------|-----------|---------|
| NXA-ST- | Starter AI Agent | NXA-ST-499 |
| NXA-GR- | Growth AI Agent | NXA-GR-1299 |
| NXA-WEB- | Websites | NXA-WEB-S-2990 |
| NXA-APP- | Apps | NXA-APP-M-9900 |
| NXA-SEO- | SEO | NXA-SEO-S-799 |
| NXA-AI- | Add-ons | NXA-AI-CB-249 |
| NXA-BDL- | Bundles | NXA-BDL-GD-17490 |

### Abrechnungslogik
- **KI-Agenten**: 30 % Aktivierungsanzahlung + 24 Monatsraten
- **Websites/Apps**: 50 % bei Auftrag, 50 % bei Abnahme
- **SEO**: Monatliche Abrechnung, 6 Monate Mindestlaufzeit
- **Add-ons**: Monatlich, keine Mindestlaufzeit
- **Bundles**: Individuell (Kombination der Einzellogiken)

### USt./VAT
- NL: 21 % BTW
- DE: 19 % MwSt.
- B2B: Reverse Charge bei EU-Lieferungen mit gültiger USt-ID

## Angebotsfluss (Offer-to-Cash)

```
Anfrage (Chat/Formular) → Bedarfsanalyse → Angebotserstellung (PDF)
→ Magic Link per E-Mail → Kundenportal (QuotePortal.js)
→ Angebotsannahme → Revolut Payment Order → Rechnungserstellung (PDF)
→ Zahlung → Projektstart
```

### Magic Links
- Einmal-Token (HMAC-SHA256), 24h gültig
- Kein Passwort erforderlich
- Audit-Log bei jedem Zugriff
- Automatische Ablaufzeit

## Payment (Revolut Merchant API)
- Production Keys in `.env` (niemals im Frontend)
- HMAC-SHA256 Webhook-Verifizierung
- Supported: Kreditkarte, SEPA, Klarna, giropay
- Fallback: Banküberweisung (IBAN in Rechnung)

## Sicherheit
- Security Headers: X-Frame-Options, CSP, HSTS, X-Content-Type-Options
- Argon2 Password Hashing (OWASP-empfohlen)
- JWT mit kurzer Laufzeit (24h)
- RBAC (Admin-Rollen)
- Keine Klartext-Passwörter in Logs/Responses
- MongoDB _id Exclusion in allen API-Responses

## DSGVO/Compliance
- Datenschutzerklärung: Art. 13/14 DSGVO — trilingual
- AGB: Zahlungsbedingungen, Laufzeiten, Revolut, Magic Links
- KI-Hinweise: EU AI Act 2024/1689 Transparenzpflichten
- Auftragsverarbeiter: Resend (E-Mail), OpenAI (Chat), MongoDB Atlas (DB), Revolut (Payment)
- Aufbewahrungsfristen: 24 Monate (Anfragen), 10 Jahre (Rechnungen), 90 Tage (Chat)

## SEO-Strategie
- Dedizierte Landing Pages pro Integration (/integrationen/:slug)
- Strukturierte Daten via react-helmet-async
- Interne Verlinkung: Integrations → Services → Pricing → Contact
- Multilingual mit hreflang-Tags (DE/NL/EN)

## Abhängigkeiten
### Backend
- fastapi, uvicorn, motor (MongoDB async), PyJWT
- reportlab (PDF-Generierung), httpx (HTTP-Client)
- resend (E-Mail), emergentintegrations (LLM)
- argon2-cffi (Password Hashing)

### Frontend
- react 18, react-router-dom 6, framer-motion
- @react-three/fiber, @react-three/drei (3D)
- react-helmet-async (SEO)

## Synchronisationsregeln (Frontend ↔ Backend)
- **Single Source of Truth**: `commercial.py` ist die autoritäre Quelle für alle Tarife und Preise
- **Frontend-Datenhaltung**: `products.js` und `integrations.js` müssen identische Preise/Features wie `SERVICE_CATALOG` enthalten
- **Bei Preisänderungen**: Zuerst `commercial.py`, dann `products.js`, dann PDF-Output prüfen
- **Validierung**: Sync-Check-Script verfügbar (python3 — vergleicht alle 15 Produkte)

## Produktportfolio (12 Produkte, 3 Bundles)

| Produkt | Tarif-Nr. | Preis (netto) | Billing | Beschreibung |
|---------|-----------|---------------|---------|-------------|
| Starter AI Agenten AG | NXA-ST-499 | 499 EUR/Mo. | 30 % + 24 Mo. | 2 Agenten, Shared Cloud |
| Growth AI Agenten AG | NXA-GR-1299 | 1.299 EUR/Mo. | 30 % + 24 Mo. | 10 Agenten, Private Cloud |
| Website Starter | NXA-WEB-S-2990 | 2.990 EUR | Projekt (50/50) | 5 Seiten, CMS |
| Website Professional | NXA-WEB-P-7490 | 7.490 EUR | Projekt (50/50) | 15 Seiten, Animations |
| Website Enterprise | NXA-WEB-E-14900 | 14.900 EUR | Projekt (50/50) | Headless CMS, E-Commerce |
| App MVP | NXA-APP-M-9900 | 9.900 EUR | Projekt (50/50) | iOS + Android, 5 Features |
| App Professional | NXA-APP-P-24900 | 24.900 EUR | Projekt (50/50) | Full-Stack, Admin, CRM |
| SEO Starter | NXA-SEO-S-799 | 799 EUR/Mo. | Monatlich (min. 6) | 50 Keywords |
| SEO Growth | NXA-SEO-G-1499 | 1.499 EUR/Mo. | Monatlich (min. 6) | 200 Keywords, Multilingual |
| SEO Enterprise | NXA-SEO-E-IND | Individuell | Monatlich (min. 12) | Dediziertes Team |
| KI-Chatbot | NXA-AI-CB-249 | 249 EUR/Mo. | Monatlich | Lead-Qualifizierung |
| KI-Automation | NXA-AI-AUTO-499 | 499 EUR/Mo. | Monatlich | Workflow-Automation |

### Bundles
| Bundle | Tarif-Nr. | Preis (netto) | Inhalt |
|--------|-----------|---------------|--------|
| Digital Starter | NXA-BDL-DS-3990 | 3.990 EUR | Website Starter + SEO Starter (3 Mo.) |
| Growth Digital | NXA-BDL-GD-17490 | 17.490 EUR | Website Pro + SEO Growth (6 Mo.) + Chatbot |
| Enterprise Digital | NXA-BDL-ED-39900 | ab 39.900 EUR | Website Enterprise + App + SEO Enterprise + Growth Agent |

## Offene Risiken
1. Resend API Key ist Platzhalter — E-Mail-Versand nicht produktiv
2. App.js >1000 Zeilen — Refactoring geplant (Phase 4)
3. Keine automatisierten E2E-Tests im CI/CD
4. Revolut Webhook-Endpoint nicht öffentlich erreichbar in Preview
