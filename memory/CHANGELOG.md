# NeXifyAI — Changelog

## 2026-04-04

### P0 Rechtstexte — Verifizierung (Iteration 62)
- Verified all 21 legal page routes (7 documents x 3 languages: DE/NL/EN)
- Footer shows all 7 legal links correctly
- Language switcher works on legal pages
- Legacy redirects (/impressum -> /de/impressum) functional
- Invalid slug redirects to homepage

### P1 Content & Copywriting Overhaul (Iteration 63)
- **BUGFIX**: TrustSection i18n — was always showing German text regardless of language setting
  - Root cause: Used `t.lang` which was `undefined` (the `t` translations object has no `.lang` property)
  - Fix: Refactored TrustSection.js to use `useLanguage()` hook directly, with structured T translation object
  - Removed `t` prop from TrustSection in App.js
- Enhanced TrustSection copy in all 3 languages (deeper descriptions for security features, GDPR references, OWASP standards)
- All 14 sections render correctly across DE/NL/EN

## 2026-04-03

### Admin Sidebar Harmonization (Iteration 60)
- Admin sidebar collapsed by default with CSS hover tooltips (::after)
- Customer Portal sidebar follows same pattern (Iteration 61)

### Customer Portal Active Features (Iteration 61)
- Added backend APIs for requests, bookings, messages, support tickets
- Full CRUD UI forms in Customer Portal
- Quote/Contract workflows functional

### Comprehensive Legal Texts Implementation
- LegalPages.js with 7 legal documents (Impressum, Datenschutz, AGB, KI-Hinweise, Widerruf, Cookies, AVV)
- Full translations for DE/NL/EN with proper URL slugs per language
- Footer updated with all 7 legal links
- LEGAL_PATHS in shared/index.js updated
