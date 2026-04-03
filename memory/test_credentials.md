# NeXifyAI Test Credentials

## Admin Panel
- URL: /admin
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!

## Test Quote IDs
- Starter: q_47e524121e72a4cd
- Growth: q_1dc26ab66b817ae1
- Test Portal: q_ba44f4dcd380223d

## Test Customer
- Email: max@testfirma.de
- Unternehmen: Testfirma GmbH
- Contact ID: ct_6df55ae162a34cd3

## API Base URL
- https://ai-architecture-lab.preview.emergentagent.com

## Auth Flow
- Login: POST /api/admin/login (form-data: username=email, password=password)
- Returns: { access_token, token_type: "bearer" }
- Use: Authorization: Bearer {access_token}
