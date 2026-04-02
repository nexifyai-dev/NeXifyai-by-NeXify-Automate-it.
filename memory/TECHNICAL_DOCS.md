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

## Offene Risiken
1. Resend API Key ist Platzhalter — E-Mail-Versand nicht produktiv
2. App.js >1000 Zeilen — sollte in Komponenten aufgeteilt werden
3. Keine automatisierten E2E-Tests im CI/CD
4. Revolut Webhook-Endpoint nicht öffentlich erreichbar in Preview
