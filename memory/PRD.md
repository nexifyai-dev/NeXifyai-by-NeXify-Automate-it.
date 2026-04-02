# NeXifyAI — Product Requirements Document

## Original Problem Statement
B2B-first commercial system "Starter/Growth AI Agenten AG" for NeXifyAI. Full-stack platform with React frontend, FastAPI backend, MongoDB. Multi-language (DE/NL/EN). Revolut Merchant API for payments. Enterprise-grade compliance (DSGVO, EU AI Act).

## Core Requirements (Static)
1. Landing page with 3D, multi-language, Trust/Compliance, Chat Discovery
2. Commercial Engine: Quotes, Invoices, PDF generation, Revolut payment
3. Magic Link customer portal for quote acceptance
4. Admin Dashboard for commercial management
5. Premium Integrations section (categorized, SEO-linked)
6. Dedicated SEO landing pages per integration (/integrationen/:slug)
7. KI-gesteuertes SEO as standalone product with pricing, FAQ, bundles
8. Full Services + Bundles pricing architecture
9. PDF tariff comparison sheets (CI-branded, per category)
10. Legal compliance (AGB, Datenschutz, KI-Hinweise) — trilingual
11. Trust section with operational security visibility
12. AI advisor with full product matrix mapping

## Central Tariff System
All products managed in `commercial.py`:
- TARIFF_CONFIG: KI-Agenten (2 tiers, 24 months, 30% deposit)
- SERVICE_CATALOG: 10 services (3 websites, 2 apps, 3 SEO, 2 add-ons)
- BUNDLE_CATALOG: 3 bundles (Digital Starter, Growth Digital, Enterprise Digital)
- PRODUCT_DESCRIPTIONS: 6 professional product descriptions

## API Endpoints
- GET /api/product/tariff-sheet?category=all|agents|websites|seo|apps|addons|bundles
- GET /api/product/descriptions
- GET /api/product/tariffs
- GET /api/product/services
- POST /api/commercial/quote
- GET /api/commercial/portal/{token}
- POST /api/chat

## Testing Status
- Iteration 16: 100% (23/23 automated tests)
- Iteration 17: All APIs verified (7 PDF categories, descriptions, services, frontend routes)

## Prioritized Backlog
### P0 (Done)
All blocks completed: UI fixes, central tariff system, product descriptions, legal, PDF sheets, trust, KI-advisor

### P1 (Remaining)
- Resend live API key activation
- App.js refactoring (>1000 lines)
- Dunning logic for overdue invoices
- Admin CSV export
- Subscription API

### P2 (Future)
- A/B testing CTAs
- Customer dashboard beyond portal
- Multi-tenant support
- API documentation
