# Test Credentials

## Admin Account
- Email: p.courbois@icloud.com
- Password: 1def!xO2022!!
- Login URL: /login
- Login Flow: 2-step (email → Weiter → password → Anmelden)
- API Login: POST /api/admin/login (form-urlencoded: username, password)

## Test API Endpoints (require Bearer token)
- GET /api/admin/stats
- GET /api/admin/leads
- GET /api/admin/bookings
- GET /api/admin/quotes
- GET /api/admin/invoices
- GET /api/admin/billing/overview
- GET /api/admin/billing/status/{email}
- GET /api/admin/outbound/campaigns
- GET /api/admin/monitoring/health
- GET /api/admin/monitoring/workers
- GET /api/admin/memory/stats
- GET /api/admin/oracle/snapshot
- GET /api/admin/oracle/contact/{email}
- GET /api/admin/workers/status
- POST /api/admin/llm/test
- POST /api/admin/llm/test-agent-flow
