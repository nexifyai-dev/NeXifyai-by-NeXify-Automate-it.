# NeXifyAI Test Credentials

## Admin CRM Dashboard
- URL: /admin
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!
- Auth: JWT via POST /api/admin/login (form-urlencoded: username, password)
- Rate limit: 20 requests per 5 minutes

## Backend API
- Health: GET /api/health
- Admin login: POST /api/admin/login (Content-Type: application/x-www-form-urlencoded)
- Curl: `curl -X POST http://localhost:8001/api/admin/login -d "username=p.courbois@icloud.com&password=NxAi%23Secure2026%21"`
- Chat: POST /api/chat/message (JSON: {session_id, message}) — LLM-powered (GPT-4o-mini)

## Email Notifications
- Internal: support@nexify-automate.com, nexifyai@nexifyai.de
- Sender: noreply@send.nexify-automate.com (via Resend)

## Environment Keys
- EMERGENT_LLM_KEY: sk-emergent-4281cA643Cd0cE117F (in backend/.env)
- ADMIN_PASSWORD: NxAi#Secure2026! (in backend/.env)

## MongoDB
- URL: mongodb://localhost:27017
- DB: nexifyai
- Collections: leads, bookings, chat_sessions, admin_users, analytics
