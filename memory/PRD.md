# NeXifyAI — Product Requirements Document

## Product Vision
NeXifyAI by NeXify Automate: B2B-first KI-Agenten-Platform fuer DACH/Benelux.
Landing Page + CRM + Commercial Engine + AI Chat Discovery + Service-Katalog + Trust/Compliance.

## Core Architecture
```
/app/
├── backend/
│   ├── server.py (FastAPI, MongoDB, JWT, LLM Chat, Admin, Commercial, Security Headers)
│   ├── commercial.py (TARIFF_CONFIG, SERVICE_CATALOG, BUNDLE_CATALOG, COMPLIANCE_STATUS, ISO_GAP_ANALYSIS, PDF, Revolut, Magic Links, FAQ)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.js (Landing, 3D, Chat Discovery, Pricing, Services, Trust, FAQ, Contact)
│   │   ├── App.css
│   │   ├── index.js (Routes: /, /de, /nl, /en, /admin, /angebot, /datenschutz, /impressum, /agb)
│   │   ├── i18n/ (LanguageContext.js, translations.js — DE/NL/EN)
│   │   └── pages/ (Admin.js, LegalPages.js, QuotePortal.js)
│   └── package.json
└── memory/ (PRD.md, test_credentials.md)
```

---

## TARIFF MODEL (Single Source of Truth — commercial.py)

### Starter AI Agenten AG (NXA-SAA-24-499)
- 499 EUR/Mo (netto), 24 Monate, 30% Aktivierungsanzahlung
- Gesamt: 11.976 EUR | Anzahlung: 3.592,80 EUR | Rate: 349,30 EUR (24x)
- 2 KI-Agenten, Shared Cloud, E-Mail-Support (48h)

### Growth AI Agenten AG (NXA-GAA-24-1299)
- 1.299 EUR/Mo (netto), 24 Monate, 30% Aktivierungsanzahlung
- Gesamt: 31.176 EUR | Anzahlung: 9.352,80 EUR | Rate: 909,30 EUR (24x)
- 10 KI-Agenten, Private Cloud, Priority Support (24h), CRM/ERP-Kit

---

## SERVICE CATALOG

### Websites
- Starter: 2.990 EUR | Professional: 7.490 EUR | Enterprise: 14.900 EUR

### Apps
- MVP: 9.900 EUR | Professional: 24.900 EUR

### KI Add-ons
- Chatbot: 249 EUR/Mo | Automation: 499 EUR/Mo

### Bundles
- Digital Starter: 3.990 EUR | Growth Digital: 17.490 EUR | Enterprise Digital: 39.900 EUR

---

## COMPLIANCE & TRUST
- DSGVO (EU) 2016/679 — implementiert
- EU AI Act (EU) 2024/1689 — implementiert
- ISO/IEC 27001 — orientiert (nicht zertifiziert)
- ISO/IEC 27701 — orientiert (nicht zertifiziert)
- EU-Hosting (Frankfurt, Amsterdam)
- Security Headers (X-Frame, CSP, HSTS, Referrer-Policy)
- Argon2 Passwort-Hashing, JWT, Rate Limiting
- Audit-Logs fuer alle kommerziellen Events
- EU-Emblem korrekt eingebunden (keine falsche Zertifizierung)

---

## COMPANY DATA
- NeXify Automate | KvK: 90483944 | USt-ID: NL865786276B01
- IBAN: NL66 REVO 3601 4304 36 | BIC: REVONL22 | Intermediary: CHASDEFX

---

## Implemented Features (all tested, all passing)

### Phase 1: Landing Page & Brand — DONE
### Phase 2: AI Chat & Lead System — DONE
### Phase 3: Admin CRM — DONE
### Phase 4: Commercial Engine v2.0 — DONE
### Phase 5: Service Catalog, Trust, Compliance, Security Hardening — DONE

**Test Results:**
- Iteration 13: 23/23 passed
- Iteration 14: 20/20 passed
- Iteration 15: 22/22 passed + all frontend verified

---

## Pending / Backlog

### P1
- Live Resend Key aktivieren fuer produktiven E-Mail-Versand
- SMTP-Fallback (Hostinger: nexifyai@nexifyai.de)
- Revolut Production Keys einsetzen

### P2
- DeepSeek/Mem0 Integration fuer persistente Chat-Memory
- Monatliche Folgerechnungen Auto-Generierung (Scheduler/Cron)
- Revolut Subscription API fuer wiederkehrende Zahlungen
- Dunning-Logik (Zahlungserinnerungen nach 7/14 Tagen)
- Admin CSV Export
- App.js Refactoring (>840 Zeilen)
