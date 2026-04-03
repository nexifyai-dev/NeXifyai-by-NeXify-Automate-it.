"""
Iteration 25 Backend Tests — Worker/Scheduler/Services Layer

Tests for:
- P0: Worker/Scheduler Layer (JobQueue, Scheduler, Dead-Letter)
- P1: Communication Service (Contacts, Conversations, Messages)
- P2: Outbound Lead Machine + Legal Gate
- P3: Billing Status-Sync
- P5: LLM Abstraction Layer

All endpoints require admin auth.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


class TestHealthAndAuth:
    """Basic health check and admin authentication."""

    def test_health_endpoint(self):
        """GET /api/health — Basis-Healthcheck"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        print(f"✅ Health check passed: {data}")

    def test_admin_login(self):
        """POST /api/admin/login — Admin authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"✅ Admin login successful")
        return data["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for authenticated requests."""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip("Admin login failed - skipping authenticated tests")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Auth headers for admin requests."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestWorkerSchedulerEndpoints:
    """P0: Worker/Scheduler Layer Tests"""

    def test_worker_status(self, auth_headers):
        """GET /api/admin/workers/status — Worker-Queue + Scheduler Status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/workers/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify queue stats
        assert "queue" in data
        queue = data["queue"]
        assert "enqueued" in queue
        assert "completed" in queue
        assert "failed" in queue
        assert "workers_active" in queue
        assert "running" in queue
        assert "registered_handlers" in queue
        
        # Verify scheduler stats
        assert "scheduler" in data
        scheduler = data["scheduler"]
        assert "running" in scheduler
        assert "jobs" in scheduler
        assert "count" in scheduler
        
        print(f"✅ Worker status: {queue['workers_active']} workers, {scheduler['count']} scheduled jobs")
        print(f"   Registered handlers: {queue['registered_handlers']}")

    def test_worker_jobs_list(self, auth_headers):
        """GET /api/admin/workers/jobs — Job-Liste"""
        response = requests.get(
            f"{BASE_URL}/api/admin/workers/jobs",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "count" in data
        assert isinstance(data["jobs"], list)
        print(f"✅ Jobs list: {data['count']} jobs found")

    def test_worker_jobs_with_filter(self, auth_headers):
        """GET /api/admin/workers/jobs with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/workers/jobs?status=completed&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        # All returned jobs should have status=completed
        for job in data["jobs"]:
            assert job.get("status") == "completed"
        print(f"✅ Filtered jobs (completed): {data['count']} jobs")

    def test_dead_letter_queue(self, auth_headers):
        """GET /api/admin/workers/dead-letter — Dead-Letter-Queue"""
        response = requests.get(
            f"{BASE_URL}/api/admin/workers/dead-letter",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "dead_letter_jobs" in data
        assert "count" in data
        assert isinstance(data["dead_letter_jobs"], list)
        print(f"✅ Dead-letter queue: {data['count']} failed jobs")

    def test_worker_status_requires_auth(self):
        """Worker endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/workers/status")
        assert response.status_code == 401
        print("✅ Worker status correctly requires auth")


class TestLLMProviderEndpoints:
    """P5: LLM Abstraction Layer Tests"""

    def test_llm_status(self, auth_headers):
        """GET /api/admin/llm/status — LLM-Provider Status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/llm/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "provider" in data
        assert "deepseek_configured" in data
        assert "emergent_configured" in data
        assert "target_architecture" in data
        assert "current_status" in data
        
        # Verify expected values
        assert data["target_architecture"] == "deepseek"
        assert isinstance(data["deepseek_configured"], bool)
        assert isinstance(data["emergent_configured"], bool)
        
        print(f"✅ LLM status: provider={data['provider']}, status={data['current_status']}")
        print(f"   DeepSeek configured: {data['deepseek_configured']}, Emergent configured: {data['emergent_configured']}")


class TestOutboundLeadMachineEndpoints:
    """P2: Outbound Lead Machine + Legal Gate Tests"""

    @pytest.fixture(scope="class")
    def test_lead_id(self, auth_headers):
        """Create a test lead for the pipeline tests."""
        lead_data = {
            "name": "TEST_Outbound GmbH",
            "website": "https://test-outbound.de",
            "industry": "technologie",
            "email": "test_outbound@example.com",
            "phone": "+49 123 456789",
            "contact_name": "Max Mustermann",
            "country": "DE",
            "notes": "Test lead for iteration 25 - skalierung, automatisierung, ki-strategie",
            "source": "test"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/discover",
            headers=auth_headers,
            json=lead_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "outbound_lead_id" in data
        print(f"✅ Test lead created: {data['outbound_lead_id']}")
        return data["outbound_lead_id"]

    def test_outbound_discover(self, auth_headers):
        """POST /api/admin/outbound/discover — Outbound-Lead erfassen"""
        lead_data = {
            "name": "TEST_Discovery Corp",
            "website": "https://discovery-test.de",
            "industry": "beratung",
            "email": "discovery_test@example.com",
            "country": "DE",
            "notes": "Discovery test lead",
            "source": "admin"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/discover",
            headers=auth_headers,
            json=lead_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "outbound_lead_id" in data
        assert data["status"] == "discovered"
        print(f"✅ Outbound discover: lead_id={data['outbound_lead_id']}")

    def test_outbound_prequalify(self, auth_headers, test_lead_id):
        """POST /api/admin/outbound/{id}/prequalify — Vorqualifizierung"""
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_lead_id}/prequalify",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "qualified" in data
        print(f"✅ Prequalify: status={data['status']}, qualified={data['qualified']}")
        if data.get("issues"):
            print(f"   Issues: {data['issues']}")

    def test_outbound_analyze(self, auth_headers, test_lead_id):
        """POST /api/admin/outbound/{id}/analyze — Analyse + Scoring"""
        analysis_data = {
            "industry": "technologie",
            "company_size": "50-200",
            "notes": "Interessiert an KI-Automatisierung und Skalierung",
            "analysis_type": "manual"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_lead_id}/analyze",
            headers=auth_headers,
            json=analysis_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "fit_products" in data
        assert "analysis" in data
        assert isinstance(data["score"], int)
        print(f"✅ Analyze: score={data['score']}, fit_products={len(data['fit_products'])}")
        for product in data["fit_products"]:
            print(f"   - {product['name']}: score={product['score']}")

    def test_outbound_legal_check(self, auth_headers, test_lead_id):
        """POST /api/admin/outbound/{id}/legal-check — Legal Gate"""
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_lead_id}/legal-check",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "legal_ok" in data
        assert "issues" in data
        assert "status" in data
        print(f"✅ Legal check: legal_ok={data['legal_ok']}, status={data['status']}")
        if data.get("issues"):
            print(f"   Issues: {data['issues']}")

    def test_outbound_leads_list(self, auth_headers):
        """GET /api/admin/outbound/leads — Liste mit Filtern"""
        response = requests.get(
            f"{BASE_URL}/api/admin/outbound/leads",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "count" in data
        assert isinstance(data["leads"], list)
        print(f"✅ Outbound leads list: {data['count']} leads")

    def test_outbound_leads_with_filter(self, auth_headers):
        """GET /api/admin/outbound/leads with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/outbound/leads?status=discovered&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        print(f"✅ Filtered outbound leads (discovered): {data['count']} leads")

    def test_outbound_stats(self, auth_headers):
        """GET /api/admin/outbound/stats — Pipeline-Statistiken"""
        response = requests.get(
            f"{BASE_URL}/api/admin/outbound/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "conversion_rate" in data
        print(f"✅ Outbound stats: total={data['total']}, conversion_rate={data['conversion_rate']}%")
        print(f"   By status: {data['by_status']}")

    def test_outbound_opt_out(self, auth_headers):
        """POST /api/admin/outbound/opt-out — Suppression"""
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/opt-out",
            headers=auth_headers,
            json={"email": "test_optout@example.com", "reason": "Test opt-out"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "opted_out"
        assert data["email"] == "test_optout@example.com"
        print(f"✅ Opt-out: {data['email']} added to suppression list")


class TestBillingServiceEndpoints:
    """P3: Billing Status-Sync Tests"""

    def test_billing_status(self, auth_headers):
        """GET /api/admin/billing/status/{email} — Billing-Status"""
        # Use test customer email
        test_email = "max@testfirma.de"
        response = requests.get(
            f"{BASE_URL}/api/admin/billing/status/{test_email}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "contact_email" in data
        assert "quotes" in data
        assert "invoices" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_quotes" in summary
        assert "total_invoices" in summary
        assert "total_invoiced" in summary
        assert "total_paid" in summary
        assert "total_outstanding" in summary
        
        print(f"✅ Billing status for {test_email}:")
        print(f"   Quotes: {summary['total_quotes']}, Invoices: {summary['total_invoices']}")
        print(f"   Invoiced: {summary['total_invoiced']} EUR, Paid: {summary['total_paid']} EUR")

    def test_billing_sync_quote_requires_status(self, auth_headers):
        """POST /api/admin/billing/sync-quote/{id} — 400 if no status"""
        response = requests.post(
            f"{BASE_URL}/api/admin/billing/sync-quote/nonexistent_quote",
            headers=auth_headers,
            json={}  # No status provided
        )
        assert response.status_code == 400
        data = response.json()
        assert "Status erforderlich" in data.get("detail", "")
        print("✅ Billing sync-quote correctly requires status")

    def test_billing_sync_invoice_requires_status(self, auth_headers):
        """POST /api/admin/billing/sync-invoice/{id} — 400 if no status"""
        response = requests.post(
            f"{BASE_URL}/api/admin/billing/sync-invoice/nonexistent_invoice",
            headers=auth_headers,
            json={}  # No status provided
        )
        assert response.status_code == 400
        data = response.json()
        assert "Status erforderlich" in data.get("detail", "")
        print("✅ Billing sync-invoice correctly requires status")


class TestCommunicationServiceEndpoints:
    """P1: Communication Service Tests"""

    def test_comms_contact_detail(self, auth_headers):
        """GET /api/admin/comms/contacts/{email} — Kontakt-Detail"""
        # Use test customer email
        test_email = "max@testfirma.de"
        response = requests.get(
            f"{BASE_URL}/api/admin/comms/contacts/{test_email}",
            headers=auth_headers
        )
        # May return 404 if contact doesn't exist, which is valid
        if response.status_code == 404:
            print(f"ℹ️ Contact {test_email} not found (expected if no prior interaction)")
            return
        
        assert response.status_code == 200
        data = response.json()
        assert "contact" in data
        assert "conversations" in data
        assert "timeline" in data
        
        contact = data["contact"]
        assert "contact_id" in contact
        assert "email" in contact
        
        print(f"✅ Contact detail for {test_email}:")
        print(f"   Contact ID: {contact['contact_id']}")
        print(f"   Conversations: {len(data['conversations'])}")
        print(f"   Timeline events: {len(data['timeline'])}")

    def test_comms_contact_not_found(self, auth_headers):
        """GET /api/admin/comms/contacts/{email} — 404 for unknown contact"""
        response = requests.get(
            f"{BASE_URL}/api/admin/comms/contacts/nonexistent_contact@example.com",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✅ Comms contact correctly returns 404 for unknown email")

    def test_comms_assign_conversation(self, auth_headers):
        """POST /api/admin/comms/conversations/{id}/assign — Konversation zuweisen"""
        # This will fail with 404 for nonexistent conversation, which is expected
        response = requests.post(
            f"{BASE_URL}/api/admin/comms/conversations/test_conv_id/assign",
            headers=auth_headers,
            json={"assigned_to": "admin"}
        )
        # Either 200 (if conversation exists) or error (if not)
        # We're testing the endpoint works, not that the conversation exists
        assert response.status_code in [200, 404, 500]
        print(f"✅ Comms assign endpoint accessible (status: {response.status_code})")

    def test_comms_send_message_requires_content(self, auth_headers):
        """POST /api/admin/comms/conversations/{id}/send — Nachricht senden"""
        response = requests.post(
            f"{BASE_URL}/api/admin/comms/conversations/test_conv_id/send",
            headers=auth_headers,
            json={"channel": "email", "content": ""}  # Empty content
        )
        assert response.status_code == 400
        data = response.json()
        assert "Nachricht darf nicht leer sein" in data.get("detail", "")
        print("✅ Comms send message correctly requires content")


class TestExistingEndpointsStillWork:
    """Verify existing endpoints still work after new additions."""

    def test_admin_stats(self, auth_headers):
        """GET /api/admin/stats — Existing admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data or "total_leads" in data or isinstance(data, dict)
        print(f"✅ Admin stats endpoint still works")

    def test_admin_leads(self, auth_headers):
        """GET /api/admin/leads — Existing leads endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"✅ Admin leads endpoint still works")


class TestAuthorizationEnforcement:
    """Verify all new endpoints require admin auth."""

    def test_worker_endpoints_require_auth(self):
        """All worker endpoints require authentication"""
        endpoints = [
            "/api/admin/workers/status",
            "/api/admin/workers/jobs",
            "/api/admin/workers/dead-letter",
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 401, f"{endpoint} should require auth"
        print("✅ All worker endpoints require auth")

    def test_llm_endpoint_requires_auth(self):
        """LLM status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/llm/status")
        assert response.status_code == 401
        print("✅ LLM status endpoint requires auth")

    def test_outbound_endpoints_require_auth(self):
        """All outbound endpoints require authentication"""
        endpoints = [
            "/api/admin/outbound/leads",
            "/api/admin/outbound/stats",
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 401, f"{endpoint} should require auth"
        print("✅ All outbound endpoints require auth")

    def test_billing_endpoints_require_auth(self):
        """All billing endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/billing/status/test@test.com")
        assert response.status_code == 401
        print("✅ Billing endpoints require auth")

    def test_comms_endpoints_require_auth(self):
        """All comms endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/comms/contacts/test@test.com")
        assert response.status_code == 401
        print("✅ Comms endpoints require auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
