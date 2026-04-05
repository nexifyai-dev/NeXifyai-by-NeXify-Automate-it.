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
- Dashboard: GET /api/admin/stats
- Oracle Dashboard: GET /api/admin/oracle/dashboard
- Oracle Health: GET /api/admin/oracle/health
- Oracle Agents: GET /api/admin/oracle/agents
- Oracle Brain Search: GET /api/admin/oracle/brain?q=query
- Oracle Tasks: GET /api/admin/oracle/tasks
- Oracle Create Task: POST /api/admin/oracle/tasks
- Oracle Invoke Agent: POST /api/admin/oracle/invoke-agent
- NeXify AI Chat: POST /api/admin/nexify-ai/chat
- Contacts: GET /api/admin/contacts
- Leads: GET /api/admin/leads
- Contracts: GET /api/admin/contracts
