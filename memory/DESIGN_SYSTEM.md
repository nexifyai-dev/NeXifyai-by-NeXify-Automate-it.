# NeXifyAI — Design System Reference

## Core Tokens

### Farben
| Token | Wert | Verwendung |
|-------|------|------------|
| `--nx-bg` | `#0c1117` | Haupt-Hintergrund |
| `--nx-surface` | `rgba(14,20,28,0.6)` | Karten, Panels |
| `--nx-surface-hover` | `rgba(14,20,28,0.8)` | Karten Hover |
| `--nx-accent` | `#ff9b7a` | Primär-Akzent, CTAs |
| `--nx-accent-glow` | `rgba(255,155,122,0.06)` | Glow-Effekte |
| `--nx-text` | `#c8d1dc` | Standard-Text |
| `--nx-muted` | `#6b7b8d` | Sekundär-Text |
| `--nx-dim` | `rgba(255,255,255,0.25)` | Tertiär-Text |
| `--nx-border` | `rgba(255,255,255,0.04)` | Standard-Rahmen |
| `--nx-border-hover` | `rgba(255,155,122,0.12)` | Hover-Rahmen |
| `--nx-err` | `#ef4444` | Fehler |
| `--nx-success` | `#10b981` | Erfolg |
| `--nx-warn` | `#f59e0b` | Warnung |

### Typografie
| Token | Wert | Verwendung |
|-------|------|------------|
| `--f-display` | `'Inter', sans-serif` | Headlines, Buttons |
| `--f-body` | `'Inter', sans-serif` | Fließtext |
| H1 | `clamp(1.75rem, 3vw, 3rem)` | Hero, Seitenüberschriften |
| H2 | `clamp(1.25rem, 2vw, 1.75rem)` | Abschnitte |
| H3 | `.9375rem` | Karten-Titel |
| Body | `.8125rem` | Standard-Text |
| Small | `.75rem` | Labels, Metadaten |
| Micro | `.6875rem` | Badges, Timestamps |

### Abstände
| Token | Wert | Verwendung |
|-------|------|------------|
| `--pad` | `clamp(16px, 4vw, 40px)` | Responsive Padding |
| `--gap` | `clamp(8px, 2vw, 24px)` | Grid-Gap |
| Card Padding | `16px-28px` | Karten-Innenabstand |
| Section Gap | `48px-80px` | Zwischen Sektionen |

### Radien
| Token | Wert | Verwendung |
|-------|------|------------|
| Small | `6px` | Inputs, kleine Buttons |
| Medium | `8px-10px` | Karten, Panels |
| Large | `12px-14px` | Modals, große Karten |
| Pill | `20px` | Badges, Tags |
| Circle | `50%` | Avatare, Dots |

### Shadows & Effects
| Effekt | CSS |
|--------|-----|
| Card Glow | `box-shadow: 0 0 40px rgba(255,155,122,0.03)` |
| Modal Shadow | `box-shadow: 0 32px 80px rgba(0,0,0,0.4)` |
| Glass Effect | `backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px)` |
| Grain Overlay | `background-image: url(data:image/svg+xml,...) /* grain noise */` |

### Motion
| Animation | Dauer | Easing |
|-----------|-------|--------|
| Hover | `200ms` | `ease` |
| Entrance | `300-500ms` | Framer Motion defaults |
| Page Transition | `300ms` | `ease-in-out` |
| Spinner | `700ms` | `linear infinite` |

### Touch Targets
| Element | Min-Größe | Kontext |
|---------|-----------|---------|
| Buttons | `44px` | Mobile |
| Tab Items | `44px` | Mobile Tabs |
| Links | `44px` | Mobile Navigation |
| Icons (interaktiv) | `32px` | Desktop |

### Breakpoints
| Name | Wert | Kontext |
|------|------|---------|
| Mobile S | `360px` | Min. unterstützte Breite |
| Mobile | `480px` | Standard Mobile |
| Tablet | `768px` | Tablets |
| Desktop | `1200px` | Standard Desktop |
| Wide | `1920px` | Full HD |

## Anwendung im Code

### CSS-Import
Alle Tokens sind in `App.css` unter `:root` definiert.

### Konsistenzregel
Jede neue Komponente MUSS:
1. CSS-Variablen aus `:root` verwenden
2. Responsive via `clamp()` oder `@media` sein
3. Touch-Targets >= 44px auf Mobile
4. `data-testid` für jedes interaktive Element
5. `transition` auf spezifische Properties (nicht `all`)
