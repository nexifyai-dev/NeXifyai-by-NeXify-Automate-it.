# NeXifyAI — Lücken-Analyse
## Abgleich: Gesendete Dokumente vs. Oracle-Design vs. Ist-Zustand

**Erstellt:** 2026-04-14
**Grundlage:** Master Prompt v2.0, DOS v2.0, Projekt-Template v2.0, Memory Context, Ist-Zustand

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 1: VOLLSTÄNDIG ABGEDECKT ✓
## ═══════════════════════════════════════════════════════════════

### ✅ Bereits im Oracle-Design
- 3 Ebenen Memory (STATE/KNOWLEDGE/TODO)
- Kleine, spezialisierte Agents
- Verify-Agent (unabhängige Prüfung)
- Feedback-Loops mit Retry (max 3x)
- Freigabe-Gates für kritische Aktionen
- Autonomie-Grenzen definiert
- 8-Stufen Copy-Compiler
- Quality Gates
- Brain-Scanner
- Monitoring-Watcher
- MiniMax M2.7 als primäres Modell

### ✅ Bereits im System (funktioniert)
- Oracle Engine mit 12 Status
- 10 spezialisierte Agents (backend)
- billing_routes (Rechnungen)
- oracle_routes (Tasks)
- comms_routes (Kommunikation)
- OutboundLeadMachine

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 2: LÜCKEN — FEHLENDE AGENTS
## ═══════════════════════════════════════════════════════════════

### 🔴 KRITISCH — Im Master Prompt definiert, NICHT in Oracle

| Agent | Definiert in | Status | Lücke |
|--------|-------------|--------|-------|
| **intake-agent** | Master Prompt (10 im System) | FEHLT in Oracle-Design | Muss: Leadaufnahme, Discovery, Erstklassifikation |
| **outreach-agent** | Master Prompt (10 im System) | FEHLT in Oracle-Design | Muss: Personalisierte Erstansprache, Nachfass-Kommunikation |
| **pm-agent** | Master Prompt |teilweise (pm in planner) | Muss: Projektsteckbrief, Aufwandsschätzung, Angebotsentwurf |
| **sales/scraper-agent** | Master Prompt | FEHLT | Muss: DACH-Lead-Suche, Outreach-Entwürfe |

### 📊 Vergleich: 10 Agents im System vs. 8 im Oracle-Design

```
SYSTEM (Backend):          ORACLE-DESIGN:
1. intake          ❌      1. pm-agent        ✓
2. research        ✓       2. coder-agent     ✓
3. outreach        ❌      3. research-agent  ✓
4. offer           ~       4. content-agent   ✓
5. planning        ✓       5. qa-agent       ✓
6. finance         ✓       6. ops-agent      ✓
7. support         ✓       7. doc-agent      ✓
8. design          ✓       8. verify-agent  ✓
9. qa              ✓
10. orchestrator   ✓
```

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 3: LÜCKEN — FEHLENDE BUSINESS-FUNKTIONEN
## ═══════════════════════════════════════════════════════════════

### 🔴 KRITISCH — Im Projekt-Template definiert, NICHT implementiert

| Funktion | Quelle | Status | Lücke |
|----------|--------|--------|-------|
| **E-Mail EINGANG bearbeiten** | Projekt-Template | FEHLT | Empfangene E-Mails lesen, klassifizieren, beantworten |
| **Kalender/Termine** | Projekt-Template | FEHLT | Termine buchen, verwalten, Erinnerungen |
| **Vertragsmanagement** | Projekt-Template | SEPARAT (contract_routes) | Lebenszyklus: Entwurf → Prüfung → Signatur → Archiv |
| **Kundenportal (komplett)** | Projekt-Template, DOS | PARTIELL | Kunde muss alles selbst machen können |
| **Inbound Lead Flow** | Master Prompt | FEHLT | Leads empfangen, qualifizieren, weiterleiten |

### 🟡 MITTEL — Fehlende Workflows

| Funktion | Quelle | Status | Lücke |
|----------|--------|--------|-------|
| **Rechnung erstellen → PDF → E-Mail → Bezahlen** | Projekt-Template | PARTIELL | Komplett-Pipeline fehlt |
| **Angebot erstellen → PDF → E-Mail → Verhandeln → Abschluss** | Projekt-Template | PARTIELL | Komplett-Pipeline fehlt |
| **Support-Ticket → Bearbeiten → Lösen → Archivieren** | Master Prompt | PARTIELL | Nur als Agent, nicht als Lifecycle |
| **Outbound Kampagne → Lead → Ansprache → Follow-up** | Master Prompt | PARTIELL | OutboundLeadMachine existiert, aber nicht im Oracle |

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 4: LÜCKEN — TECHNISCHE ANFORDERUNGEN
## ═══════════════════════════════════════════════════════════════

### 🔴 KRITISCH — Security/Compliance

| Anforderung | Quelle | Status | Lücke |
|-------------|--------|--------|-------|
| **Mandantentrennung** | DOS Guardrail #8 | FEHLT | Keine tenant_id in mem0/Oracle, Cross-Tenant möglich! |
| **ISO 9001 Compliance** | Master Prompt | FEHLT | Audit-Trail, CAPA, Review-Prozesse nicht im Oracle |
| **ISO 27001 Security** | Master Prompt | FEHLT | Security-Review, Penetrationstest-Plan fehlt |
| **DSGVO/GDPR** | Projekt-Template | FEHLT | Kein Löschkonzept, kein Export, keine Anonymisierung |
| **RBAC/2FA** | DOS Security | PARTIELL | Vorhanden, aber nicht in mem0/Oracle integriert |

### 🟡 MITTEL — Daten & Monitoring

| Anforderung | Quelle | Status | Lücke |
|-------------|--------|--------|-------|
| **Cost Tracking** | — | FEHLT | Keine API-Kosten pro Agent/Task/Agent-Run |
| **Daten-Retention** | — | FEHLT | Keine Cleanup/Archivierungs-Policy |
| **Disaster Recovery** | DOS | FEHLT | Kein Backup-Konzept, kein RTO/RPO |
| **Webhook-Integration** | DOS Trigger | FEHLT | Externe Systeme können Oracle nicht auslösen |

### 🟡 MITTEL — Performance

| Anforderung | Quelle | Status | Lücke |
|-------------|--------|--------|-------|
| **Event-Taxonomy** | Master Prompt | FEHLT | page_view, cta_click etc. nicht implementiert |
| **Lighthouse CI** | DOS | FEHLT | Performance-Checks nicht automatisiert |
| **Load Balancing** | — | FEHLT | Kein HA-Setup für Oracle-Engine |

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 5: LÜCKEN — MEMORY CONTEXT ANFORDERUNGEN
## ═══════════════════════════════════════════════════════════════

### 🔴 AUS MEMORY CONTEXT — Nicht umgesetzt

| Anforderung | Memory Context | Status | Lücke |
|-------------|----------------|--------|-------|
| **Chat → Erfolg → Autonome Überprüfung durch AI Agent** | Memory | FEHLT | Nach Auftrag-Erfolg kein automatischer QA-Trigger |
| **Fehler/Erfolg → Rückmeldung an Oracle → Feedback-Loop** | Memory | PARTIELL | Verify-Agent existiert, aber Feedback-Loop nicht vollständig |
| **24/7 autonom, NICHT nur wenn Pascal am PC** | Memory | PARTIELL | Scanner läuft, aber kein vollständiger Auto-Modus |
| **Alles aus Wissen + Monitoring → Aufträge** | Memory | PARTIELL | Brain-Scanner existiert, aber Monitoring-Integration fehlt |

### 🟡 SELF-HEALING LOOP

| Schritt | Memory Context | Status | Lücke |
|---------|----------------|--------|-------|
| 1. Auftrag erstellt | Memory | ✓ | |
| 2. Specialist arbeitet | Memory | ✓ | |
| 3. Erfolg/Fehler | Memory | ✓ | |
| 4. **Autonome Überprüfung** | Memory | ❌ | Kein automatischer QA-Trigger |
| 5. **Ergebnis rückmelden an Agent** | Memory | ❌ | Kein Feedback an Specialist-Agent |
| 6. **Agent legt ab oder next Auftrag** | Memory | ❌ | Nicht im geschlossenen Loop |

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 6: LÜCKEN — DOKUMENTATION & GOVERNANCE
## ═══════════════════════════════════════════════════════════════

### 🟡 Fehlende Dokumente aus Projekt-Template

| Dokument | Projekt-Template | Status |
|----------|-----------------|--------|
| **Normen-Compliance-Matrix** | Pflicht | FEHLT |
| **Datenquellen-Matrix** | Pflicht | FEHLT |
| **Rollenmatrix** | Pflicht | FEHLT (nur grob) |
| **Risiko-Register** | Pflicht | FEHLT |
| **ADR (Architektur-Entscheidungen)** | Pflicht | FEHLT |
| **Betriebshandbuch** | Pflicht | FEHLT |

### 🟡 Fehlende Templates

| Template | Projekt-Template | Status |
|----------|-----------------|--------|
| **Projekt-Stammdaten-Blatt** | Pflicht | FEHLT |
| **Funnel-Mapping** | Pflicht | FEHLT |
| **KPI-Dashboard-Blueprint** | Pflicht | FEHLT |

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 7: LÜCKEN — LIBRECHAT INTEGRATION
## ═══════════════════════════════════════════════════════════════

### 🔴 KRITISCH — LibreChat als Arbeitsplatz

| Anforderung | Status | Lücke |
|-------------|--------|-------|
| **LibreChat = Login + Chat + Dashboard** | OFFEN | Muss komplett geplant werden |
| **Paperclip-View im Dashboard** | OFFEN | Aufträge sehen, Status ändern |
| **Metrics/Stats anzeigen** | OFFEN | KPIs, Cycle-Count, Erfolge |
| **Backend-APIs an LibreChat** | OFFEN | Anbindung existiert nicht |
| **Auth-Flow (Single Sign-On)** | OFFEN | Admin-Login = LibreChat-Login |

---

## ═══════════════════════════════════════════════════════════════
## KATEGORIE 8: LÜCKEN — DB & INFRASTRUKTUR
## ═══════════════════════════════════════════════════════════════

### 🔴 KRITISCH — Datenbank

| Thema | Status | Lücke |
|-------|--------|-------|
| **Supabase-Migration** | OFFEN | Emergent → eigene Supabase |
| **Schema-Design** | OFFEN | Vollständiges DB-Schema fehlt |
| **MongoDB → Postgres** | OFFEN | Migration aller Daten |
| **mem0 OSS Schema** | PARTIELL | läuft, aber nicht vollständig integriert |

### 🟡 Infrastructure

| Thema | Status | Lücke |
|-------|--------|-------|
| **Vercel-Verbindung** | OFFEN | Trennen oder neu aufsetzen |
| **Docker-Orchestrierung** | PARTIELL | Läuft, aber nicht dokumentiert |
| **CI/CD Pipeline** | FEHLT | GitHub Actions existieren, aber nicht für Oracle |

---

## ═══════════════════════════════════════════════════════════════
## ZUSAMMENFASSUNG: PRIORITÄTEN
## ═══════════════════════════════════════════════════════════════

### P1 — MÜSSEN (System funktioniert nicht ohne)

```
1. intake-agent → Lead-Aufnahme, Discovery
2. outreach-agent → Erstansprache, Nachfass
3. E-Mail EINGANG bearbeiten → Empfangene E-Mails beantworten
4. LibreChat-Integration → Arbeitsplatz fertig
5. Mandantentrennung → Security-Basis
6. DB-Migration → Supabase sauber
7. Vertrag-Pipeline → Angebote → Rechnungen
8. Kalender/Termine → Terminbuchung
```

### P2 — SOLLTEN (System ist sonst unvollständig)

```
9. Self-Healing Loop → Autonomer QC-Cycle
10. Cost Tracking → API-Kosten pro Task
11. Brain-Scanner erweitern → Mehr Trigger
12. Webhook-Integration → Externe Systeme
13. Normen-Compliance-Matrix → Audit-Fähigkeit
14. Daten-Retention → Cleanup-Policy
```

### P3 — KÖNNEN (Verbesserungen)

```
15. ISO 9001/27001 Audit-Trail
16. Lighthouse CI Integration
17. High Availability Setup
18. Disaster Recovery Plan
19. Vollständiges Betriebshandbuch
20. ADR-Dokumentation
```

---

## ═══════════════════════════════════════════════════════════════
## MANDANTENTRENNUNG — DETAIL
## ═══════════════════════════════════════════════════════════════

**CRITICAL SECURITY ISSUE:**

Aktuell kann ein Agent eines Kunden Daten eines anderen Kunden sehen!

LÖSUNG (muss implementiert werden):
```
Every Agent-Run bekommt:
- tenant_id (Welcher Kunde?)
- company_id (Welches Unternehmen?)
- user_id (Welcher Mitarbeiter?)

Jede DB-Query filtert automatisch:
WHERE tenant_id = :current_tenant

mem0-Einträge bekommen tenant-tag
Oracle-Tasks bekommen tenant_id
Alle Agents arbeiten nur im eigenen Tenant
```

---

## ═══════════════════════════════════════════════════════════════
## EMPFOHLENE NEUE AGENT-DEFINITION (10 statt 8)
## ═══════════════════════════════════════════════════════════════

```
ORACLE SPECIALISTS:
├── oracle-core        (bestehend, orchestriert)
├── pm-agent           (Projektmanagement, Angebote)
├── intake-agent       (Lead-Aufnahme, Discovery)          ← NEU
├── research-agent     (Recherche, Analyse)
├── outreach-agent     (Erstansprache, Follow-up)           ← NEU
├── sales-agent        (DACH-Leads, Kampagnen)              ← NEU (oder outreach erweitern)
├── content-agent     (Texte, SEO, Copy)
├── finance-agent     (Rechnungen, Zahlungen)
├── support-agent     (Kundenservice, Tickets)
├── ops-agent          (Monitoring, Backups, Incidents)
├── doc-agent          (PDFs, E-Mails)
├── qa-agent          (Tests, Prüfungen, Self-Healing)
└── verify-agent      (Unabhängige Verifizierung)
```

---

## NÄCHSTE SCHRITTE (nach Lücken-Analyse)

1. ✅ Lücken-Analyse erstellt
2. ⬜ P1 Agents definieren (intake, outreach)
3. ⬜ E-Mail-Flow definieren (eingehend + ausgehend)
4. ⬜ LibreChat-Integration planen
5. ⬜ Mandantentrennung im Oracle implementieren
6. ⬜ DB-Migration starten (Supabase)
7. ⬜ Self-Healing Loop implementieren
