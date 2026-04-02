# NeXifyAI Test Credentials

## Admin Account
- **Email**: p.courbois@icloud.com
- **Password**: NxAi#Secure2026!
- **Login Endpoint**: POST /api/admin/login (form-urlencoded: username=email&password=pw)
- **Returns**: JWT access_token

## API Base URL
- Preview: https://ai-architecture-lab.preview.emergentagent.com

## Routes
- Landing: /de (or /nl, /en)
- Admin: /admin
- Customer Offer Portal: /angebot?token={magic_link_token}&qid={quote_id}
- Datenschutz: /datenschutz
- Impressum: /impressum
- AGB: /agb

## Database Collections
leads, bookings, blocked_slots, inquiries, chat_sessions, admin_users, analytics,
quotes, invoices, documents, access_links, audit_log, webhook_events, commercial_events, counters

## Test Data
- Quote IDs in DB: q_47e524121e72a4cd (starter), q_1dc26ab66b817ae1 (growth)
