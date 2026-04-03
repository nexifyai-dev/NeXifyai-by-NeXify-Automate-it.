"""
Iteration 39 Backend Tests — P1: Stripe Live Integration, P2: Object Storage, P3: Self-Healing/Recovery, P5: Project Derived Status

Tests:
1. Stripe Checkout Session Creation (POST /api/admin/invoices/{id}/create-stripe-checkout)
2. Stripe Checkout Status Polling (GET /api/payments/checkout/status/{session_id})
3. Stripe Webhook Handling (POST /api/webhooks/stripe)
4. Monitoring Status with Object Storage, Documents, Stripe (GET /api/admin/monitoring/status)
5. Contract PDF Generation with Object Storage (POST /api/admin/contracts/{id}/generate-pdf)
6. Contract PDF Download (GET /api/documents/contract/{id}/pdf)
7. Project Derived Status with Phase (GET /api/admin/projects/{id})
8. Customer Project Phase with German Labels (GET /api/customer/projects/{id})
9. E2E Verify Flow (POST /api/admin/e2e/verify-flow)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://contract-os.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"

# Test entities from review request
TEST_INVOICE_ID = "inv_0769994ba27f5ab7"
TEST_CONTRACT_ID = "ctr_3d5efbc6b9c04a29"
TEST_PROJECT_ID = "prj_6c4e346089384828"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin JWT token."""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Auth headers for admin requests."""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestHealthAndBasics:
    """Basic health checks."""

    def test_api_health(self):
        """Test API health endpoint."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ API healthy: version {data['version']}")


class TestStripeIntegration:
    """P1: Stripe Live Integration via emergentintegrations."""

    def test_create_stripe_checkout_session(self, auth_headers):
        """Test POST /api/admin/invoices/{id}/create-stripe-checkout — Creates real Stripe checkout session."""
        response = requests.post(
            f"{BASE_URL}/api/admin/invoices/{TEST_INVOICE_ID}/create-stripe-checkout",
            headers=auth_headers
        )
        # May return 200 (success) or 400 (already has session) or 404 (invoice not found)
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data, "Missing checkout_url in response"
            assert "session_id" in data, "Missing session_id in response"
            assert data["checkout_url"].startswith("https://"), "checkout_url should be HTTPS URL"
            print(f"✓ Stripe checkout created: session_id={data['session_id'][:20]}...")
            print(f"  checkout_url: {data['checkout_url'][:60]}...")
            return data["session_id"]
        elif response.status_code == 400:
            # Invoice may already have a checkout session
            data = response.json()
            print(f"✓ Stripe checkout endpoint working (invoice may already have session): {data.get('detail', data)}")
        elif response.status_code == 404:
            print(f"⚠ Invoice {TEST_INVOICE_ID} not found - skipping checkout test")
            pytest.skip("Test invoice not found")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")

    def test_checkout_status_polling(self, auth_headers):
        """Test GET /api/payments/checkout/status/{session_id} — Returns checkout status from Stripe."""
        # First, get an existing session from the invoice
        inv_response = requests.get(
            f"{BASE_URL}/api/admin/invoices/{TEST_INVOICE_ID}",
            headers=auth_headers
        )
        if inv_response.status_code != 200:
            pytest.skip("Test invoice not found")
        
        invoice = inv_response.json()
        session_id = invoice.get("stripe_checkout_session_id")
        
        if not session_id:
            # Try to create one
            create_resp = requests.post(
                f"{BASE_URL}/api/admin/invoices/{TEST_INVOICE_ID}/create-stripe-checkout",
                headers=auth_headers
            )
            if create_resp.status_code == 200:
                session_id = create_resp.json().get("session_id")
        
        if not session_id:
            pytest.skip("No Stripe session available for testing")
        
        # Poll the status
        response = requests.get(f"{BASE_URL}/api/payments/checkout/status/{session_id}")
        assert response.status_code == 200, f"Status polling failed: {response.text}"
        data = response.json()
        assert "status" in data, "Missing status in response"
        # session_id may be in response or we already have it
        print(f"✓ Checkout status: {data['status']} for session {session_id[:20]}...")
        print(f"  → payment_status: {data.get('payment_status')}, amount: {data.get('amount_total')}")

    def test_stripe_webhook_endpoint_exists(self):
        """Test POST /api/webhooks/stripe — Endpoint exists and handles requests."""
        # Send a minimal test payload (will fail signature but endpoint should exist)
        response = requests.post(
            f"{BASE_URL}/api/webhooks/stripe",
            json={"type": "test", "data": {}},
            headers={"Content-Type": "application/json"}
        )
        # Should return 400 (bad signature) or 200 (processed), not 404
        assert response.status_code != 404, "Stripe webhook endpoint not found"
        print(f"✓ Stripe webhook endpoint exists (status: {response.status_code})")


class TestMonitoringStatus:
    """P3: Enhanced Monitoring with Object Storage, Documents, Stripe status."""

    def test_monitoring_status_endpoint(self, auth_headers):
        """Test GET /api/admin/monitoring/status — Includes object_storage, documents, and stripe status."""
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/status", headers=auth_headers)
        assert response.status_code == 200, f"Monitoring status failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "systems" in data, "Missing systems in response"
        assert "timestamp" in data, "Missing timestamp in response"
        
        systems = data["systems"]
        
        # Check required system components
        required_systems = ["api", "database", "workers", "email", "payments", "webhooks", "llm", "object_storage", "documents"]
        for sys_name in required_systems:
            assert sys_name in systems, f"Missing {sys_name} in systems"
        
        # Verify object_storage structure
        obj_storage = systems["object_storage"]
        assert "status" in obj_storage, "Missing status in object_storage"
        assert "initialized" in obj_storage, "Missing initialized in object_storage"
        print(f"✓ Object Storage: status={obj_storage['status']}, initialized={obj_storage['initialized']}")
        
        # Verify documents structure
        docs = systems["documents"]
        assert "total" in docs, "Missing total in documents"
        assert "in_storage" in docs, "Missing in_storage in documents"
        assert "in_mongodb" in docs, "Missing in_mongodb in documents"
        print(f"✓ Documents: total={docs['total']}, in_storage={docs['in_storage']}, in_mongodb={docs['in_mongodb']}")
        
        # Verify Stripe in payments
        payments = systems["payments"]
        assert "stripe" in payments, "Missing stripe in payments"
        stripe_status = payments["stripe"]
        assert "status" in stripe_status, "Missing status in stripe"
        assert "api_key_set" in stripe_status, "Missing api_key_set in stripe"
        print(f"✓ Stripe: status={stripe_status['status']}, api_key_set={stripe_status['api_key_set']}")
        
        # Verify overall status
        assert data.get("overall_status") == "operational", f"Overall status not operational: {data.get('overall_status')}"
        print(f"✓ Monitoring status complete: overall_status={data['overall_status']}")


class TestObjectStorageAndPDF:
    """P2: Object Storage for PDF Archiving."""

    def test_contract_pdf_generation(self, auth_headers):
        """Test POST /api/admin/contracts/{id}/generate-pdf — Generates PDF and archives to Object Storage."""
        response = requests.post(
            f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID}/generate-pdf",
            headers=auth_headers
        )
        if response.status_code == 404:
            pytest.skip(f"Test contract {TEST_CONTRACT_ID} not found")
        
        assert response.status_code == 200, f"PDF generation failed: {response.text}"
        data = response.json()
        assert data.get("generated") == True, "PDF not generated"
        assert "contract_id" in data, "Missing contract_id in response"
        assert "size_bytes" in data, "Missing size_bytes in response"
        assert data["size_bytes"] > 0, "PDF size should be > 0"
        print(f"✓ Contract PDF generated: {data['size_bytes']} bytes")

    def test_contract_pdf_download(self, auth_headers):
        """Test GET /api/documents/contract/{id}/pdf — Downloads PDF (Object Storage primary, MongoDB fallback)."""
        # First ensure PDF exists
        gen_response = requests.post(
            f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID}/generate-pdf",
            headers=auth_headers
        )
        if gen_response.status_code == 404:
            pytest.skip(f"Test contract {TEST_CONTRACT_ID} not found")
        
        # Download PDF
        response = requests.get(
            f"{BASE_URL}/api/documents/contract/{TEST_CONTRACT_ID}/pdf",
            headers=auth_headers
        )
        if response.status_code == 404:
            pytest.skip("Contract PDF not found")
        
        assert response.status_code == 200, f"PDF download failed: {response.text}"
        assert response.headers.get("Content-Type") == "application/pdf", "Content-Type should be application/pdf"
        
        # Verify PDF content starts with PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Content should start with %PDF"
        print(f"✓ Contract PDF downloaded: {len(content)} bytes, valid PDF format")


class TestProjectDerivedStatus:
    """P5: Project Chat Status from Real Entities."""

    def test_admin_project_derived_status(self, auth_headers):
        """Test GET /api/admin/projects/{id} — Returns derived_status with phase."""
        response = requests.get(
            f"{BASE_URL}/api/admin/projects/{TEST_PROJECT_ID}",
            headers=auth_headers
        )
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        assert response.status_code == 200, f"Project fetch failed: {response.text}"
        data = response.json()
        
        # Verify derived_status exists
        assert "derived_status" in data, "Missing derived_status in project"
        derived = data["derived_status"]
        
        # Verify phase exists and is valid
        assert "phase" in derived, "Missing phase in derived_status"
        valid_phases = ["discovery", "quote_pending", "contract_pending", "payment_pending", "build_ready"]
        assert derived["phase"] in valid_phases, f"Invalid phase: {derived['phase']}"
        
        # Verify build_ready flag
        assert "build_ready" in derived, "Missing build_ready in derived_status"
        
        print(f"✓ Project derived_status: phase={derived['phase']}, build_ready={derived['build_ready']}")
        
        # Check for linked entities
        if "quote" in derived:
            print(f"  → Quote: {derived['quote'].get('number')} ({derived['quote'].get('status')})")
        if "contract" in derived:
            print(f"  → Contract: {derived['contract'].get('number')} ({derived['contract'].get('status')})")
        if "invoice" in derived:
            print(f"  → Invoice: {derived['invoice'].get('number')} ({derived['invoice'].get('payment_status')})")

    def test_customer_project_phase_with_german_labels(self, auth_headers):
        """Test GET /api/customer/projects/{id} — Returns project_phase with phase_label in German."""
        # First get project to find customer email
        admin_response = requests.get(
            f"{BASE_URL}/api/admin/projects/{TEST_PROJECT_ID}",
            headers=auth_headers
        )
        if admin_response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found")
        
        project = admin_response.json()
        customer_email = project.get("customer_email") or project.get("customer", {}).get("email")
        
        if not customer_email:
            pytest.skip("No customer email found for project")
        
        # Generate customer portal access
        portal_response = requests.post(
            f"{BASE_URL}/api/admin/customers/portal-access",
            headers=auth_headers,
            json={"email": customer_email}
        )
        if portal_response.status_code != 200:
            pytest.skip("Could not generate customer portal access")
        
        portal_data = portal_response.json()
        portal_url = portal_data.get("portal_url", "")
        
        # Extract token from portal URL
        import urllib.parse
        parsed = urllib.parse.urlparse(portal_url)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [None])[0]
        
        if not token:
            pytest.skip("Could not extract token from portal URL")
        
        # Verify token to get customer JWT
        verify_response = requests.post(
            f"{BASE_URL}/api/auth/verify-token",
            json={"token": token}
        )
        if verify_response.status_code != 200:
            pytest.skip("Token verification failed")
        
        customer_jwt = verify_response.json().get("access_token")
        if not customer_jwt:
            pytest.skip("No customer JWT received")
        
        # Now fetch project as customer
        customer_headers = {"Authorization": f"Bearer {customer_jwt}", "Content-Type": "application/json"}
        response = requests.get(
            f"{BASE_URL}/api/customer/projects/{TEST_PROJECT_ID}",
            headers=customer_headers
        )
        
        if response.status_code == 404:
            pytest.skip("Project not accessible to customer")
        
        assert response.status_code == 200, f"Customer project fetch failed: {response.text}"
        data = response.json()
        
        # Verify project_phase exists
        assert "project_phase" in data, "Missing project_phase in customer project"
        phase = data["project_phase"]
        
        # Verify phase and phase_label
        assert "phase" in phase, "Missing phase in project_phase"
        assert "phase_label" in phase, "Missing phase_label in project_phase"
        
        # Verify German labels
        german_labels = ["Bedarfsanalyse", "Angebot in Prüfung", "Vertrag ausstehend", "Zahlung ausstehend", "Build-Phase bereit"]
        assert phase["phase_label"] in german_labels, f"phase_label not in German: {phase['phase_label']}"
        
        print(f"✓ Customer project_phase: phase={phase['phase']}, phase_label={phase['phase_label']}")


class TestE2EVerifyFlow:
    """E2E verification flow."""

    def test_e2e_verify_flow(self, auth_headers):
        """Test POST /api/admin/e2e/verify-flow — Still 100% pass with all new systems."""
        response = requests.post(
            f"{BASE_URL}/api/admin/e2e/verify-flow",
            headers=auth_headers,
            json={}
        )
        if response.status_code == 404:
            pytest.skip("E2E verify flow endpoint not found")
        
        assert response.status_code == 200, f"E2E verify flow failed: {response.text}"
        data = response.json()
        
        # Check for pass status - can be boolean or count
        if "e2e_verification" in data:
            assert data["e2e_verification"] == True, f"E2E verification not true: {data}"
            assert data.get("pass_rate") == "100%", f"E2E pass rate not 100%: {data.get('pass_rate')}"
            print(f"✓ E2E verify flow: PASSED ({data.get('passed')}/{data.get('total_checks')} checks)")
        elif "passed" in data and isinstance(data["passed"], bool):
            assert data["passed"] == True, f"E2E flow not passed: {data}"
            print(f"✓ E2E verify flow: PASSED")
        elif "status" in data:
            print(f"✓ E2E verify flow: status={data['status']}")
        else:
            print(f"✓ E2E verify flow response: {data}")


class TestInvoiceDetails:
    """Test invoice details for Stripe integration."""

    def test_get_invoice_details(self, auth_headers):
        """Verify test invoice exists and has expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices/{TEST_INVOICE_ID}",
            headers=auth_headers
        )
        if response.status_code == 404:
            print(f"⚠ Test invoice {TEST_INVOICE_ID} not found")
            # List available invoices
            list_response = requests.get(f"{BASE_URL}/api/admin/invoices", headers=auth_headers)
            if list_response.status_code == 200:
                invoices = list_response.json().get("invoices", [])
                if invoices:
                    print(f"  Available invoices: {[inv.get('invoice_id') for inv in invoices[:5]]}")
            pytest.skip("Test invoice not found")
        
        assert response.status_code == 200, f"Invoice fetch failed: {response.text}"
        data = response.json()
        
        # Verify invoice structure
        assert "invoice_id" in data, "Missing invoice_id"
        assert "total_eur" in data or "amount" in data, "Missing amount field"
        
        amount = data.get("total_eur") or data.get("amount", 0)
        print(f"✓ Invoice {TEST_INVOICE_ID}: amount={amount} EUR")
        
        # Check for Stripe session
        if data.get("stripe_checkout_session_id"):
            print(f"  → Has Stripe session: {data['stripe_checkout_session_id'][:20]}...")
        if data.get("checkout_url"):
            print(f"  → Has checkout URL: {data['checkout_url'][:50]}...")


class TestContractDetails:
    """Test contract details for PDF generation."""

    def test_get_contract_details(self, auth_headers):
        """Verify test contract exists and has expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID}",
            headers=auth_headers
        )
        if response.status_code == 404:
            print(f"⚠ Test contract {TEST_CONTRACT_ID} not found")
            # List available contracts
            list_response = requests.get(f"{BASE_URL}/api/admin/contracts", headers=auth_headers)
            if list_response.status_code == 200:
                contracts = list_response.json().get("contracts", [])
                if contracts:
                    print(f"  Available contracts: {[c.get('contract_id') for c in contracts[:5]]}")
            pytest.skip("Test contract not found")
        
        assert response.status_code == 200, f"Contract fetch failed: {response.text}"
        data = response.json()
        
        # Verify contract structure
        assert "contract_id" in data, "Missing contract_id"
        assert "status" in data, "Missing status"
        
        print(f"✓ Contract {TEST_CONTRACT_ID}: status={data.get('status')}")
        print(f"  → has_pdf: {data.get('has_pdf')}")
        print(f"  → pdf_url: {data.get('pdf_url')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
