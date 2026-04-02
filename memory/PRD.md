# NeXifyAI Landing Page — Product Requirements Document

## Original Problem Statement
Premium DACH B2B landing page for "NeXifyAI by NeXify" — enterprise AI automation. Core claim: "Chat it. Automate it." Primary goal: generate qualified B2B strategy calls. Target: DACH + NL + Global. **Real 3D animated web experience with full multilingual support.**

## Brand & Legal
- **Name**: NeXifyAI by NeXify | **Entity**: NeXify Automate (NL, KvK: 90483944)
- **CEO**: Pascal Courbois | **USt-ID**: NL865786276B01
- **Applicable Law**: Dutch (Burgerlijk Wetboek), DSGVO/UAVG, EU AI Act

## Architecture
- Frontend: React 18 (CRA, port 3000) with Three.js 3D animations
- Backend: FastAPI (port 8001), MongoDB (motor), JWT+Argon2 auth
- 3D: @react-three/fiber v8, @react-three/drei v9, three v0.170
- LLM: GPT-4o-mini via Emergent LLM Key (emergentintegrations)
- Email: Resend API
- i18n: Custom React Context + translations.js (DE/NL/EN)
- SEO: react-helmet-async, JSON-LD, hreflang, Open Graph
- Chat: react-markdown + remark-gfm for formatted responses

## Implemented Features

### Chat Icon Fix + LLM Quality Upgrade — April 2026 (Iteration 10)
- **Replaced Material Symbols**: chat_bubble icon replaced with inline SVG arrows (no external font dependency)
- **System Prompt v2**: Added GESPRÄCHSSTIL UND TONALITÄT — conversational, proactive but not pushy
- **Restored booking instructions**: TERMINBUCHUNG section was accidentally deleted, now restored
- **Welcome messages**: More engaging, proactive in all 3 languages

### Form Label Fix + i18n Completion — April 2026 (Iteration 9)
- Fixed duplicate "Name" labels → proper Vorname/Nachname separation
- Fixed hardcoded "Telefon" → translated phone labels
- Complete i18n coverage for all form fields

### AI Chat Markdown + 3D Graphics — April 2026 (Iteration 8)
- ReactMarkdown rendering for bold, lists, headings
- Process Pipeline v2, Orchestration Hub-Spoke, Enhanced Globe

### Admin CRM + Calendar — April 2026 (Iteration 7)
- Monthly calendar, slot blocking, customer management

### Multilingual + SEO + 400+ Integrations (Iterations 5-6)
- IP-based language detection, 3 language translations, JSON-LD, hreflang

## Testing History
- Iteration 7: 28/28 — Admin Calendar, CRM
- Iteration 8: 40/40 — Chat markdown, 3D graphics
- Iteration 9: 40/40 — Form labels, i18n completion
- Iteration 10: 40/40 — Chat icons, LLM quality, booking flow

## Upcoming Tasks
- P1: Automated email sequences (booking confirmation, 24h reminder, 48h follow-up)
- P1: Lighthouse Performance Optimization (3D lazy-loading, font preloading)
- P2: Analytics Dashboard in Admin area
- P2: App.js Refactoring (>740 lines)

## Backlog
- Cookie settings granular page
- Admin CSV export, MFA
- A/B testing framework

---
*Last updated: 02.04.2026 — Chat icon fix, LLM quality upgrade, booking flow restored. Iteration 10: 40/40 tests PASSED.*
