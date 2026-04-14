# NeXifyAI — Oracle-System Gesamtplan v1.0

## Erstellt: 2026-04-14
## Status: DESIGN PHASE — Wartet auf Umsetzungs-Start

---

## 1. SYSTEM-ÜBERSICHT

### Was wir bauen
Ein vollständiges, 24/7 autonomes System das:
- Chat-Nachrichten überwacht und Aufträge erkennt
- Brain-Wissen proaktiv scannt und Lücken als Aufträge generiert
- Monitoring-Events empfängt und reaktiv Aufträge erstellt
- Kleine, spezialisierte Agenten orchestriert
- Ergebnisse unabhängig verifiziert
- Alles in Brain und Paperclip persistiert

### Was NICHT gebaut wird (Schritt 1)
- Komplexe neue Frontends
- Neue Datenbanken
- Neue Cloud-Infrastruktur
- Alles was nicht direkt zum Oracle-System gehört

###tech-Stack für Oracle
- Paperclip: Control Plane (Aufträge, Agenten, Status)
- Hermes: Master-Agent (Oracle-Logik)
- mem0: Brain (STATE/KNOWLEDGE/TODO)
- Docker: Container für Specialist-Agents
- Cron/Webhook: Scanner-Trigger
-现有- Infrastruktur: Passt

---

## 2. PAPERCLIP-INTEGRATION

### Was Paperclip macht
- Zentrale Auftragsverwaltung
- Agent-Registrierung
- Status-Tracking
- Freigabe-Gates
- Audit-Trail

### Was wir brauchen
```
Company: NeXifyAI (intern)
Agenten:
- oracle-agent (Master)
- pm-agent
- coder-agent  
- research-agent
- content-agent
- qa-agent
- ops-agent
- doc-agent
- verify-agent

Auftrags-Status:
- backlog (generiert)
- todo (priorisiert, bereit)
- in_progress (in Bearbeitung)
- in_review (Verifizierung)
- blocked (wartet auf Gate/Info)
- done (abgeschlossen)
- cancelled (abgebrochen)
```

### API-Endpoints die wir nutzen
```
POST /api/v1/tasks              → Auftrag erstellen
GET  /api/v1/tasks?status=...   → Aufträge lesen
PATCH /api/v1/tasks/:id          → Status updaten
POST /api/v1/agent-runs         → Agent-Run starten
GET  /api/v1/agent-runs/:id     → Run-Status
```

### Paperclip Agent-Setup (heute schon möglich)
```sql
-- Oracle Agent
INSERT INTO agents (company_id, name, role, model, provider, api_key_hash, status)
VALUES ('neXifyAI-company-id', 'oracle-agent', 'orchestrator', 'minimax/minimax-m2.7', 'openrouter', 'hash', 'active');

-- Specialist Agents (Stub-Definitionen für später)
INSERT INTO agents (company_id, name, role, model, provider, status)
VALUES 
  ('neXifyAI-company-id', 'pm-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'coder-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'research-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'content-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'qa-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'ops-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'doc-agent', 'specialist', 'minimax/minimax-m2.7', 'openrouter', 'active'),
  ('neXifyAI-company-id', 'verify-agent', 'verifier', 'minimax/minimax-m2.7', 'openrouter', 'active');
```

---

## 3. SPECIALIST-AGENT-DEFINITIONEN

### 3.1 pm-agent
```
Zweck: Projektmanagement, Angebote, Aufwandsschätzungen
Trigger: User plant etwas / Entscheidung erforderlich
Input: Kontext, Scope, Zielgruppe
Output: Projektsteckbrief, Aufwandsschätzung, Angebotstext
Autonomie: Erstellt Entwürfe, braucht Freigabe für Versand
Gate: Angebotsversand
```

### 3.2 coder-agent
```
Zweck: Code, APIs, Fixes, Migrationen
Trigger: Auftrag mit code-requirement
Input: Spec, Kontext, Tech-Stack
Output: Code, Tests, PR
Autonomie: Schreibt Code + Tests, braucht Review
Gate: Produktive Deployments
```

### 3.3 research-agent
```
Zweck: DACH-Lead-Suche, Wettbewerbsanalyse, Marktrecherche
Trigger: Proaktiv oder Auftrag
Input: Suchkriterien, Scope
Output: Leads-Liste, Analysen, Reports
Autonomie: Vollständig autonom
Gate: Keines für Recherche, Outreach braucht Freigabe
```

### 3.4 content-agent
```
Zweck: Texte, SEO, Claims, Copy
Trigger: Auftrag oder Brain-Lücke
Input: Topic, Copy-Compiler-Schema
Output: Texte, Meta, CTA
Autonomie: Erstellt Entwürfe
Gate: Rechtlich kritische Claims brauchen Review
```

### 3.5 qa-agent
```
Zweck: E2E-Tests, Accessibility, Security, Regression
Trigger: Nach Code-Änderung oder periodisch
Input: Was wurde geändert, Test-Scope
Output: Testberichte, Findings, Screenshots
Autonomie: Vollständig autonom
Gate: Findings werden eskaliert
```

### 3.6 ops-agent
```
Zweck: Monitoring, Backups, Incidents, Deployments
Trigger: System-Event, heartbeat-Fehler, Timing
Input: Event-Daten, System-Status
Output: Incident-Reports, Rollback-Vorschläge, Fixes
Autonomie: Analysen autonom, Eingriffe mit Gate
Gate: Produktive Eingriffe, Deployments
```

### 3.7 doc-agent
```
Zweck: PDFs, Rechnungen, Angebote, E-Mails
Trigger: Auftrag oder Workflow-Trigger
Input: Template, Daten, Empfänger
Output: PDF/Entwurf, E-Mail-Entwurf
Autonomie: Erstellt Entwürfe
Gate: Versand
```

### 3.8 verify-agent
```
Zweck: Unabhängige Verifizierung aller Ergebnisse
Trigger: Nach Abschluss jedes Specialist-Auftrags
Input: Ergebnis + Prüfkriterien (DoD)
Output: bestanden / durchgefallen + Feedback
Autonomie: Vollständig unabhängig
Gate: Keiner — prüft nur
```

---

## 4. ORACLE-CORE-LOGIK

### Intent-Detection (Chat)
```python
# Pseudocode
def detect_intent(message):
    # Explizite Keywords
    if any(kw in message for kw in ['plan', 'umsetzen', 'machen', 'soll', 'brauchen']):
        return 'PLAN_INTENT'
    
    # Implizite Patterns
    if has_decision_context(message):
        return 'DECISION_INTENT'
    
    if asks_for_help(message):
        return 'HELP_INTENT'
    
    return None
```

### Brain-Scanner
```python
# Alle 15 Minuten
def scan_brain():
    # Suche überfällige Einträge
    overdue = mem0.search('overdue OR outdated OR needs_review', type='todo')
    
    # Suche offene Implikationen
    implications = mem0.search('decisions_needing_followup')
    
    # Suche Wissenslücken
    gaps = detect_knowledge_gaps(knowledge_base)
    
    # Generiere Aufträge
    for item in overdue + implications + gaps:
        create_task(item, priority='high')
```

### Monitoring-Watcher
```python
# Alle 5 Minuten
def check_monitoring():
    events = get_system_events()
    
    for event in events:
        if event.type == 'kpi_threshold_breach':
            create_task(f"KPI {event.kpi} unter Schwelle", priority='urgent')
        
        elif event.type == 'heartbeat_failed':
            create_task(f"Service {event.service} nicht erreichbar", priority='critical')
        
        elif event.type == 'new_lead':
            create_task(f"Neuer Lead: {event.lead}", priority='normal')
```

---

## 5. VERIFIER-LOGIK

### DoD-Prüfung (automated)
```python
def verify_result(task, result):
    checks = []
    
    # Check 1: Vollständigkeit
    checks.append(check_completeness(task, result))
    
    # Check 2: Qualität (keine Halluzinationen)
    checks.append(check_quality(result))
    
    # Check 3: Security (keine Secrets, keine Leaks)
    checks.append(check_security(result))
    
    # Check 4: Scope (nicht übertrieben)
    checks.append(check_scope(task, result))
    
    # Check 5: DoD-Kriterien (taskspezifisch)
    checks.append(check_dod(task, result))
    
    if all(checks):
        return VERIFIED
    else:
        return FAILED + feedback(checks)
```

### Feedback-Format
```json
{
  "status": "failed",
  "checks": [
    {"name": "completeness", "passed": true},
    {"name": "security", "passed": false, "issue": "API-Key in Output gefunden"}
  ],
  "feedback": "Security-Check fehlgeschlagen: Keine API-Keys oder Secrets im Output. Bitte bereinigen.",
  "retry": true
}
```

---

## 6. FEEDBACK-LOOPS

### Loop 1: Chat → Auftrag → Specialist → Verify → Brain
```
User chat → Oracle erkennt Intent → Paperclip-Auftrag → Specialist-Agent 
→ Ergebnis → verify-agent → (falls OK) → Brain-Update → Nächster Auftrag
```

### Loop 2: Brain-Scan → Auftrag → Specialist → Verify → Brain
```
Brain-Scanner (15min) → Findet Lücke/Overdue → Paperclip-Auftrag 
→ Specialist-Agent → Ergebnis → verify-agent → Brain-Update
```

### Loop 3: Monitoring → Auftrag → Ops/Specialist → Verify → Brain
```
Monitoring-Event → Oracle empfängt → Paperclip-Auftrag (priorität) 
→ ops-agent oder Specialist → Ergebnis → verify-agent → Brain + ggf. Alert
```

### Loop 4: Fehler → Retry mit Feedback
```
verify-agent lehnt ab → Feedback an Specialist 
→ Retry mit Korrektur → verify-agent → (Loop bis bestanden oder eskaliert)
```

---

## 7. SCANNER/TRIGGER-KONFIGURATION

### Chat-Überwachung
```
Option A: Webhook von LibreChat
  - Neue Message → POST /oracle/webhook/chat
  - Vorteil: Echtzeit
  - Nachteil: Integration nötig

Option B: Polling (jetzt)
  - Alle 1 Min Chat-History checken
  - Vorteil: Keine Integration nötig
  - Nachteil: 1 Min Latenz

Option C: Trigger bei eigener Antwort (heute am besten)
  - Wenn Hermes antwortet, prüfe ob Auftrag
  - Vorteil: Sofort umsetzbar
  - Nachteil: Nur bei eigener Aktivität
```

### Brain-Scanner
```yaml
# Alle 15 Minuten via Cron
cron:
  - name: brain-scan
    schedule: "*/15 * * * *"
    command: hermes oracle scan-brain
```

### Monitoring-Watcher
```yaml
# Alle 5 Minuten via Cron
cron:
  - name: monitoring-check
    schedule: "*/5 * * * *"
    command: hermes oracle check-monitoring
```

### System-Events (Webhook-fähig)
```
Heartbeat-Fehler → Monitoring-Tool → Webhook → Oracle
KPI-Breach → PostHog/Analytics → Webhook → Oracle
New Lead → CRM → Webhook → Oracle
Error → Sentry → Webhook → Oracle
```

---

## 8. 24/7 BETRIEBS-SETUP

### Was läuft permanent
1. Oracle-Core (Hermes mit Oracle-Prompt)
2. Cron-Scanner (Brain + Monitoring alle 5/15 Min)
3. Specialist-Agents (bei Bedarf, ephemeral)
4. Verifier (nach jedem Specialist-Abschluss)

### Restart-Logik
```
Docker Restart Policy: unless-stopped
Auto-Restart bei Crash
Max 3 Restart-Versuche, dann Alert
```

### Alerting
```
Bei: Crash, Loop-Detection, Max-Retries
→ Telegram/Discord an Pascal
→ Log für Review
```

---

## 9. IMPLEMENTIERUNGS-REIHENFOLGE

### Phase 1: Foundation (jetzt)
1. ✅ Oracle-Architektur designt
2. ⬜ Paperclip: NeXifyAI Company + 9 Agents anlegen
3. ⬜ Oracle-Prompt in mem0 speichern
4. ⬜ Specialist-Prompts definieren und in mem0 speichern
5. ⬜ Verify-Logik definieren
6. ⬜ Gesamtplan speichern

### Phase 2: Core-Loop (Tag 1)
1. ⬜ Oracle-Prompt aktivieren
2. ⬜ Chat-Trigger (eigene Antwort als Trigger)
3. ⬜ Paperclip-Task-Creation integrieren
4. ⬜ Specialist-Agent-Stubbs (heute nur 1-2)
5. ⬜ Verify-Agent integrieren
6. ⬜ Brain-Feedback-Loop

### Phase 3: Scanner (Tag 2)
1. ⬜ Brain-Scanner (Cron 15 Min)
2. ⬜ Monitoring-Watcher (Cron 5 Min)
3. ⬜ Webhook-Endpoints (für Zukunft)
4. ⬜ Alerting-Logik

### Phase 4: Specialist-Vervollständigung (Tag 3-5)
1. ⬜ pm-agent vollständig
2. ⬜ coder-agent vollständig
3. ⬜ research-agent vollständig
4. ⬜ content-agent vollständig
5. ⬜ qa-agent vollständig
6. ⬜ ops-agent vollständig
7. ⬜ doc-agent vollständig

### Phase 5: 24/7 Stabilisierung (Tag 6-7)
1. ⬜ Restart-Tests
2. ⬜ Loop-Detection
3. ⬜ Escalation-Tests
4. ⬜ Alerting-Tests
5. ⬜ Brain-Consistency-Tests

---

## 10. PAPIERCLIP-API-INTEGRATION (Code-Snippets)

### Task erstellen
```python
import requests

def create_task(title, description, priority='normal', tags=None):
    response = requests.post(
        'http://paperclip-nr7s-paperclip-1:3100/api/v1/tasks',
        headers={'Authorization': f'Bearer {PAPERCLIP_API_KEY}'},
        json={
            'company_id': 'neXifyAI-company-id',
            'title': title,
            'description': description,
            'status': 'backlog',
            'priority': priority,
            'tags': tags or []
        }
    )
    return response.json()
```

### Task-Status updaten
```python
def update_task_status(task_id, status, agent_run_id=None):
    data = {'status': status}
    if agent_run_id:
        data['agent_run_id'] = agent_run_id
    
    response = requests.patch(
        f'http://paperclip-nr7s-paperclip-1:3100/api/v1/tasks/{task_id}',
        headers={'Authorization': f'Bearer {PAPERCLIP_API_KEY}'},
        json=data
    )
    return response.json()
```

---

## 11. SECURITY & GOVERNANCE

### Mandantentrennung
- Alle Agents arbeiten nur im NeXifyAI-Company-Kontext
- Keine Cross-Tenant-Daten
- Brain-Einträge mit tenant-tag

### Secrets
- API-Keys nur in Paperclip (Agent-Definition)
- Keine Secrets in Brain-Einträgen
- Keine Secrets in Logs

### Audit-Trail
- Alle Task-Creations in Paperclip
- Alle Brain-Updates mit Metadaten
- Alle Verifier-Entscheidungen geloggt

### Eskalation
- Bei 3x Verify-Failed → Eskalation an Pascal
- Bei Loop-Detection → Stop + Alert
- Bei Crash → Auto-Restart + Alert

---

## 12. OFFENE PUNKTE

1. **Paperclip Company ID**: Muss aus DB abgefragt werden (company_id für NeXifyAI)
2. **API Key für Paperclip**: Ist bereits in Agent-Definition hinterlegt
3. **Webhook-URLs**: Müssen später konfiguriert werden (LibreChat, Monitoring)
4. **Specialist-Container**: Ob Docker-Compose oder EPHEMERAL via docker run
5. **Memory-Bereinigung**: Alte Entries archivieren (Retention-Policy)

---

## 13. NÄCHSTE SCHRITTE (Sofort)

```
1. Papierclip Company + Agents anlegen (DB)
2. Oracle-Prompt in mem0 speichern
3. Specialist-Prompts in mem0 speichern  
4. Verify-Logik in mem0 speichern
5. Gesamtplan in /opt/data/nexifyai/plans/ speichern
6. Oracle aktivieren (neuer Hermes-Session-Typ)
7. Test-Loop: Chat → Auftrag → Specialist → Verify → Brain
```

---

## 14. SUCCESS-CRITERIA

Das System ist erfolgreich wenn:
- [ ] Chat-Nachricht erkennt Intent und generiert Task in Paperclip
- [ ] Specialist-Agent kann aufgaben eigenständig bearbeiten
- [ ] Verifier prüft Ergebnis und gibt Feedback
- [ ] Brain wird nach jedem Loop aktualisiert
- [ ] Brain-Scanner generiert proaktive Aufgaben
- [ ] Monitoring-Events generieren reaktive Aufgaben
- [ ] System läuft 24/7 ohne manuelle Intervention
- [ ] Keine Halluzinationen in Brain gelangen
- [ ] Eskalation funktioniert bei Problemen
