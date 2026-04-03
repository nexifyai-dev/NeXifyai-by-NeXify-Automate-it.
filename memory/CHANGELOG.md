# NeXifyAI — Änderungsverlauf (Changelog)

## 2026-04-03 — Phase 3: Self-Healing, Systemhärtung & Vollständige Dokumentation

### BLOCK 1 — Self-Healing: Umlaut-/Encoding-Korrektur (abgeschlossen)
- 76 ASCII-Umlaut-Korrekturen in 7 Dateien (QuotePortal.js, commercial.py, server.py, App.js, products.js, integrations.js, translations.js)
- Codeweit verifiziert: kein einziger ASCII-Umlaut verbleibt
- Alle PDFs, Portaltexte, Angebots- und Rechnungstexte geprüft
- Sprachvarianten DE/NL/EN clean

### BLOCK 2 — Header/Navigation auf allen Breakpoints final gehärtet
- Desktop (1920px): Alle Nav-Links + CTA sauber sichtbar
- Tablet (1100px): Burger-Menü aktiviert, kein Überlappen
- Mobile (375px): Kompaktes Layout, keine Kollisionen
- Sprachumschalter (DE/NL/EN) in allen Breakpoints getestet

### BLOCK 3 — Frontend/Backend-Daten-Sync vollständig verifiziert
- Alle 15 Produkte/Services synchron: Preise, Features, Laufzeiten, Tarif-Nummern
- Mathematische Korrektheit: Aktivierungsanzahlungen, Monatsraten, Gesamtvertragswerte
- Kein Widerspruch zwischen Website, API, PDF, Portal

### BLOCK 4 — Tarifsystem für alle Services erweitert
- PRODUCT_DESCRIPTIONS erweitert um 6 neue Produkte: web_enterprise, app_mvp, app_professional, seo_enterprise, ai_addon_chatbot, ai_addon_automation
- Insgesamt 12 Produkte mit vollständiger Beschreibung (what, for_whom, results, included, not_included, process, contract_terms)
- FAQ ergänzt um SEO-Tarife und korrigierte Bundle-Beschreibungen (18 FAQ-Einträge)

### BLOCK 5 — Rechtliche und kommerzielle Logik verifiziert
- Starter AI Agenten AG: 499 EUR/Mo., 24 Mo., 30 % Anzahlung (3.592,80 EUR), 2 Agenten, Shared Cloud
- Growth AI Agenten AG: 1.299 EUR/Mo., 24 Mo., 30 % Anzahlung (9.352,80 EUR), 10 Agenten, Private Cloud
- Websites: Starter 2.990, Professional 7.490, Enterprise 14.900 (je 50/50 Zahlungsbedingungen)
- Apps: MVP 9.900, Professional 24.900 (je 50/50)
- SEO: Starter 799/Mo., Growth 1.499/Mo., Enterprise individuell (je 6 Monate Mindestlaufzeit)
- Bundles: Digital Starter 3.990, Growth Digital 17.490, Enterprise Digital ab 39.900

### BLOCK 6 — PDF-Tarifblätter final verifiziert
- 4-seitiges PDF: KI-Agenten, Websites, SEO, Apps, Add-ons, Bundles
- Keine ASCII-Umlaute, korrekte Firmendaten (KvK, USt-ID, IBAN)
- CI-konformes Layout mit NeXifyAI Branding

### BLOCK 7 — App-weite Absicherung
- Alle API-Endpunkte getestet und funktional (health, tariffs, faq, compliance, descriptions, tariff-sheet, booking/slots)
- Integration-Detail-Seiten (Salesforce etc.) visuell geprüft
- Rechtsseiten (Impressum, Datenschutz, AGB) korrekt

### BLOCK 8 — Dokumentation
- CHANGELOG.md aktualisiert mit Phase 3
- TECHNICAL_DOCS.md mit aktualisierter Produktarchitektur
- PRD.md mit vollständigem Taskstatus

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
