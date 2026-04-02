# NeXifyAI Landing Page - PRD

## Projektübersicht
**Projekt:** NeXifyAI by NeXify – Landing Page & Advisory Entry System
**Typ:** Hybrid (SaaS/Consulting/White-Label)
**Zielgruppe:** DACH-Mittelstand, B2B, Enterprise

## Original Problem Statement
Optimierung und Fehlerkorrektur eines bestehenden HTML-Prototyps für die NeXifyAI Landing Page mit folgenden Anforderungen:
- Design-Token und Design-System verwenden
- Unternehmensdaten fest hinterlegen
- Bestehende Fehler beheben und verfeinern
- Kein neues Design, sondern Verfeinerung

## Unternehmensdaten (Fix)
- **Marke:** NeXifyAI by NeXify
- **Claim:** Chat it. Automate it.
- **Rechtsform:** NeXify Automate
- **Geschäftsführer:** Pascal Courbois
- **NL-Adresse:** Graaf van Loonstraat 1E, 5921 JA Venlo
- **DE-Adresse:** Wallstraße 9, 41334 Nettetal-Kaldenkirchen
- **Telefon:** +31 6 133 188 56
- **E-Mail:** support@nexify-automate.com
- **Website:** nexify-automate.com
- **KvK:** 90483944
- **USt-ID:** NL865786276B01

## Implementierte Features

### ✅ Vollständig implementiert (02.04.2026)

1. **Navigation**
   - Responsive Navbar mit Mobile-Menü
   - Interne Anker-Navigation zu allen Sections
   - Sticky header mit Blur-Effekt

2. **Hero Section**
   - Editorial, links-ausgerichtetes Layout
   - Responsives Architecture Panel
   - Zwei CTAs (Potenzial analysieren, Lösungen ansehen)
   - Key-Stats Grid

3. **Solutions Grid**
   - 6 Lösungskarten mit Icons
   - Hover-Effekte
   - Responsive Grid-Layout

4. **Use Cases Section**
   - Bento-Grid Layout
   - Dashboard-Visualisierungen
   - Orchestrierungs-Diagramm

5. **Prozess Timeline**
   - 4-Schritt Workflow
   - Progress-Indikatoren
   - Responsive Grid

6. **Integrationen**
   - Microsoft 365, HubSpot, Salesforce, SAP
   - API-Badges (REST, Webhooks, Python SDK)

7. **Governance & Compliance**
   - DSGVO-konform
   - RBAC-Features
   - Audit-Logging
   - Zertifizierungsübersicht (ISO 27001 angestrebt, WCAG 2.2)

8. **Pricing Section**
   - 3-Tier Pricing (Starter €1.900, Growth €4.500, Enterprise individuell)
   - Highlight für empfohlenen Plan

9. **FAQ Section**
   - 5 vollständige Fragen mit Antworten
   - Accordion-Funktionalität
   - Tastatur-bedienbar

10. **Contact Form**
    - Validierung aller Felder
    - Backend-Integration (/api/contact)
    - Success/Error Feedback
    - Loading State

11. **Advisory Chat Modal**
    - Öffnen/Schließen (Button, ESC, Overlay-Click)
    - Starter-Fragen
    - Chat-Preview
    - Focus Trap

12. **Footer**
    - Korrekte Unternehmensdaten
    - Navigation Links
    - Rechtliche Links
    - KvK & USt-ID

## Tech Stack
- **Frontend:** React 18, CSS Custom Properties (Design Tokens)
- **Backend:** FastAPI, Pydantic
- **Fonts:** Manrope (Headlines), Inter (Body), Material Symbols
- **Icons:** Material Symbols Outlined

## Design System

### Farben
- Primary: #ffb599 (Orange)
- Background: #0e141b (Deep Navy)
- Surface: #1b2028, #171c23, #252a32
- Text: #dee3ed, #c5c6cb

### Typografie
- Headlines: Manrope 700-800
- Body: Inter 400-500
- Labels: Inter 700 uppercase

## API Endpoints
- `GET /api/health` - Health Check
- `GET /api/company` - Unternehmensdaten
- `POST /api/contact` - Kontaktformular
- `POST /api/newsletter` - Newsletter

## Bekannte Annahmen
1. SOC 2 Type II auf "In Vorbereitung" gesetzt (kein falscher Claim)
2. ISO 27001 als "angestrebt" markiert
3. Fiktiver CTO-Quote entfernt
4. Alle Links sind interne Anker (keine #-Platzhalter mehr)

## Prioritized Backlog

### P0 - Erledigt
- [x] Alle # Links durch echte Anker ersetzen
- [x] Footer-Daten korrigieren
- [x] FAQ mit Antworten befüllen
- [x] Contact Form Validierung
- [x] Mobile Navigation

### P1 - Future
- [ ] Cookie-Consent Banner
- [ ] Impressum Seite
- [ ] Datenschutz Seite
- [ ] AGB Seite
- [ ] CRM-Integration (HubSpot)
- [ ] Email-Service Integration (Resend/SendGrid)

### P2 - Nice to have
- [ ] Chat mit echtem AI-Backend (Mem0 + DeepSeek)
- [ ] Analytics Integration
- [ ] A/B Testing Setup
- [ ] Performance Monitoring

## Test Status
- Backend: 100% (7/7 Tests bestanden)
- Frontend: 95% (FAQ Fix angewendet)
- E2E: Nicht verfügbar (Preview-Service temporär offline)

---
*Letzte Aktualisierung: 02.04.2026*
