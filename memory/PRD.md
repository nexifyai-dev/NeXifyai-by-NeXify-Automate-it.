# NeXifyAI Landing Page — Product Requirements Document

## Original Problem Statement
Premium DACH B2B landing page for "NeXifyAI by NeXify" — an enterprise AI automation company. Core claim: "Chat it. Automate it." Primary goal: generate qualified B2B strategy calls ("Strategiegespräch buchen"). Target: DACH Mittelstand (Germany, Austria, Switzerland).

## Brand
- **Name**: NeXifyAI by NeXify
- **Legal Entity**: NeXify Automate
- **CEO**: Pascal Courbois, Geschäftsführer
- **Locations**: DE (Wallstraße 9, 41334 Nettetal-Kaldenkirchen) + NL (Graaf van Loonstraat 1E, 5921 JA Venlo)
- **KvK**: 90483944 | **USt-ID**: NL865786276B01

## Architecture
- **Frontend**: React 18 SPA (CRA) at port 3000
- **Backend**: FastAPI at port 8001
- **Database**: MongoDB (motor async driver)
- **Auth**: JWT + Argon2 (pwdlib)
- **Email**: Resend API
- **Proxy**: package.json proxy forwards /api/* to backend

## What's Been Implemented (April 2026)

### Frontend
- [x] Hero section with ArchPanel visual
- [x] Solutions section (6 cards)
- [x] Use Cases section (bento grid)
- [x] App Development section (6 cards + highlight CTA)
- [x] Process section (4 steps)
- [x] Integrations section (64 integrations, 10 categories)
- [x] Governance section (DSGVO, ISO 27001 angestrebt, SOC 2 Roadmap)
- [x] Pricing section (3 tiers)
- [x] FAQ section (7 items, accordion)
- [x] Contact section (form + CTA)
- [x] Footer (company info, nav, legal links, cookie settings)
- [x] Live Chat modal (rule-based, keyword qualification)
- [x] Booking modal (date/time/form/success)
- [x] Cookie consent banner (accept/reject/reopen from footer)
- [x] Mobile responsive (tested 375-1920px, no horizontal scroll)
- [x] Legal pages: /impressum, /datenschutz, /agb, /ki-hinweise
- [x] Admin CRM: /admin (JWT login, stats, leads table, bookings, lead detail)
- [x] Logo: icon-mark.svg, logo-light.svg, logo-dark.svg
- [x] Typography: Plus Jakarta Sans (display) + Inter (body)
- [x] Accessibility: skip link, aria labels, keyboard nav, focus-visible
- [x] Analytics tracking (scroll depth, clicks, form submissions)

### Backend
- [x] FastAPI v3.0 with lifespan management
- [x] JWT auth (OAuth2PasswordRequestForm, Argon2 hashing)
- [x] POST /api/contact (lead creation + email notifications)
- [x] POST /api/booking (booking creation + confirmation emails)
- [x] GET /api/booking/slots (availability check)
- [x] POST /api/chat/message (rule-based advisor, qualification tracking)
- [x] POST /api/analytics/track (event tracking)
- [x] Admin: /api/admin/login, /stats, /leads, /bookings, /leads/:id (PATCH)
- [x] Rate limiting on all public endpoints
- [x] Resend email templates (customer confirmation + internal notification)
- [x] Audit logging

## Testing
- Backend: 84% pass rate (21/25, 4 skipped fixture issues)
- Frontend: 100% pass rate (all critical flows)
- Test report: /app/test_reports/iteration_3.json

## Backlog / Future
- P1: SEO schema markup (JSON-LD)
- P1: Proper cookie consent persistence settings page
- P2: LLM integration for chat (currently rule-based)
- P2: Admin: lead/booking export CSV
- P2: Admin: MFA support
- P3: Performance: Lighthouse optimization
- P3: A/B testing framework

---
*Letzte Aktualisierung: 02.04.2026*
