# NeXifyAI — Änderungsverlauf (Changelog)

## 2026-04-02 — Phase 2: Commercial System Overhaul

### BLOCK 0 — UI Self-Healing
- Navigation Breakpoint von 1024px auf 1200px erhöht → kein Overlap bei mittleren Viewports
- Mobile 400+-Counter ausgeblendet (Redundanz mit Sektions-Titel)
- Alle deutschen Umlaute in Data-Dateien korrigiert (integrations.js, products.js, App.js, IntegrationDetail.js, commercial.py)
- Responsive Spacing optimiert für Integration-Header

### BLOCK 1 — Integrations UI Overhaul
- Tag-Cloud ersetzt durch kategorisiertes Premium-Layout
- 12 Kategorien mit Icons, Beschreibungen, Item-Counts
- 9 Featured Integrations als klickbare Karten
- Interne Verlinkung zu SEO-Detailseiten

### BLOCK 2 — SEO Landing Pages
- Route /integrationen/:slug für alle Featured Integrations
- Seiten für: Salesforce, HubSpot, SAP, DATEV, Slack, AWS, Shopify, OpenAI, Stripe
- Jede Seite: Breadcrumb, Use Cases, Process, FAQ, Combined-With, CTA
- SEO Meta-Tags, Canonical URLs

### BLOCK 3 — KI-gesteuertes SEO Produkt
- Vollständige Produktsektion mit Benefits (6), Process (4 Schritte), 3 Tarifen, FAQ (5)
- Tarife: SEO Starter (799 EUR/Mo.), SEO Growth (1.499 EUR/Mo.), SEO Enterprise (individuell)

### BLOCK 4 — Services & Bundles
- ServicesAll-Komponente mit 5 Kategorien (Websites, Apps, SEO, KI-Agenten, Add-ons)
- 3 Bundle-Cards (Digital Starter, Growth Digital, Enterprise Digital)
- PDF-Download-Button für Tarifübersicht

### BLOCK 5 — PDF Tarif-Vergleichsblätter
- Backend-Funktion generate_tariff_sheet_pdf() in commercial.py
- Kategorien: all, agents, websites, seo, apps, addons, bundles
- CI-branded Layout mit NeXifyAI Header, Fußnoten, Seitenzahlen
- API-Endpoint: GET /api/product/tariff-sheet?category=all

### BLOCK 6 — Legal Updates
- NL/EN Datenschutz: Revolut, Magic Links, Quotes/Invoices-Abschnitte ergänzt
- NL/EN AGB: Zahlungsbedingungen, 30 % Aktivierungsanzahlung, Revolut, IBAN
- Alle 3 Sprachen konsistent

### BLOCK 7 — Trust Section
- 4 operationale Sicherheitskarten: Magic Links, Audit Trail, Daten-Lebenszyklus, RBAC

### BLOCK 8 — KI-Advisor Update
- System-Prompt erweitert: SEO-Tarife, Bundle-Logik, Cross-Sell-Triggers
- Produktempfehlungslogik: SEO → Growth empfehlen, Website+SEO → Bundle vorschlagen

### BLOCK 9 — Zentrales Tarifsystem
- SERVICE_CATALOG um SEO-Tarife (3) erweitert
- BUNDLE_CATALOG an Frontend angeglichen (Digital Starter, Growth Digital, Enterprise Digital)
- PRODUCT_DESCRIPTIONS hinzugefügt (6 detaillierte Produktbeschreibungen)
- API: GET /api/product/descriptions
- PDF-Tarif-Sheets erweitert um Apps, Add-ons, vollständige Bundles

### BLOCK 10 — Dokumentation
- TECHNICAL_DOCS.md: Architektur, Tarifsystem, Sicherheit, Compliance
- CHANGELOG.md: Vollständiger Änderungsverlauf
- PRD.md: Aktualisierte Produktanforderungen

## 2026-04-01 — Phase 1: Core Commercial Engine (Previous forks)
- FastAPI Backend, MongoDB, JWT Auth, Security Headers
- Commercial Engine: Quotes, Invoices, Revolut Integration
- Magic Link / Quote Portal
- Chat Discovery Flow mit LLM
- Admin Dashboard
- 3D Landing Page, Multi-Language (DE/NL/EN)
- EU Compliance Trust UI
- 65 automatisierte Tests bestanden
