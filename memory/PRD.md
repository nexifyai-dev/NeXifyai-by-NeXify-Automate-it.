# NeXifyAI Landing Page — Product Requirements Document

## Original Problem Statement
Premium DACH B2B landing page for "NeXifyAI by NeXify" — enterprise AI automation. Core claim: "Chat it. Automate it." Primary goal: generate qualified B2B strategy calls. Target: DACH Mittelstand. **Now with real 3D animated web experience.**

## Brand & Legal
- **Name**: NeXifyAI by NeXify | **Entity**: NeXify Automate (NL, KvK: 90483944)
- **CEO**: Pascal Courbois | **USt-ID**: NL865786276B01
- **Applicable Law**: Dutch (Burgerlijk Wetboek), DSGVO/UAVG, EU AI Act

## Architecture
- Frontend: React 18 (CRA, port 3000) with Three.js 3D animations
- Backend: FastAPI (port 8001), MongoDB (motor), JWT+Argon2 auth
- 3D: @react-three/fiber v8.18.0, @react-three/drei v9.122.0, three v0.170.0
- LLM: GPT-4o-mini via Emergent LLM Key (emergentintegrations)
- Email: Resend API

## Implemented Features (April 2026)

### 3D Animated Landing Page (v5.0)
- **HeroScene**: Neural network constellation (80 nodes, 100 edges), floating icosahedron core with distort material, data streams, accent geometries (spheres, torus, boxes)
- **IntegrationsGlobe**: Wireframe sphere with equatorial ring, 50 surface nodes, 16 connection arcs
- **ProcessScene**: 4 pipeline nodes with glow rings and connectors
- Premium CSS: glass-morphism, grain texture overlay, animated gradient borders, glow effects
- All 3D canvases properly z-indexed (background layer, no interaction blocking)

### Landing Page Sections
- Hero, Solutions (6 glass cards), Use Cases (bento grid), App Development (6+highlight)
- Process (4 steps with gradient numbers), 64 Integrations in 10 categories with 3D globe
- Governance (compliance matrix), Pricing (3 tiers), FAQ (7 accordion), Contact form
- Footer with legal links + cookie settings reopener
- Logo: icon-mark.svg | Typography: Plus Jakarta Sans + Inter

### LLM-Powered Chat
- GPT-4o-mini via Emergent key with comprehensive system prompt
- Context-aware responses, qualification tracking, chat-based booking
- Dynamic date awareness

### Admin CRM (/admin)
- JWT login (Argon2 hashing), dashboard with stats/leads/bookings
- Search, filter, sort, status management, internal notes
- Rate limit: 20 req/5min for login

### Legal & Compliance
- /impressum (TMG + Art. 3:15d BW), /datenschutz (DSGVO + UAVG)
- /agb (Boek 6 BW), /ki-hinweise (EU AI Act Art. 52)
- Cookie consent (accept/reject/reopen)

### UX/Performance
- Invisible scrollbars, mobile responsive (360-1920px)
- 3D DPR capped at 1.5 for performance
- Accessibility: skip link, ARIA labels, keyboard nav

## Testing (Iteration 5) — April 2026
- Backend: 100% (18/18 tests passed)
- Frontend: 100% (all critical features verified)
- Note: Headless Chrome may crash (SIGSEGV) due to WebGL — real browsers work fine

## Upcoming Tasks
- P1: Lighthouse Performance Optimization (3D canvas lazy-loading, font preloading)
- P2: SEO JSON-LD schema markup
- P2: Final E2E Visual Audit

## Backlog
- P1: Cookie settings granular page
- P2: Admin CSV export, MFA
- P3: A/B testing

---
*Letzte Aktualisierung: 02.04.2026 — 3D Premium Design v5.0 deployed, all tests PASSED*
