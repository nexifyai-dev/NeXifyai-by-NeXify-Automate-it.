# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-first commercial system "Starter/Growth AI Agenten AG" for NeXifyAI. Full-stack platform with React frontend, FastAPI backend, MongoDB. Multi-language (DE/NL/EN). Enterprise-grade compliance (DSGVO, EU AI Act).

## Core Requirements
1. Landing page with 3D, multi-language, Trust/Compliance, Chat Discovery
2. Commercial Engine: Quotes, Invoices, PDF generation, Revolut payment
3. Magic Link customer portal for quote acceptance
4. Admin Dashboard / CRM with full entity management
5. Premium Integrations section (categorized, SEO-linked)
6. Dedicated SEO landing pages per integration (/integrationen/:slug)
7. KI-gesteuertes SEO as standalone product
8. Full Services + Bundles pricing architecture
9. PDF tariff comparison sheets (CI-branded)
10. Legal compliance (AGB, Datenschutz, KI-Hinweise) — trilingual
11. Trust section with operational security
12. AI advisor with full product matrix + memory
13. **LeadFlow: All CTAs → AI Chat (not booking calendar)**
14. **Customer Memory Model (contextual conversations)**
15. **Customer Portal (/portal) with Magic Link access**
16. **WhatsApp button (left side, +31613318856)**
17. **Professional email signatures with legal links**

## Architecture (Post Phase 4)
```
/app/frontend/src/
├── App.js (495 lines — Nav, Hero, Sections, WhatsApp, CookieConsent)
├── components/
│   ├── sections/ (Integrations, LiveChat, SEOProduct, ServicesAll, TrustSection, BookingModal)
│   ├── shared/index.js (API, COMPANY, animations, utilities)
│   ├── Scene3D.js, SEOHead.js, LanguageSwitcher.js
│   └── ui/ (Shadcn components)
├── data/ (integrations.js, products.js)
├── pages/ (Admin.js, CustomerPortal.js, IntegrationDetail.js, LegalPages.js, QuotePortal.js)
└── i18n/ (LanguageContext.js, translations.js)

/app/backend/
├── server.py (2400 lines — API routes, auth, chat, memory, admin, portal)
└── commercial.py (1600 lines — tariffs, PDF, quote/invoice generation)
```

## API Endpoints (Updated)
### Product
- GET /api/product/tariff-sheet, /descriptions, /tariffs, /services, /faq, /compliance
### Commercial
- POST /api/commercial/quote, GET /api/admin/quotes, /invoices, /commercial/stats
### Chat
- POST /api/chat/message (with customer memory injection)
### Admin (new)
- GET /api/admin/timeline, /chat-sessions, /chat-sessions/{id}, /customer-memory/{email}
- POST /api/admin/leads/{id}/notes
### Portal (new)
- GET /api/portal/customer/{token}
### Existing
- POST /api/booking, GET /api/booking/slots, POST /api/contact, /api/admin/login

## Testing Status
- Iteration 16: 100% (23/23)
- Iteration 17: 100% (19/19 backend + full frontend)
- Iteration 18: 100% (22/22 backend + full frontend)

## Completed Phases
- Phase 1: Foundation (landing page, 3D, integrations, legal)
- Phase 2: Commercial System (quotes, invoices, PDF, Revolut)
- Phase 3: Self-Healing (76 umlauts fixed, header hardened, data sync, refactoring)
- Phase 4: LeadFlow + CRM + Customer Portal + Memory + WhatsApp + Signature

## Prioritized Backlog
### P0 — None

### P1 (Next)
- Resend live API key (email sending)
- Revolut live keys (payment processing)
- Complete email communication flows (auto-responses, support routing)
- Dunning logic for overdue invoices
- Admin CSV export

### P2 (Future)
- Customer dashboard beyond Magic Link (OTP/session auth)
- Subscription recurring billing API
- A/B testing CTAs
- Swagger/OpenAPI docs
- CI/CD pipeline with E2E tests
