# Test Credentials

## Admin Login
- **Email**: p.courbois@icloud.com
- **Password**: 1def!xO2022!!
- **Login Flow**: 2-Step (Email → "Weiter" → "Administration" → Password → "Anmelden")
- **Login Endpoint**: POST /api/admin/login (form-urlencoded: username, password)
- **Auth Header**: Authorization: Bearer {access_token}

## App URLs
- **Frontend**: https://contract-os.preview.emergentagent.com
- **Admin Panel**: https://contract-os.preview.emergentagent.com/admin

## Key API Endpoints
- GET /api/admin/stats
- GET /api/admin/oracle/leitstelle
- GET /api/admin/oracle/dashboard
- GET /api/admin/service-templates
- POST /api/admin/service-templates/instantiate
- POST /api/admin/nexify-ai/chat
- GET /api/admin/nexify-ai/conversations
- GET /api/admin/nexify-ai/status
