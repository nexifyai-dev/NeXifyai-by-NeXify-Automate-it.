# NeXifyAI Oracle-Architektur v1.0

## Status
Design 2026-04-14. Wird umgesetzt nach Genehmigung.

## Überblick
Das Oracle-System ist das autonome Gehirn des NeXifyAI-Systems. Es läuft 24/7 und generiert, orchestriert und überwacht Aufträge aus drei Quellen: Chat, Brain und Monitoring.

## Kernprinzip
Kleine, spezialisierte Agenten. Nicht ein riesiger Agent, sondern viele kleine, fokussierte Einheiten.

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORACLE                                   │
│  ┌───────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ CHAT-WATCH │  │ BRAIN-SCANNER│  │ MONITORING-WATCHER    │   │
│  └─────┬─────┘  └──────┬───────┘  └───────────┬────────────┘   │
│        │                │                      │                │
│        └────────────────┼──────────────────────┘                │
│                         ▼                                       │
│              ┌──────────────────┐                              │
│              │  INTENT-DETECTOR │                              │
│              │  + REQUEST-GEN   │                              │
│              └────────┬─────────┘                              │
│                       ▼                                        │
│              ┌──────────────────┐                              │
│              │  PAPERCLIP       │  ← Control Plane             │
│              │  (Aufträge)      │                              │
│              └────────┬─────────┘                              │
│                       │                                        │
│        ┌──────────────┼──────────────┐                        │
│        ▼              ▼              ▼                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ Specialist│  │ Specialist│  │ Specialist│                     │
│  │  Agent   │  │  Agent   │  │  Agent   │                     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                     │
│       │             │             │                             │
│       └─────────────┼─────────────┘                             │
│                     ▼                                           │
│              ┌──────────────────┐                              │
│              │  VERIFIER        │  ← Unabhängige Prüfung       │
│              └────────┬─────────┘                              │
│                       │                                        │
│                       ▼                                         │
│              ┌──────────────────┐                              │
│              │  BRAIN          │  ← STATE/TODO/KNOWLEDGE     │
│              └──────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## Die drei Auftragsquellen

### 1. CHAT (Explicit/Implicit Intent)
- User plant, diskutiert, entscheidet
- Implizit: aus Kontext erkannt
- Explizit: User formuliert direkt

### 2. BRAIN (Proaktive Intelligenz)
- Regelmäßiger Scan aller Memories
- Erkennt: Wissenslücken, überfällige Prüfungen, offene Todos, veraltete Infos
- Generiert proaktive Aufträge

### 3. MONITORING (Reaktive Signale)
- System-Events, KPI-Brüche, Fehler
- Neue Leads, Deadlines, Termine
- heartbeat-Fehler, Backups überfällig

## Specialist Agents

| Agent | Verantwortung | Autonom bis |
|-------|--------------|-------------|
| pm-agent | Angebote, Projektbriefe, Aufwandsschätzungen | Vorlage fertig |
| coder-agent | Code, APIs, Migrationen, Fixes | Test grün |
| research-agent | DACH-Leads, Wettbewerb, Analysen | Recherche fertig |
| content-agent | Texte, SEO, Claims, Copy | Entwurf fertig |
| qa-agent | E2E, Accessibility, Security, Regression | Report fertig |
| ops-agent | Monitoring, Backups, Incidents, Deploys | Review fertig |
| doc-agent | PDFs, Rechnungen, Angebote, Mail | Entwurf fertig |
| verify-agent | Unabhängige Prüfung aller Ergebnisse | bestanden/ablehnt |

## Auftrags-Lebenszyklus

```
GENERIERT → PRIORISIERT → ZUGEWIESEN → IN_ARBEIT → FERTIG → VERIFIZIERT → BRAIN → (Loop)
     │           │            │            │          │         │          │
     │           │            │            │          │         │          ▼
     └───────────┴────────────┴────────────┴──────────┴─────────┴──→ NÄCHSTER
                                                                          AUFTRAG
```

## Autonomie-Grenzen

### Autonom (ohne Gate)
- Recherche, Analysen
- Code-Schreiben, Tests
- Content-Entwürfe
- interne Tasks
- Monitoring-Auswertungen

### Mit Gate (vor Ausführung)
- Outreach-Versand
- Angebotsversand
- Rechnungsversand
- Preisänderungen
- Produktive Deployments
- Sensible Datenfreigaben
- Kritische Security-Ops

## Feedback-Loop (24/7)

```
1. Oracle scannt alle X-Minuten (Chat + Brain + Monitoring)
2. Neue/überfällige Aufträge werden in Paperclip erstellt
3. Passende Specialist-Agenten werden gestartet
4. Ergebnis wird vom verify-agent geprüft
5. Alles fließt in Brain (STATE/TODO/KNOWLEDGE)
6. Bei Fehler: Rückgabe an Specialist mit Feedback
7. Loop beginnt von vorne
```

## Scanner-Intervalle

| Quelle | Intervall | Trigger |
|--------|-----------|---------|
| Chat | Echtzeit (Webhook/Poll) | Neue Message |
| Brain | Alle 15 Min | Timing-Trigger |
| Monitoring | Alle 5 Min | System-Event |

## Verifizierung

- verify-agent prüft unabhängig
- Kriterien: Vollständigkeit, Qualität, Sicherheit, DoD-Check
- Bei Fehler: Detail-Feedback an Specialist
- Bei Erfolg: Abschluss + Brain-Update

## Brain-Persistenz

Nach jedem abgeschlossenen Zyklus:
- STATE: Aktualisierte Systemzustände
- KNOWLEDGE: Neue Erkenntnisse, Entscheidungen, Patterns
- TODO: Nächste offene Aufgaben

## Risiken und Mitigations

| Risiko | Mitigations |
|--------|-------------|
| Agent-Schleifen (Endlosschleifen)) | Max-Iterations + Eskalation |
| Halluzinationen | Verifier-Gate vor Brain-Write |
| Cross-Tenant-Leaks | mandant Isolateon in allen Agents |
| Overload (zu viele Aufträge) | Priorisierung + Throttling |
| Stillstand (keine Aufträge) | Proaktive Brain-Scans |

## Next Steps

1. ✅ Oracle-Design speichern
2. Paperclip-Integration definieren
3. Specialist-Agent-Prompts erstellen
4. Verifier-Logik implementieren
5. Scanner/Trigger konfigurieren
6. Test-Loop aufsetzen
7. 24/7 Betrieb starten
