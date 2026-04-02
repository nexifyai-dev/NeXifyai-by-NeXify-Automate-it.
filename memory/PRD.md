# NeXifyAI Landing Page — Product Requirements Document

## Original Problem Statement
Premium DACH B2B landing page for "NeXifyAI by NeXify" — enterprise AI automation. Core claim: "Chat it. Automate it." Primary goal: generate qualified B2B strategy calls. Target: DACH Mittelstand.

## Brand & Legal
- **Name**: NeXifyAI by NeXify | **Entity**: NeXify Automate (NL, KvK: 90483944)
- **CEO**: Pascal Courbois | **USt-ID**: NL865786276B01
- **Applicable Law**: Dutch (Burgerlijk Wetboek), DSGVO/UAVG, EU AI Act

## Architecture
- Frontend: React 18 (CRA, port 3000) with proxy to backend
- Backend: FastAPI (port 8001), MongoDB (motor), JWT+Argon2 auth
- LLM: GPT-4o-mini via Emergent LLM Key (emergentintegrations)
- Email: Resend API

## Implemented Features (April 2026)

### Landing Page
- Hero, Solutions (6), Use Cases (bento), App Development (6+highlight), Process (4 steps)
- 64 Integrations in 10 categories, Governance, Pricing (3 tiers), FAQ (7), Contact form
- Footer with legal links + cookie settings reopener
- Logo system: icon-mark.svg, logo-light.svg, logo-dark.svg
- Typography: Plus Jakarta Sans (display) + Inter (body)

### LLM-Powered Chat
- GPT-4o-mini via Emergent key with comprehensive system prompt
- Context-aware responses about all services, pricing, integrations
- Qualification tracking (use case, interest area)
- **Chat-based booking**: LLM collects name/email/date, creates booking, sends confirmation email
- Dynamic date awareness (current date injected into system prompt)

### Admin CRM (/admin)
- JWT login (Argon2 hashing, OAuth2PasswordRequestForm)
- Dashboard: stats cards, leads table with search/filter/sort, lead detail drawer
- Bookings view, status management, internal notes
- Rate limit: 20 req/5min for login

### Legal & Compliance
- /impressum (TMG + Art. 3:15d BW), /datenschutz (DSGVO + UAVG + AVG)
- /agb (Boek 6 BW, NL law), /ki-hinweise (EU AI Act Art. 52, compliance matrix)
- Cookie consent (accept/reject/reopen from footer)

### UX/Performance
- Invisible scrollbars globally (scrollbar-width:none)
- Mobile responsive (360-1920px, no horizontal overflow)
- Container system with responsive padding (20-64px)
- Accessibility: skip link, ARIA labels, keyboard nav

## Testing (Iteration 4)
- Backend: 100% | Frontend: 100% | All critical features verified
- Test reports: /app/test_reports/iteration_4.json

## Backlog
- P1: SEO JSON-LD schema markup
- P1: Cookie settings granular page
- P2: Admin CSV export, MFA
- P3: Lighthouse optimization, A/B testing

---
*Letzte Aktualisierung: 02.04.2026*
