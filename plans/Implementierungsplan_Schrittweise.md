# NeXifyAI — Schrittweise Implementierung
## Phasen-Plan: Incrementell, aufeinander aufbauend

**Erstellt:** 2026-04-14
**Prinzip:** Ein Schritt nach dem anderen. Jeder Schritt ist ein vollständiges, funktionierendes System. Nächster Schritt baut auf vorherigem auf.

---

## GRUNDLAGE

### Bestehende Assets
- Oracle Engine (funktioniert, aber buggy)
- 10 Agents im Backend
- LibreChat (läuft auf ai.unternehmensbot.eu)
- Paperclip (Control Plane)
- mem0 OSS (Brain)
- Supabase `xhmltysfaqzwtpaiesjf` (eigene DB)
- GitHub Repo (nexifyai-dev/NeXifyai-by-NeXify-Automate-it)
- MiniMax M2.7 (OpenRouter)

### Aktuelles Projekt
- Studienkolleg Aachen: studienkolleg.nexifyai.de
- Eigene Seite mit Bestell-/Bezahlsystem
- Workflow: Auftragserfüllung → Rechnungsstellung → Statusmails

---

## ═══════════════════════════════════════════════════════════════
## PHASE 0: FUNDAMENT (Stabilisiert bestehendes System)
## ═══════════════════════════════════════════════════════════════

### Ziel
Bestehendes System stabilisieren, Fehler beheben, Grundlagen schaffen.

### Aufgaben

#### 0.1 mem0 OSS fixen (HEUTE)
```
Problem: mem0_search gibt leere memory-Felder zurück
Lösung: Plugin-Patch bereits gemacht, aber NICHT verifiziert
Aktion: Test ob mem0_search jetzt korrekte Results liefert
```

#### 0.2 GitHub Repo sync
```
Aktion: Lokale Docs mit Repo synchronisieren
Docs die reingehören:
- /opt/data/nexifyai/docs/ → repo docs/
- /opt/data/nexifyai/plans/ → repo plans/
- /opt/data/nexifyai/plans/Luecken_Analyse.md
```

#### 0.3 Keys updaten
```
Bestehende Secrets in Repo NICHT committen
Keys in /opt/data/keys/nexifyai/secrets.env (bereits done)
```

#### 0.4 Supabase Schema designen (nur Design, noch nicht migrieren)
```
Was brauchen wir?
- tenants (Mandanten)
- users (Mitarbeiter)
- customers (Kunden)
- projects (Projekte)
- tasks (Oracle-Aufträge)
- agents (Agent-Definitionen)
- logs (Audit-Trail)
- ...
```

### Deliverable
✅ System läuft stabil, Docs im Repo, Schema designed

---

## ═══════════════════════════════════════════════════════════════
## PHASE 1: MANDANTENTRENNUNG (Security-Basis)
## ═══════════════════════════════════════════════════════════════

### Ziel
Jeder Kunde/Tenant sieht nur seine eigenen Daten. Security-Basis.

### Aufgaben

#### 1.1 Tenant-Modell definieren
```
NeXifyAI (intern)
├── Studienkolleg Aachen (Tenant 1)
├── [Zukünftige Kunden] (Tenant N)
└── ...
```

#### 1.2 Tenant-IDs in mem0
```
Ab jetzt: JEDER mem0-Eintrag bekommt tenant_id
Suchen/Schreiben: Immer mit tenant_id filtern
Kein Cross-Tenant-Zugriff möglich
```

#### 1.3 Tenant-IDs in Oracle-Tasks
```
Jeder Task hat: tenant_id
Oracle-Core filtert immer nach current_tenant
Specialist-Agents bekommen nur Tasks ihrer tenant_id
```

#### 1.4 Tenant-IDs in Paperclip
```
Company = Tenant
Task-Filter: immer WHERE tenant_id = current_tenant
```

### Deliverable
✅ Mandantentrennung implementiert. Security-Risiko behoben.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 2: INTAKE-AGENT (Lead-Aufnahme)
## ═══════════════════════════════════════════════════════════════

### Ziel
Leads werden sauber aufgenommen, klassifiziert und weitergeleitet.

### Aufgaben

#### 2.1 intake-agent Prompt definieren
```
Eingang: Chat-Nachricht, E-Mail, Formular, Inbound
Output: Klassifizierter Lead mit:
- Quelle (Chat/Email/Web/...)
- Intent (Anfrage/Support/Kauf/...)
- Priorität (hot/warm/cold)
- Nächste Aktion (research/outreach/pm/...)
```

#### 2.2 intake-agent in Oracle integrieren
```
Chat-Nachricht erkannt
→ Oracle leitet an intake-agent
→ intake-agent klassifiziert
→ Task erstellt in Paperclip
→ Zugehöriger Specialist-Agent startet
```

#### 2.3 Lead-Qualifizierung
```
BASH-Methode:
- Budget vorhanden?
- Timeline bekannt?
- Entscheidungsbefugnis?
- Bedarf klar?
```

#### 2.4 First-Response generieren
```
intake-agent erstellt automatisch:
- Empfangsbestätigung
- Erwartete Timeline
- Nächste Schritte
```

### Deliverable
✅ Jeder Lead wird professionell aufgenommen und weitergeleitet.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 3: RESEARCH + OUTREACH AGENTS
## ═══════════════════════════════════════════════════════════════

### Ziel
DACH-Leads finden und professionell ansprechen.

### Aufgaben

#### 3.1 research-agent
```
Sucht: Websites, Kontakte, Technologie-Stack
Output: Lead-Liste mit Qualifizierungs-Details
Filter: DACH, relevant, nicht bereits Kunde
```

#### 3.2 outreach-agent
```
Erstellt: Personalisierte Erstansprache
Channels: E-Mail (primär)
Feedback-Loop: Keine Antwort → Nachfass (max 3x)
Freigabe: Erstversand NUR nach Pascal-Approval
```

#### 3.3 Outreach-Pipeline
```
research → outreach_entwurf → verify → freigabe → versand
                                      ↓
                              kein Erfolg → research (weiter)
```

### Deliverable
✅ Outbound-Maschine läuft. Leads werden gefunden und angesprochen.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 4: E-MAIL INTEGRATION (Ein- + Ausgang)
## ═══════════════════════════════════════════════════════════════

### Ziel
E-Mails empfangen UND senden. Komplette Kommunikation über Oracle.

### Aufgaben

#### 4.1 E-Mail-Empfang (IMAP)
```
Polling: Alle 5 Min neue E-Mails abrufen
Klassifizieren: Support/Angebot/Reply/Kündigung/...
Weiterleiten: An intake-agent oder relevanten Specialist
```

#### 4.2 E-Mail-Sende-Integration
```
Bestehend: Resend API (nexifyai@nexifyai.de)
Neu: Jeder Agent kann E-Mails versenden (nach Freigabe-Gate)
Template: CI-konformes E-Mail-Design
```

#### 4.3 E-Mail-Thread-Tracking
```
Kunde schreibt → Thread erkannt → Kontext laden → Antwort
Alle E-Mails werden geloggt (Audit-Trail)
```

### Deliverable
✅ E-Mails rein und raus funktionieren. Kein Communication-Bruch.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 5: SUPPORT + TICKET-SYSTEM
## ═══════════════════════════════════════════════════════════════

### Ziel
Support-Anfragen werden professionell bearbeitet.

### Aufgaben

#### 5.1 support-agent
```
Eingang: E-Mail, Chat, Ticket
Klassifizieren: Technisch/Billing/Allgemein
Priorisieren: Kritisch/Hoch/Normal/Niedrig
Eskalation: Bei SLA-Bruch → Pascal
```

#### 5.2 Ticket-Lifecycle
```
OFFEN → IN_BEARBEITUNG → WARTEND → GELÖST → ARCHIVIERT
         ↓ (bei Eskalation)
      ESKALIERT → Pascal greift ein
```

#### 5.3 Knowledge Base Integration
```
Support-Agent sucht erst in Knowledge Base
Wenn Lösung gefunden → direkt antworten
Wenn nicht → an Pascal eskalieren
```

### Deliverable
✅ Support läuft. Tickets werden getrackt, SLA eingehalten.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 6: PM + OFFER + FINANCE PIPELINE
## ═══════════════════════════════════════════════════════════════

### Ziel
Komplette Angebots- und Rechnungs-Pipeline.

### Aufgaben

#### 6.1 pm-agent
```
Projektsteckbrief erstellen
Aufwandsschätzung (Stunden, Preis)
Angebotsentwurf generieren
Timeline/Meilensteine planen
```

#### 6.2 Angebots-Pipeline
```
Lead qualifiziert → pm-agent erstellt Entwurf
→ verify-agent prüft
→ Pascal freigibt
→ doc-agent erstellt PDF
→ outreach-agent versendet
```

#### 6.3 Rechnungs-Pipeline
```
Meilenstein erreicht / Projekt abgeschlossen
→ finance-agent erstellt Rechnung (PDF)
→ verify-agent prüft (rechtlich, D/A/CH)
→ Pascal freigibt
→ doc-agent versendet
→ Zahlungsstatus wird getrackt
```

#### 6.4 Vertragsmanagement
```
Angebot angenommen → Vertrag erstellt
→ beide Parteien signieren (digital)
→ Vertrag wird archiviert
→ Folgetasks werden erstellt
```

### Deliverable
✅ Angebote und Rechnungen werden professionell erstellt und versendet.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 7: KALENDER + TERMINE
## ═══════════════════════════════════════════════════════════════

### Ziel
Termine werden gemanagt. Erinnerungen automatisch.

### Aufgaben

#### 7.1 Kalender-Integration
```
Welcher Kalender? → Google Calendar API oder Cal.com?
Termine: Meetings, Deadlines, Meilensteine
Erinnerungen: Automatisch X Stunden vorher
```

#### 7.2 Terminbuchungs-Flow
```
Kunde möchte Termin → intake-agent
→ Verfügbarkeit prüfen
→ Terminvorschlag senden
→ Kunde bucht
→ Kalender wird gefüllt
→ Erinnerungen werden gesetzt
```

#### 7.3 Meeting-Vorbereitung
```
Termin steht an → pm-agent bereitet vor
→ Agenda
→ Kontext aus Brain laden
→ Notizen-Template bereit
```

### Deliverable
✅ Kalender funktioniert. Keine verpassten Termine.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 8: LIBRECHAT INTEGRATION (Arbeitsplatz)
## ═══════════════════════════════════════════════════════════════

### Ziel
LibreChat = mein zentraler Arbeitsplatz. Chat + Dashboard + Paperclip.

### Aufgaben

#### 8.1 LibreChat als Frontend
```
Login → Chat mit NeXifyAI
               ↓
        Ich kann:
        - Fragen stellen
        - Aufträge erteilen
        - Status sehen
        - Aufgaben verwalten
```

#### 8.2 Dashboard-View
```
Metrics:
- Offene Aufgaben
- Leads diese Woche
- Offene Angebote
- Umsatz diesen Monat
- SLA-Compliance
```

#### 8.3 Paperclip-View embedded
```
Aufgaben:
- Meine Aufgaben
- Status ändern
- Details ansehen
- Kommentieren
```

#### 8.4 Quick Actions
```
"Neuer Lead" → öffnet intake-flow
"Neues Angebot" → öffnet pm-flow
"Support-Ticket" → öffnet ticket-flow
```

### Deliverable
✅ LibreChat = Arbeitsplatz. Alles an einem Ort.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 9: SELF-HEALING + AUTONOMER LOOP
## ═══════════════════════════════════════════════════════════════

### Ziel
System läuft 24/7. Fehler werden automatisch erkannt und behoben.

### Aufgaben

#### 9.1 Brain-Scanner (erweitert)
```
Alle 15 Min:
- Überfällige Tasks?
- Wissenslücken?
- Offene Feedbacks?
- SLA-Brüche?
```

#### 9.2 Monitoring-Trigger
```
System-Event → Oracle-Event
→ Task wird erstellt
→ Specialist wird benachrichtigt
→ Ergebnis wird verifiziert
```

#### 9.3 Self-Healing Loop
```
Task abgeschlossen
→ qa-agent prüft automatisch
→ Wenn Fehler → zurück an Specialist
→ Retry (max 3x)
→ Bei 3x Fail → Eskalation
```

#### 9.4 Autonomer Modus
```
Pascal ist nicht da → System läuft weiter
Nur bei kritischen Events → Alert an Pascal
Sonst: alles läuft autonom
```

### Deliverable
✅ System läuft 24/7. Kein Stillstand.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 10: DB-MIGRATION (Supabase)
## ═══════════════════════════════════════════════════════════════

### Ziel
Daten von Emergent auf eigene Supabase. Volle Kontrolle.

### Aufgaben

#### 10.1 Schema finalisieren
```
Basiert auf Phase 0.4 Design
Tables:
- tenants
- users
- customers
- projects
- tasks
- agent_runs
- audit_logs
- ...
```

#### 10.2 Data Migration
```
MongoDB (Emergent) → Postgres (Supabase)
Migration-Script schreiben
Test-Migration
Cutover planen
```

#### 10.3 Verification
```
Nach Migration:
- Alle Daten vollständig?
- Referenzen intakt?
- Kein Data Loss?
```

### Deliverable
✅ Eigene Supabase läuft. Emergent nicht mehr nötig.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 11: VERCEL TRENNEN
## ═══════════════════════════════════════════════════════════════

### Ziel
Klarheit: Was läuft wo? Kein unnötiger Ballast.

### Aufgaben

#### 11.1 Inventar machen
```
Was läuft aktuell auf Vercel?
- Frontend?
- Backend-APIs?
- Statische Files?
```

#### 11.2 Entscheidung
```
Option A: Alles auf eigene Infra
Option B: Nur Frontend auf Vercel, Backend lokal
Option C: Frontend woanders (z.B. Cloudflare Pages)
```

#### 11.3 Umsetzen
```
DNS umstellen
Deployment umstellen
Monitoring anpassen
```

### Deliverable
✅ Klarheit wo was läuft. Vercel-Verbindung bereinigt.

---

## ═══════════════════════════════════════════════════════════════
## PHASE 12: OPTIMIERUNG + DOKUMENTATION
## ═══════════════════════════════════════════════════════════════

### Ziel
System ist vollständig dokumentiert und optimiert.

### Aufgaben

#### 12.1 Betriebshandbuch
```
Wie bediene ich das System?
Wie erstelle ich einen Lead?
Wie genehmige ich ein Angebot?
Wie gehe ich mit Support um?
...
```

#### 12.2 Compliance-Matrix
```
ISO 9001, ISO 27001, DSGVO
Was ist implementiert?
Was fehlt noch?
```

#### 12.3 Cost Tracking
```
API-Kosten pro Agent/Task
Optimierungspotenzial?
Budget-Alerts?
```

### Deliverable
✅ System ist vollständig dokumentiert und optimiert.

---

## ═══════════════════════════════════════════════════════════════
## ZUSAMMENFASSUNG: PHASEN-ÜBERSICHT
## ═══════════════════════════════════════════════════════════════

```
PHASE 0: Fundament (Stabilisierung)
PHASE 1: Mandantentrennung (Security)
PHASE 2: Intake-Agent (Lead-Aufnahme)
PHASE 3: Research + Outreach (Akquise)
PHASE 4: E-Mail Integration (Kommunikation)
PHASE 5: Support + Tickets (Service)
PHASE 6: PM + Offer + Finance (Pipeline)
PHASE 7: Kalender + Termine (Scheduling)
PHASE 8: LibreChat Integration (Arbeitsplatz)
PHASE 9: Self-Healing + Autonom (24/7)
PHASE 10: DB-Migration (Supabase)
PHASE 11: Vercel trennen (Klarheit)
PHASE 12: Optimierung + Doku (Abschluss)
```

---

## NÄCHSTER SCHRITT

**Phase 0.1: mem0 OSS Test**

Test ob der mem0-Fix funktioniert hat:
```
mem0_search('restart checkpoint')
```
Sollte jetzt Ergebnisse MIT memory-Text liefern.

**Wenn das funktioniert → Phase 0.2: Docs in GitHub Repo syncen**

---

**Soll ich mit Phase 0.1 beginnen?**