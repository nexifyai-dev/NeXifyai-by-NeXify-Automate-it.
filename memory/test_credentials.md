# Test Credentials

## Admin
- Email: p.courbois@icloud.com
- Password: NxAi#Secure2026!
- Login: POST /api/admin/login (form-data: username + password)

## Customer Portal
- Customer auth via Magic Link: POST /api/admin/customers/portal-access → extract token from portal_url → POST /api/auth/verify-token → JWT
- Test customer: max@testfirma.de

## LLM Provider
- Active: Emergent GPT (Fallback)
- Target: DeepSeek (DEEPSEEK_API_KEY not set)
- Test: POST /api/admin/llm/test, POST /api/admin/llm/test-agent-flow
