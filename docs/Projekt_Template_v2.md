# NeXifyAI Projekt-Template v2.0

## Status
Vollständig empfangen 2026-04-14. 28 Sektionen.

## Leitprinzipien
- Wahrheitspflicht: Keine Behauptung ohne Prüfung, keine Mock-Aussage als Fakt, keine Freigabe ohne echte Verifikation
- Qualitätsprinzip: Genauigkeit vor Geschwindigkeit, Produktionsreife vor Schönrederei
- Systemprinzip: Eine Source of Truth pro Bereich, keine Parallelstrukturen, klare Rollen
- UX-Prinzip: Klarheit statt Reibung, keine Sackgassen, mobil zuerst
- Architekturprinzip: Default-Standards zuerst, OSS/Marketplace/Template zuerst, Tool-Dogma verboten

## Pflicht-Stammdaten je Projekt
- Projektname, Kurzbeschreibung, verantwortliche Marke, Teilmarken
- Zielmärkte, Sprachen, Geschäftsmodell
- B2C/B2B/Hybrid/intern/Enterprise/White-Label
- Projektart: Website, Portal, Shop, CRM, interne App, Automation, Content-System, Plattform, Hybrid
- primäre/nicht relevante/nicht relevante Geschäftsziele, Nutzerziele, Betriebsziele, Qualitätsziele, rechtliche Mindestziele, technische Mindestziele, Messziele/KPIs, Freigabeziele

## Marken- und Kommunikationsrahmen
- Markenarchitektur, Hauptmarke, Submarken, Dachmarkenlogik
- Markenwerte: Verlässlichkeit, Verantwortung, Transparenz, Kompetenz, Nahbarkeit, Modernität ohne Kitsch
- Tonalität: professionell, klar, ehrlich, D/A/CH-konform, keine KI-Floskeln, problem-/lösungsorientiert
- Messaging: Kernversprechen, Nutzenbotschaften, Vertrauensargumente, Differenzierungsmerkmale, Proof-Elemente, Claim-Scope, CTA-Strategie

## Normen-Compliance-Matrix (pro Projekt)
- Norm/Regelwerk, Relevanz, Muss/Soll/Nicht relevant, Umsetzungsobjekte, Prüfobjekte, Nachweise, Owner, Status

## Rechtliche Pflichtbereiche
Impressum, Datenschutz, AGB, Cookies/Consent, Nutzungsbedingungen, KI-Hinweise, Newsletter-/Formular-/Mail-/Tracking-Hinweise, B2B/B2C Unterschiede, Österreich/Deutschland/Schweiz Unterschiede

## Discovery-Pflichtanalyse
Geschäftsmodell, Prozesse, Datenquellen, Rollenmodell, Systemgrenzen, Risiken, Rechtstexte, technische Randbedingungen, vorhandene Systeme/APIs/Storage/Integrationen, Bestandsarchitektur, Tenant-/Mandantenlogik, Freigabe-/Auditlogik

## Problemklassen
Prozessbrüche, Datenbrüche, Rollenbrüche, Medienbrüche, Content-Lücken, rechtliche Lücken, UX-Lücken, Prüf-/Nachweislücken, Integrationslücken, Betriebslücken

## Discovery-Ergebnisdokumente
Scope-Dokument, Prozesslandkarte, Rollenmatrix, Systemarchitektur-Skizze, Datenquellen-Matrix, Risiko-Register, Release-Zielbild, Normen-/Compliance-Matrix, ADR-Vorlage

## Informationsarchitektur Pflichtprüfung je Bereich
Zweck, Zielgruppe, primäre/sekundäre Aktionen, Datenquellen, Rollen/Rechte, Abhängigkeiten, Leere Zustände, Fehlerzustände, mobile Nutzbarkeit, Nachweispflicht, Auditspur

## Designsystem-Pflichtbestandteile
Farb-Tokens, Typografie-Tokens, Spacing, Radius, Motion, Statusfarben, themingfähige Struktur, Dark-Mode wenn relevant
Pflicht-Komponenten: Header, Topbar, Footer, Buttons, Cards, Grids, Tables, Lists, Search, Autocomplete, Filter, Forms, Modals, Tabs, Stepper, KPI-Kards, Status-Badges, Empty States, Error States, Upload, PDF-Viewer, Chat, Kalender, Freigabe-Status

## Textarten
Navigationstexte, Headlines, Hero-Texte, Vertrauens-/Proof-Texte, Leistungsbeschreibungen, Produkttexte, FAQ, Systemtexte, Fehlermeldungen, Leere-Zustände, Mailtexte, PDF-Texte, Portal-/Dashboard-Texte, Freigabe-/Statuskommunikation

## Datenmodell-Pflichtobjekte je Projekt
Nutzer/Profile, Rollen/Rechte, Kunden, Kontakte, Fahrzeuge/Produkte/Dokumente/Inhalte/Assets, Aufgaben, Termine, Angebote, Rechnungen, Bestellungen, Dokumente/Uploads, Sync-Läufe/Issues/Logs, Kommunikationsereignisse, Freigaben, Automationsläufe, Monitoring-/Systemereignisse

## Rollenmodell Standard
Gast, Kunde, Mitarbeiter, Admin, optional: Manager/Support/Vertrieb/Redaktion/B2B/Technik/Partner

## CRM-/Workflow-Standardverknüpfungen
Kunde → Objekt/Asset/Fahrzeug/Produktbezug, Kunde → Aufgabe, Kunde → Termin, Kunde → Angebot, Kunde → Rechnung, Objekt → Aufgabe, Objekt → Termin, Angebot → PDF/Versand/Rechnung, Rechnung → PDF/Versand/Zahlung/Status, Dokument → Kunde/Objekt/Vorgang, Freigabe → Dokument/Versand/Veröffentlichung/Deploy

## Shop-/Katalog-Bot-Pflichtfunktionen
Discovery, Pagination, Produktdetailerfassung, Change Detection, Queue/Jobs, Retry/Backoff, Heartbeat, Health Checks, Coverage-Dashboard, Fehlerprotokollierung, Alerting, Freigabe-/Reviewlogik

## PDF-Logik
Angebots-PDF, Rechnungs-PDF, CI-konform, D/A/CH-formatiert, druckbar, downloadbar, statuslogisch korrekt, reproduzierbar

## E-Mail-Logik
Transaktional, Auth, Termine, Angebote/Rechnungen/Bestellungen, CI-konformes Layout, Rechtsangaben, Versandstatus/Trigger-Nachweis, Freigabegate wenn erforderlich

## Chatbot-Pflichtkriterien
Echte Hilfe, gute Gesprächsführung, saubere Formatierung, responsive UI, sinnvoller Einstieg, Kontextbezug je Seite, Nutzerführung, Lead-/Service-/Support-Nutzen, Eskalationslogik

## Accessibility-Pflicht
Fokusführung, Tastaturbedienung, Kontrast, Labels, Screenreader-freundliche Struktur, verständliche Fehlermeldungen, große Touch-Ziele, semantische Buttons/Links, WCAG 2.1 AA minimum, WCAG 2.2 AA bevorzugt

## D/A/CH-Pflichtstandard
Deutsches Datumsformat, deutsches Preisformat, Euro mit Komma, deutschsprachige Validierungen, keine US-Placeholders, keine Mischlokalisierung

## Security-Pflicht
Rollenprüfung serverseitig, Secrets sauer, Logging/Monitoring, Upload-Schutz, API-Härtung, Session-/Auth-Flows stabil, Webhooks signaturgeprüft/idempotent/replay-sicher, service_role nie im Browser

## QA-Prüfkategorien
Fachlich, visuell, funktional, responsiv, rollenbezogen, datenbezogen, rechtlich, lokalisierungsbezogen, accessibility-bezogen, sicherheitsbezogen, betriebsbezogen

## Breakpoints
1920, 1440, 1280, 1024, 820, 768, 480, 430, 390, 375, 360

## Release-Gates
Gate A: Scope/Rollen/Datenquellen klar
Gate B: Kernflows implementiert
Gate C: Volltest/Rechtslage/D/A/CH/Accessibility/Sicherheitsprüfung
Gate D: Release Candidate
Gate E: Produktivfreigabe

## Implementierungs-Phasenreihenfolge
Phase 1: Grundlagen (Scope, Discovery, Markenlogik, Rollenmodell, Datenquellen, Rechts-/Normenprofil)
Phase 2: Architektur/Designsystem (Informationsarchitektur, Komponentenbibliothek, Datenmodell, API-Struktur, Portalstruktur, Stack-Entscheidungen)
Phase 3: Kernflows (Öffentliche Seiten, Portale, Kernprozesse, Dokumente/PDFs/E-Mails, Bot/Sync/Monitoring, Tracking/Events/Automationen)
Phase 4: Härtung (RBAC, RLS, Validierungen, Fehlerzustände, Upload-/Download-Tests, Performance/Stabilität, Security-/Monitoring-Setup)
Phase 5: Release Candidate (vollständige Deep-QA, Rechts-/Compliance-Abgleich, Accessibility-Check, Datenintegritätsprüfung, Nachweis-/Auditspur, Freigabegates)

## Verbindlicher Qualitätsmaßstab
Projekt gilt als reif wenn: Kernflows vollständig funktional, Datenquellen klar/konsistent, Rollenmodell sauber durchgesetzt, keine Mockdaten im Produktivpfad, PDFs/Dokumente/E-Mails/Uploads/zentrale Betriebsfunktionen real nutzbar, UX klar/arbeitsfähig, D/A/CH-Lokalisierung sauber, Rechtsseiten realen Systemzustand abbilden, QA/Nachweise vollständig, Freigaben nachvollziehbar, Rollback/Monitoring bedacht
