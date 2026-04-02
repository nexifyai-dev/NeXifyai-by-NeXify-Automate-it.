# NeXifyAI Test Credentials

## Admin CRM Dashboard
- URL: /admin
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!
- Auth: JWT via POST /api/admin/login (form-urlencoded: username, password)

## Backend API
- Health: GET /api/health
- Admin login: POST /api/admin/login (Content-Type: application/x-www-form-urlencoded)
- Curl example: `curl -X POST http://localhost:8001/api/admin/login -d "username=p.courbois@icloud.com&password=NxAi%23Secure2026%21"`

## Email Notifications
- Internal: support@nexify-automate.com, nexifyai@nexifyai.de
- Sender: noreply@send.nexify-automate.com (via Resend)

## Environment
- Backend: http://localhost:8001
- Frontend: http://localhost:3000 (proxy to backend for /api/*)
- MongoDB: mongodb://localhost:27017 (DB: nexifyai)
