# NeXifyAI — Vollständiges Design-System

## Design-Tokens (:root)

### CI-Farben
| Token | Wert | Zweck |
|-------|------|-------|
| `--nx-accent` | #ff9b7a | CI-Gelb (Primär-Akzent, CTAs, Highlights) |
| `--nx-accent-h` | #ffb59e | Hover-Variante CI-Gelb |
| `--nx-accent-bg` | rgba(255,155,122,0.07) | Hintergrund-Tint CI-Gelb |
| `--nx-accent-b` | rgba(255,155,122,0.18) | Border-Tint CI-Gelb |
| `--nx-blue` | #6B8AFF | CI-Blau (Sekundär, Info, Kontrast) |
| `--nx-blue-h` | #8DA4FF | Hover-Variante CI-Blau |
| `--nx-blue-bg` | rgba(107,138,255,0.07) | Hintergrund-Tint CI-Blau |
| `--nx-blue-b` | rgba(107,138,255,0.18) | Border-Tint CI-Blau |

### Oberflächen (dunkel → hell)
| Token | Wert | Verwendung |
|-------|------|------------|
| `--nx-bg` | #0c1117 | Haupthintergrund |
| `--nx-s1` | #131a22 | Eingabefelder, Card-Innenflächen |
| `--nx-s2` | #1a2230 | Erhöhte Flächen |
| `--nx-glass` | rgba(14,20,28,0.6) | Glasflächen (Cards, Panels) |
| `--nx-glass-h` | rgba(14,20,28,0.8) | Modale Glasflächen |

### Radien (abgestuft)
| Token | Wert | Verwendung |
|-------|------|------------|
| `--r-xs` | 4px | Kleine Inlines (Tags, Dots) |
| `--r-sm` | 6px | Buttons, Inputs, Badges, Small Cards |
| `--r-md` | 8px | Cards, Panels, Modals, Tables |
| `--r-lg` | 12px | Modale Overlays, große Panels |
| `--r-xl` | 16px | Hero-Elemente, Feature-Cards |
| `--r-pill` | 100px | Pills, Chips, Badges |

### Schatten (3-Stufen-Tiefe)
| Token | Wert | Verwendung |
|-------|------|------------|
| `--shadow-sm` | 0 1px 2px + border-glow | Standard (Buttons, Input-Focus) |
| `--shadow-md` | 0 4px 16px + border-glow | Hover-Lift (Cards, Dropdowns) |
| `--shadow-lg` | 0 12px 48px + border-glow | Modale, Overlays |
| `--shadow-glow` | 24px + 80px accent | CTA-Glow-Effekt |
| `--shadow-focus` | 3px ring + 20px glow | Focus-Ring (Accessibility) |

## Button-System

### Hierarchie
1. **Primary** (`.btn-primary`): Hauptaktionen (Speichern, Absenden, CTA)
2. **Secondary** (`.btn-secondary`): Nebenaktionen (Abbrechen, Filter)
3. **Tertiary** (`.btn-tertiary`): Dritte Priorität (Optionen, Extras)
4. **Outline** (`.btn-outline`): Visuell prominent aber nicht dominierend
5. **Ghost** (`.btn-ghost`): Minimal (Navigation, Links)
6. **Destructive** (`.btn-destructive`): Löschen, Abbrechen, Warnung
7. **Success** (`.btn-success`): Bestätigen, Akzeptieren
8. **Link** (`.btn-link`): Inline-Links
9. **Icon** (`.btn-icon`): Icon-Only (Toolbar, Actions)

### Größen
- `.btn-xs`: 5px 10px, 11px
- `.btn-sm`: 7px 14px, 13px
- (Standard): 10px 22px, 14px
- `.btn-lg`: 14px 28px, 15px
- `.btn-xl`: 16px 36px, 16px

### Modifikatoren
- `.btn-glow`: Accent-Glow-Effekt
- `.btn-full`: 100% Breite
- `.btn-pill`: Pill-Form
- `.btn-loading`: Spinner-Animation

### Zustände
- `:hover` → translateY(-1px) + shadow-lift
- `:active` → translateY(0) + inset shadow
- `:focus-visible` → shadow-focus ring
- `:disabled` → opacity 0.4, no pointer-events

## Flächen-System

### Card (`.nx-card`)
- Background: `--nx-glass` mit backdrop-filter
- Border: 1px `--nx-border`
- Radius: `--r-md`
- Top-Gradient-Line (::before)
- Hover: border-color accent-glow

### Panel (`.nx-panel`)
- Wie Card, ohne backdrop-filter
- Für Container-Elemente (Tables, Listen)

### Surface (`.nx-surface`)
- Solid background `--nx-s1`
- Für Inputs, Textarea-Container

## Regelwerk

### DO
- Immer CSS-Variablen statt hardcoded Farben
- Transitions auf spezifische Properties, nicht `all`
- Glass-Morphism für schwebende Flächen (backdrop-filter: blur(12px))
- Focus-Ringe mit `--shadow-focus` für Accessibility
- Hover-States mit subtiler Y-Translation + Schatten-Verstärkung

### DON'T
- Keine eckigen Elemente (immer mindestens `--r-xs`)
- Keine chaotischen Schatten (nur die 3 definierten Stufen)
- Keine hardcoded `#ff9b7a` — immer `var(--nx-accent)`
- Keine `transition: all` (bricht transforms)
- Keine unterschiedlichen Qualitätsniveaus zwischen Seiten
