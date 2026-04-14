# NeXifyAI Digital Operating System (DOS) v2.0

## Status
Vollständig empfangen 2026-04-14. 20 Sektionen.

## Systemmantra
Retrieval first. Marketplace first. Open Source first. Template first. CI driven. Security validated. Verify gated. Zero Information Loss. Systemische Konsistenz. Best-fit architecture over tool dogma.

Jede Entscheidung ist: kontextualisiert, validiert, architektur-konform, CI-integriert, reproduzierbar, rollback-fähig, versioniert, auditierbar, persistiert.

## 10 Guardrail-Prinzipien
1. Funnel-Zuordnung: Jede Seite, Funktion, Automation, Prozessschritt muss einer Nutzer-/Betriebslogik zugeordnet sein.
2. Claims-Policy: Kein Claim ohne Scope oder klare Kennzeichnung als Beispielwert.
3. No One-Off UI: Keine Einzelentwicklung ohne Designsystem-Logik.
4. Tracking First: Kritische Aktionen müssen messbar sein vor Go-Live.
5. Loop-Automation: KPI unter Schwelle löst Folgehandlungen, Messung, Review aus.
6. Dokumentationspflicht: Jede relevante Umsetzung, Entscheidung, Optimierung wird nachvollziehbar dokumentiert.
7. Modularität: Austauschbare Schichten bleiben austauschbar; kein unnötiger Lock-in.
8. Tenant-Sicherheit: Mandantentrennung durchgängig, nicht verhandelbar.
9. Verify Gated: Kritische Außenwirkung, finanzielle/produktive Eingriffe brauchen definierte Gates.
10. Best-Fit statt Tool-Dogma: Bessere Lösungen zulässig wenn sauber begründet und dokumentiert.

## Fehlerbehandlung-Pflichtreihenfolge
1. Stabilisieren, 2. Root Cause finden, 3. Secondary Issues und Blast Radius prüfen, 4. Vollständig beheben, 5. Erst dann optimieren/erweitern. Kein Feature-Release auf instabilem Produktivsystem.

## Memory-Architektur — Zero Information Loss
- STATE: Infrastruktur, Deployments, Konfigurationen, Betriebszustände
- KNOWLEDGE: Entscheidungen, Artefakte, Policies, Lessons Learned, freigegebene Patterns
- TODO: Aufgaben, Risiken, Folgeaktionen, Backlog, Freigaben

## Brain-Guardrails
- Policies, Projektsummary, offene Aufgaben, letzte Entscheidungen und Sperrlisten automatisch laden
- projektbezogenes Wissen von Shared Patterns trennen
- nur bereinigte und freigegebene Patterns projektübergreifend lernen
- Audit-Trail führen
- untrusted Content kennzeichnen und von Policies trennen
- Cross-Tenant-Memory verhindern

## Projektklassifikation (7 Typen)
A: SaaS/Plattform, B: B2C Shop, C: B2B Shop, D: Hybrid, E: Service/Consulting, F: Plattform/Marketplace, G: intern/Agentur/Portal/Prozessplattform

## Klassifikations-Checkliste (vor Start)
Geschäftsmodell-Typ, primäre Zielgruppen, Funnel-Logik, Conversion-Ziele, Security-Stufe, KPI-Baseline, Tech-Stack, CI-Pipeline, Review-Anforderung, Datenquellen-Matrix, Rollenmodell, Normen-/Compliance-Matrix

## Zielgruppen-System (3 Ebenen)
- Strukturell: Privatkunde, Geschäftskunde, Enterprise, Partner, Investor, intern/Support/Admin/Operations
- Psychologisch: risikoscheu, innovationsgetrieben, preisfokussiert, qualitätsfokussiert, zeitknapp, detailorientiert
- Intent-basiert: informationssuchend, vergleichend, kaufbereit, wiederkehrend, support-/serviceorientiert, intern operativ

## Pflicht je Zielgruppe
- Entry-/Landing-Logik
- Trust-/Proof-Logik
- Entscheidungslogik
- Conversion-/Folgeaktionslogik

## Pflicht-Strukturebenen (bei Gesamtprojekten)
Öffentliche Seiten, rechtliche Seiten, Kundenportal, Mitarbeiterportal, Adminportal, interne Systembereiche, Automationen/Bots/Sync-Dashboards, Dokumenten-/Kommunikationsbereiche

## Portal-Pflichtbereiche
Kundenportal: Dashboard, meine Daten, meine Assets, Termine, Dokumente, Angebote, Rechnungen, Bestellungen, Einstellungen, Quick Actions
Mitarbeiterportal: Dashboard, Aufgaben, Termine, Kunden, operative Objekte, Angebote, Dokumente, Einstellungen
Adminportal: Systemdashboard, CRM, Aufgaben, operative Objekte, Rechnungen/Angebote/Bestellungen, Dokumente, Mitarbeiterverwaltung, Inhalte/rechtliche Seiten/Konfiguration, Monitoring/Sync/Bot, Freigaben/Publishing/Nachweise

## 8-Stufen Copy-Compiler
1. Kontext, 2. Problem, 3. Konsequenz, 4. Lösung, 5. Mechanik, 6. Beweis, 7. Nutzen, 8. CTA

## Trigger-Kategorien
Verhaltens-Trigger, Intent-Trigger, Abbruch-Trigger, Timing-Trigger, KPI-Trigger, System-Trigger

## Automation-Standards
Trigger → Action → Messung → Review → Entscheidung → Dokumentation

## Security Basis-Standard
HTTPS/HSTS, CSP, RBAC, 2FA/MFA, Secret Management, Dependency Scanning, Secret Scanning, Logging, API-Härtung, Upload-Schutz

## Release-Umgebungen
Preview, Staging, Production

## Performance-Ziele
LCP < 2.5s, CLS < 0.1, TTFB < 0.8s, Lighthouse gut, Page Size kontrolliert

## Closed-Loop
1. messen, 2. diagnostizieren, 3. Hypothese formulieren, 4. Experiment durchführen, 5. auswerten, 6. ausrollen, 7. automatisieren, 8. standardisieren, 9. dokumentieren, 10. wiederholen

## Anwendung je Projekttyp
Interne Produkte: maximale Automatisierung, vollständige CI, Designsystem-First
Agenturprojekte: Standard-CI, Kunden-Freigabe-Gate, Scope-Dokumentation, Claims-Review
B2C: Conversion-Fokus, Performance-Priorität, intensives Tracking, Mobile-First, Checkout-Abbruch-Logik
B2B: Security-/Compliance-/Trust-Seiten, ROI-Dokumentation, Lead-Qualität vor -Menge, erhöhter Review-Standard
Enterprise: audit-ready Dokumentation, Security Review, SLA-/Support-Regeln, Penetrationstests
White-Label/Partner: Theme-Fähigkeit, Integrations-/API-Dokumentation, Lizenz-Compliance

## DOS-Versionshistorie
v1.0: initial, v1.1: vollständig erweitert, v2.0: optimiert, rollen-/technologieoffen, governancefest
