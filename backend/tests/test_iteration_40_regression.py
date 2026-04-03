"""
NeXifyAI Iteration 40 — Modular Architecture Regression Test
Tests all routes after server.py monolith refactoring (6530 lines → 10 route modules)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin and return JWT token."""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Return headers with Bearer token."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestPublicRoutes:
    """Public routes (no auth required) - routes/public_routes.py"""

    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "version" in data
        print(f"✓ Health: {data}")

    def test_company_endpoint(self):
        """GET /api/company returns company data"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "NeXify" in data.get("name", "")
        print(f"✓ Company: {data.get('name')}")

    def test_product_tariffs(self):
        """GET /api/product/tariffs returns starter,growth"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        assert response.status_code == 200
        data = response.json()
        tariffs = data.get("tariffs", {})
        assert "starter" in tariffs or len(tariffs) > 0
        print(f"✓ Tariffs: {list(tariffs.keys())}")

    def test_product_faq(self):
        """GET /api/product/faq"""
        response = requests.get(f"{BASE_URL}/api/product/faq")
        assert response.status_code == 200
        data = response.json()
        assert "faq" in data
        print(f"✓ FAQ: {len(data.get('faq', []))} items")

    def test_product_services(self):
        """GET /api/product/services"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data or "bundles" in data
        print(f"✓ Services: {len(data.get('services', {}))} services, {len(data.get('bundles', {}))} bundles")

    def test_booking_slots(self):
        """GET /api/booking/slots?date=2026-04-10"""
        response = requests.get(f"{BASE_URL}/api/booking/slots", params={"date": "2026-04-10"})
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"✓ Booking slots: {len(data.get('slots', []))} available")

    def test_contact_form(self):
        """POST /api/contact with valid data"""
        payload = {
            "vorname": "Test",
            "nachname": "Regression",
            "email": "test_regression_iter40@example.com",
            "nachricht": "This is a regression test message for iteration 40 modular refactoring.",
            "consent": True,
            "datenschutz_akzeptiert": True
        }
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Contact form: lead_id={data.get('lead_id')}")


class TestAuthRoutes:
    """Auth routes - routes/auth_routes.py"""

    def test_admin_login(self):
        """POST /api/admin/login with admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
        print(f"✓ Admin login: token received")

    def test_admin_me(self, auth_headers):
        """GET /api/admin/me with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_EMAIL
        print(f"✓ Admin me: {data.get('email')}")


class TestAdminRoutes:
    """Admin CRM routes - routes/admin_routes.py"""

    def test_admin_stats(self, auth_headers):
        """GET /api/admin/stats with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        print(f"✓ Admin stats: {data.get('total_leads')} leads")

    def test_admin_leads(self, auth_headers):
        """GET /api/admin/leads with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        print(f"✓ Admin leads: {data.get('total')} total")

    def test_admin_bookings(self, auth_headers):
        """GET /api/admin/bookings with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        print(f"✓ Admin bookings: {data.get('total', len(data.get('bookings', [])))} total")

    def test_admin_calendar_data(self, auth_headers):
        """GET /api/admin/calendar-data with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/calendar-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "month" in data
        print(f"✓ Calendar data: month={data.get('month')}")


class TestBillingRoutes:
    """Billing routes - routes/billing_routes.py"""

    def test_admin_quotes(self, auth_headers):
        """GET /api/admin/quotes with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/quotes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        print(f"✓ Admin quotes: {len(data.get('quotes', []))} quotes")

    def test_admin_invoices(self, auth_headers):
        """GET /api/admin/invoices with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        print(f"✓ Admin invoices: {len(data.get('invoices', []))} invoices")

    def test_admin_billing_status(self, auth_headers):
        """GET /api/admin/billing/status with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/billing/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data or "invoices" in data
        print(f"✓ Billing status: {data}")

    def test_admin_email_stats(self, auth_headers):
        """GET /api/admin/email/stats with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/email/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        print(f"✓ Email stats: {data.get('total')} total, {data.get('sent')} sent")


class TestContractRoutes:
    """Contract routes - routes/contract_routes.py"""

    def test_admin_contracts(self, auth_headers):
        """GET /api/admin/contracts with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/contracts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "contracts" in data
        print(f"✓ Admin contracts: {data.get('total', len(data.get('contracts', [])))} contracts")


class TestProjectRoutes:
    """Project routes - routes/project_routes.py"""

    def test_admin_projects(self, auth_headers):
        """GET /api/admin/projects with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"✓ Admin projects: {data.get('total', len(data.get('projects', [])))} projects")


class TestOutboundRoutes:
    """Outbound routes - routes/outbound_routes.py"""

    def test_admin_outbound_pipeline(self, auth_headers):
        """GET /api/admin/outbound/pipeline with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/outbound/pipeline", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pipeline" in data
        print(f"✓ Outbound pipeline: {data.get('total', 0)} leads")


class TestCommsRoutes:
    """Communications routes - routes/comms_routes.py"""

    def test_admin_conversations(self, auth_headers):
        """GET /api/admin/conversations with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        print(f"✓ Admin conversations: {len(data.get('conversations', []))} conversations")


class TestMonitoringRoutes:
    """Monitoring routes - routes/monitoring_routes.py"""

    def test_admin_monitoring_status(self, auth_headers):
        """GET /api/admin/monitoring/status with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "systems" in data
        assert "overall_status" in data
        print(f"✓ Monitoring status: {data.get('overall_status')}")

    def test_admin_workers_status(self, auth_headers):
        """GET /api/admin/workers/status with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/workers/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Workers status: {data}")

    def test_admin_agents(self, auth_headers):
        """GET /api/admin/agents with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/agents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"✓ Agents: {list(data.get('agents', {}).keys())}")

    def test_admin_llm_status(self, auth_headers):
        """GET /api/admin/llm/status with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/llm/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "active_provider" in data
        print(f"✓ LLM status: {data.get('active_provider')}")

    def test_admin_audit_health(self, auth_headers):
        """GET /api/admin/audit/health with auth"""
        response = requests.get(f"{BASE_URL}/api/admin/audit/health", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "checks" in data
        print(f"✓ Audit health: {data.get('overall')}")


class TestE2EVerification:
    """End-to-end verification of modular architecture"""

    def test_e2e_verify_flow(self, auth_headers):
        """POST /api/admin/e2e/verify-flow"""
        response = requests.post(f"{BASE_URL}/api/admin/e2e/verify-flow", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "e2e_verification" in data
        print(f"✓ E2E verify: {data.get('passed')}/{data.get('total_checks')} passed ({data.get('pass_rate')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
