# NeXifyAI Test Credentials

## Admin Panel
- URL: /admin (oder /login → Admin-Flow)
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!

## Test Customer
- Email: max@testfirma.de
- Unternehmen: Testfirma GmbH
- Contact ID: ct_6df55ae162a34cd3
- Portal: /login → Magic Link Flow

## Unified Login
- URL: /login
- Admin: E-Mail → Passwort-Feld → Anmelden → /admin
- Kunde: E-Mail → Magic Link per E-Mail → /login/verify?token=xxx → /portal

## Auth Flow
- Admin Login: POST /api/admin/login (form-data) → {access_token, role:admin}
- Customer Login: POST /api/auth/verify-token → {access_token, role:customer}
- Role Check: POST /api/auth/check-email → {role: admin|customer|unknown}

## API Base URL
- https://ai-architecture-lab.preview.emergentagent.com
