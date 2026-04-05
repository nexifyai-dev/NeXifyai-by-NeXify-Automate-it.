# Test Credentials

## Admin Login
- Email: p.courbois@icloud.com
- Password: 1def!xO2022!!
- Login URL: /login
- Login Flow: Email → Weiter → Role Selection "Administration" → Password → Anmelden

## API Authentication
- POST /api/admin/login (form-encoded: username=email&password=pw)
- Returns: { access_token: "JWT..." }
- Use: Authorization: Bearer {token}

## Key API Endpoints
- Dashboard Stats: GET /api/admin/stats
- System Health: GET /api/admin/monitoring/health
- Customers: GET /api/admin/customers (NOT /contacts)
- Leads: GET /api/admin/leads
- Contracts: GET /api/admin/contracts
- Invoices: GET /api/admin/invoices
- Quotes: GET /api/admin/quotes
- Bookings: GET /api/admin/bookings

## Oracle System Endpoints
- Dashboard: GET /api/admin/oracle/dashboard
- Health: GET /api/admin/oracle/health
- Agents: GET /api/admin/oracle/agents
- Brain Search: GET /api/admin/oracle/brain?q=query
- Tasks: GET/POST /api/admin/oracle/tasks
- Engine Status: GET /api/admin/oracle/engine/status
- Engine Trigger: POST /api/admin/oracle/engine/trigger
- Font Audit: POST /api/admin/oracle/engine/font-audit
- Knowledge Sync: POST /api/admin/oracle/engine/sync-knowledge
- Invoke Agent: POST /api/admin/oracle/invoke-agent

## NeXify AI
- Chat (SSE): POST /api/admin/nexify-ai/chat
- Conversations: GET /api/admin/nexify-ai/conversations
- Status: GET /api/admin/nexify-ai/status
