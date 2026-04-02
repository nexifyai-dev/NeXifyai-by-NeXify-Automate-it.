# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-first commercial system "Starter/Growth AI Agenten AG" for NeXifyAI. Full-stack platform with React frontend, FastAPI backend, MongoDB. Multi-language (DE/NL/EN). Revolut Merchant API for payments. Enterprise-grade compliance (DSGVO, EU AI Act).

## User Persona
Pascal Courbois — CEO, NeXify Automate. DACH/Benelux markets. B2B customers seeking KI-Agenten, Websites, Apps, SEO.

## Core Requirements (Static)
1. Landing page with 3D, multi-language, Trust/Compliance, Chat Discovery
2. Commercial Engine: Quotes, Invoices, PDF generation, Revolut payment
3. Magic Link customer portal for quote acceptance
4. Admin Dashboard for commercial management
5. Premium Integrations section (categorized, SEO-linked)
6. Dedicated SEO landing pages per integration (/integrationen/:slug)
7. KI-gesteuertes SEO as standalone product with pricing, FAQ, bundles
8. Full Services + Bundles pricing architecture
9. PDF tariff comparison sheets (CI-branded)
10. Legal compliance (AGB, Datenschutz, KI-Hinweise, Impressum) — trilingual
11. Trust section with operational security visibility
12. AI advisor with full product matrix mapping

## Architecture
```
/app/
├── backend/
│   ├── server.py (FastAPI, MongoDB, JWT, LLM, Security Headers, Chat)
│   ├── commercial.py (Quotes, Invoices, PDF generation, Revolut, Tariff Sheets)
│   └── .env (MONGO_URL, Revolut keys, Resend key, LLM key)
├── frontend/
│   ├── src/
│   │   ├── App.js (Landing page, Integrations, Pricing, SEO, Services, Trust, FAQ, Contact)
│   │   ├── App.css (Full design system)
│   │   ├── data/integrations.js (Integration categories + featured data)
│   │   ├── data/products.js (SEO product, Full Services, Bundles)
│   │   ├── i18n/ (LanguageContext.js, translations.js)
│   │   ├── components/ (LanguageSwitcher, SEOHead, Scene3D)
│   │   └── pages/ (Admin.js, LegalPages.js, QuotePortal.js, IntegrationDetail.js)
```

## What's Been Implemented
### Phase 1 (Previous forks)
- FastAPI backend with MongoDB, JWT auth, security headers
- Commercial engine (quotes, invoices, PDF generation via reportlab)
- Revolut Merchant API integration (production keys)
- Magic Link / Quote Portal
- Chat Discovery Flow with LLM
- Admin Dashboard
- 3D landing page with multi-language support
- EU Compliance Trust UI

### Phase 2 (Current session — April 2, 2026)
- **BLOCK 1**: Integrations UI Overhaul — premium categorized layout (12 categories, 100+ systems, popular grid, category cards, CTAs)
- **BLOCK 2**: SEO Landing Pages — /integrationen/:slug for Salesforce, HubSpot, SAP, DATEV, Slack, AWS, Shopify, OpenAI, Stripe (with use cases, FAQ, process, combined-with, CTA)
- **BLOCK 3**: KI-gesteuertes SEO as standalone product (benefits, process, 3 pricing tiers, FAQ, bundle integration)
- **BLOCK 4**: Full Services pricing (Websites 3 tiers, Apps 2 tiers, SEO 3 tiers, AI Agents 2 tiers, Add-ons 2)
- **BLOCK 5**: Bundles & Cross-sell (Digital Starter 3.990 EUR, Growth Digital 17.490 EUR, Enterprise Digital ab 39.900 EUR)
- **BLOCK 6**: PDF Tariff Comparison Sheets (CI-branded, per category or all, via /api/product/tariff-sheet)
- **BLOCK 7**: Legal updates (Privacy/AGB updated with Revolut, Magic Links, quote/invoice sections in all 3 languages)
- **BLOCK 8**: Trust section with operational security cards (Magic Links, Audit Trail, Data Lifecycle, RBAC)
- **BLOCK 9**: AI advisor system prompt updated with full product matrix, SEO products, bundle logic, cross-sell triggers

## Testing Status
- Iteration 16: 100% (23/23 backend, all frontend UI verified)
- Previous iterations 13-15: 100% (65/65 tests)

## Key Endpoints
- POST /api/commercial/quote — Create quote
- GET /api/commercial/portal/{token} — Magic Link portal
- GET /api/product/tariff-sheet?category=all|agents|websites|seo|bundles — PDF download
- GET /api/product/tariffs — Tariff data
- GET /api/product/services — Services catalog
- GET /api/product/compliance — Compliance status
- POST /api/chat — AI advisor

## 3rd Party Integrations
- Resend (Email) — User API key
- Emergent LLM Key (Chat) — Universal key
- Revolut Merchant API (Payments) — Production keys in .env

## Prioritized Backlog
### P0 (Done)
- All blocks 1-9 completed and tested

### P1 (Remaining)
- Resend live API key activation (currently placeholder)
- App.js refactoring (>1000 lines → split into components)
- Dunning logic for overdue invoices
- Admin CSV export for quotes/invoices
- Subscription API for recurring billing

### P2 (Future)
- A/B testing for CTA variants
- Customer dashboard beyond quote portal
- Multi-tenant support
- API documentation (Swagger/OpenAPI)
- Performance optimization (lazy loading, code splitting)
