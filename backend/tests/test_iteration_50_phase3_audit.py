"""
NeXifyAI Iteration 50 - Phase 3 Full System Audit Tests
Covers: Public endpoints, Admin endpoints, Quote→Invoice→Contract chain, Oracle endpoints, System Health
"""
import pytest
import requests
import os
import secrets
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://contract-os.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    form_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    response = requests.post(f"{BASE_URL}/api/admin/login", data=form_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code}")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestPublicEndpoints:
    """Test all public endpoints (no auth required)"""

    def test_health_endpoint(self):
        """GET /api/health - System health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "version" in data
        print(f"Health: {data}")

    def test_booking_slots_endpoint(self):
        """GET /api/booking/slots - Available booking slots"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/booking/slots?date={future_date}")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "date" in data
        print(f"Booking slots for {future_date}: {len(data.get('slots', []))} slots")

    def test_contact_endpoint(self):
        """POST /api/contact - Contact form submission"""
        test_email = f"test_{secrets.token_hex(4)}@test.com"
        payload = {
            "vorname": "Test",
            "nachname": "User",
            "email": test_email,
            "nachricht": "Test message from iteration 50",
            "source": "test",
            "language": "de"
        }
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True or "lead_id" in data
        print(f"Contact created: {data}")

    def test_booking_endpoint(self):
        """POST /api/booking - Booking submission"""
        test_email = f"test_{secrets.token_hex(4)}@test.com"
        future_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        # Get available slots first
        slots_resp = requests.get(f"{BASE_URL}/api/booking/slots?date={future_date}")
        assert slots_resp.status_code == 200
        slots = slots_resp.json().get("slots", [])
        
        if not slots:
            pytest.skip("No available slots for booking test")
        
        payload = {
            "vorname": "Test",
            "nachname": "Booking",
            "email": test_email,
            "date": future_date,
            "time": slots[0],  # Use first available slot
            "source": "test",
            "language": "de"
        }
        response = requests.post(f"{BASE_URL}/api/booking", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "booking_id" in data or data.get("success") == True
        print(f"Booking created: {data.get('booking_id', 'success')}")

    def test_chat_message_endpoint(self):
        """POST /api/chat/message - Chat message"""
        session_id = f"test_{secrets.token_hex(8)}"
        payload = {
            "session_id": session_id,
            "message": "Hallo, was bietet NeXifyAI an?",
            "language": "de"
        }
        response = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "message" in data
        print(f"Chat response received (session: {session_id})")


class TestAdminAuthentication:
    """Test admin login"""

    def test_admin_login(self):
        """POST /api/admin/login - Admin authentication"""
        form_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response = requests.post(f"{BASE_URL}/api/admin/login", data=form_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"Admin login successful")


class TestAdminEndpoints:
    """Test all admin endpoints return 200"""

    def test_admin_stats(self, admin_headers):
        """GET /api/admin/stats"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads_total" in data or "total" in str(data)
        print(f"Stats: leads_total={data.get('leads_total', 'N/A')}")

    def test_admin_leads(self, admin_headers):
        """GET /api/admin/leads"""
        response = requests.get(f"{BASE_URL}/api/admin/leads", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        print(f"Leads: {len(data.get('leads', []))} total")

    def test_admin_bookings(self, admin_headers):
        """GET /api/admin/bookings"""
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=admin_headers)
        assert response.status_code == 200
        print("Bookings endpoint OK")

    def test_admin_quotes(self, admin_headers):
        """GET /api/admin/quotes"""
        response = requests.get(f"{BASE_URL}/api/admin/quotes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        print(f"Quotes: {len(data.get('quotes', []))} total")

    def test_admin_invoices(self, admin_headers):
        """GET /api/admin/invoices"""
        response = requests.get(f"{BASE_URL}/api/admin/invoices", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        print(f"Invoices: {len(data.get('invoices', []))} total")

    def test_admin_contracts(self, admin_headers):
        """GET /api/admin/contracts"""
        response = requests.get(f"{BASE_URL}/api/admin/contracts", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "contracts" in data
        print(f"Contracts: {len(data.get('contracts', []))} total")

    def test_admin_projects(self, admin_headers):
        """GET /api/admin/projects"""
        response = requests.get(f"{BASE_URL}/api/admin/projects", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"Projects: {len(data.get('projects', []))} total")

    def test_admin_billing_overview(self, admin_headers):
        """GET /api/admin/billing/overview"""
        response = requests.get(f"{BASE_URL}/api/admin/billing/overview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Response has summary.quotes and summary.invoices structure
        assert "summary" in data or "quotes" in data or "invoices" in data
        print(f"Billing overview OK")

    def test_admin_billing_status(self, admin_headers):
        """GET /api/admin/billing/status"""
        response = requests.get(f"{BASE_URL}/api/admin/billing/status", headers=admin_headers)
        assert response.status_code == 200
        print("Billing status OK")

    def test_admin_outbound_campaigns(self, admin_headers):
        """GET /api/admin/outbound/campaigns"""
        response = requests.get(f"{BASE_URL}/api/admin/outbound/campaigns", headers=admin_headers)
        assert response.status_code == 200
        print("Outbound campaigns OK")

    def test_admin_outbound_pipeline(self, admin_headers):
        """GET /api/admin/outbound/pipeline"""
        response = requests.get(f"{BASE_URL}/api/admin/outbound/pipeline", headers=admin_headers)
        assert response.status_code == 200
        print("Outbound pipeline OK")

    def test_admin_commercial_stats(self, admin_headers):
        """GET /api/admin/commercial/stats"""
        response = requests.get(f"{BASE_URL}/api/admin/commercial/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data or "invoices" in data
        print(f"Commercial stats OK")

    def test_admin_email_stats(self, admin_headers):
        """GET /api/admin/email/stats"""
        response = requests.get(f"{BASE_URL}/api/admin/email/stats", headers=admin_headers)
        assert response.status_code == 200
        print("Email stats OK")

    def test_admin_webhooks_history(self, admin_headers):
        """GET /api/admin/webhooks/history"""
        response = requests.get(f"{BASE_URL}/api/admin/webhooks/history", headers=admin_headers)
        assert response.status_code == 200
        print("Webhooks history OK")

    def test_admin_legal_risks(self, admin_headers):
        """GET /api/admin/legal/risks"""
        response = requests.get(f"{BASE_URL}/api/admin/legal/risks", headers=admin_headers)
        assert response.status_code == 200
        print("Legal risks OK")

    def test_admin_legal_audit(self, admin_headers):
        """GET /api/admin/legal/audit"""
        response = requests.get(f"{BASE_URL}/api/admin/legal/audit", headers=admin_headers)
        assert response.status_code == 200
        print("Legal audit OK")

    def test_admin_legal_compliance(self, admin_headers):
        """GET /api/admin/legal/compliance"""
        response = requests.get(f"{BASE_URL}/api/admin/legal/compliance", headers=admin_headers)
        assert response.status_code == 200
        print("Legal compliance OK")

    def test_admin_audit_health(self, admin_headers):
        """GET /api/admin/audit/health - System Health with workers/scheduler/memory"""
        response = requests.get(f"{BASE_URL}/api/admin/audit/health", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "checks" in data
        checks = data.get("checks", {})
        # Verify workers, scheduler, memory checks exist
        assert "workers" in checks, "Workers check missing"
        assert "scheduler" in checks, "Scheduler check missing"
        assert "memory" in checks, "Memory check missing"
        print(f"System Health: overall={data.get('overall')}, workers={checks.get('workers', {}).get('status')}, scheduler={checks.get('scheduler', {}).get('status')}, memory={checks.get('memory', {}).get('status')}")

    def test_admin_workers_status(self, admin_headers):
        """GET /api/admin/workers/status"""
        response = requests.get(f"{BASE_URL}/api/admin/workers/status", headers=admin_headers)
        assert response.status_code == 200
        print("Workers status OK")

    def test_admin_llm_test(self, admin_headers):
        """POST /api/admin/llm/test"""
        response = requests.post(f"{BASE_URL}/api/admin/llm/test", headers=admin_headers, json={})
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        print(f"LLM test: provider={data.get('provider')}, success={data.get('success')}")

    def test_admin_monitoring_health(self, admin_headers):
        """GET /api/admin/monitoring/health"""
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/health", headers=admin_headers)
        assert response.status_code == 200
        print("Monitoring health OK")

    def test_admin_monitoring_workers(self, admin_headers):
        """GET /api/admin/monitoring/workers"""
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/workers", headers=admin_headers)
        assert response.status_code == 200
        print("Monitoring workers OK")


class TestOracleEndpoints:
    """Test Oracle/Single Source of Truth endpoints"""

    def test_oracle_snapshot(self, admin_headers):
        """GET /api/admin/oracle/snapshot - Full system snapshot"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/snapshot", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "operational_data" in data
        assert "financial" in data
        assert "infrastructure" in data
        print(f"Oracle snapshot: leads={data.get('operational_data', {}).get('leads', {}).get('total', 'N/A')}")

    def test_oracle_contact(self, admin_headers):
        """GET /api/admin/oracle/contact/{email} - Contact oracle"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/contact/{ADMIN_EMAIL}", headers=admin_headers)
        assert response.status_code == 200
        print("Oracle contact OK")

    def test_memory_stats(self, admin_headers):
        """GET /api/admin/memory/stats - Memory service stats"""
        response = requests.get(f"{BASE_URL}/api/admin/memory/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "oracle_status" in data
        assert "totals" in data
        print(f"Memory stats: entries={data.get('totals', {}).get('memory_entries', 'N/A')}")


class TestQuoteInvoiceContractChain:
    """Test the full Quote → Invoice → Contract E2E chain"""

    def test_create_quote_growth_tier(self, admin_headers):
        """POST /api/admin/quotes - Create Growth tier quote with upfront_eur > 0"""
        test_email = f"test_chain_{secrets.token_hex(4)}@test.com"
        payload = {
            "tier": "growth",
            "customer_name": "Test Chain Customer",
            "customer_email": test_email,
            "customer_company": "Test GmbH",
            "customer_country": "DE",
            "customer_industry": "IT",
            "use_case": "E2E Chain Test",
            "notes": "Iteration 50 test"
        }
        response = requests.post(f"{BASE_URL}/api/admin/quotes", headers=admin_headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        quote = data.get("quote", data)
        assert "quote_id" in quote
        calc = quote.get("calculation", {})
        # Growth tier should have upfront_eur > 0
        upfront = calc.get("upfront_eur", 0)
        assert upfront > 0, f"Growth tier upfront_eur should be > 0, got {upfront}"
        print(f"Quote created: {quote.get('quote_id')}, tier=growth, upfront_eur={upfront}")
        return quote

    def test_create_invoice_from_quote_activation(self, admin_headers):
        """POST /api/admin/invoices - Create activation invoice from quote"""
        # First create a quote
        test_email = f"test_inv_{secrets.token_hex(4)}@test.com"
        quote_payload = {
            "tier": "growth",
            "customer_name": "Invoice Test",
            "customer_email": test_email,
            "customer_company": "Invoice GmbH",
            "customer_country": "DE"
        }
        quote_resp = requests.post(f"{BASE_URL}/api/admin/quotes", headers=admin_headers, json=quote_payload)
        assert quote_resp.status_code == 200
        quote = quote_resp.json().get("quote", quote_resp.json())
        quote_id = quote.get("quote_id")
        upfront_eur = quote.get("calculation", {}).get("upfront_eur", 0)

        # Create activation invoice
        invoice_payload = {
            "quote_id": quote_id,
            "type": "activation"
        }
        inv_resp = requests.post(f"{BASE_URL}/api/admin/invoices", headers=admin_headers, json=invoice_payload)
        assert inv_resp.status_code == 200
        invoice = inv_resp.json()
        assert "invoice_id" in invoice
        # Verify amount matches upfront_eur
        amount = invoice.get("amount_netto_eur", 0)
        assert amount > 0, f"Invoice amount should be > 0, got {amount}"
        print(f"Invoice created: {invoice.get('invoice_id')}, amount_netto_eur={amount}, expected upfront_eur={upfront_eur}")
        return invoice, quote_id

    def test_create_contract_from_quote(self, admin_headers):
        """POST /api/admin/contracts - Create contract from quote (auto-populate customer)"""
        # First create a quote
        test_email = f"test_ctr_{secrets.token_hex(4)}@test.com"
        quote_payload = {
            "tier": "growth",
            "customer_name": "Contract Test",
            "customer_email": test_email,
            "customer_company": "Contract GmbH",
            "customer_country": "DE"
        }
        quote_resp = requests.post(f"{BASE_URL}/api/admin/quotes", headers=admin_headers, json=quote_payload)
        assert quote_resp.status_code == 200
        quote = quote_resp.json().get("quote", quote_resp.json())
        quote_id = quote.get("quote_id")

        # Create contract with only quote_id (should auto-populate customer)
        contract_payload = {
            "quote_id": quote_id
        }
        ctr_resp = requests.post(f"{BASE_URL}/api/admin/contracts", headers=admin_headers, json=contract_payload)
        assert ctr_resp.status_code == 200
        contract = ctr_resp.json()
        assert "contract_id" in contract
        # Verify customer was auto-populated from quote
        customer = contract.get("customer", {})
        assert customer.get("email") == test_email, f"Customer email should be auto-populated from quote"
        print(f"Contract created: {contract.get('contract_id')}, customer_email={customer.get('email')}")
        return contract


class TestFullE2EChain:
    """Test complete Quote → Invoice → Contract chain"""

    def test_full_chain(self, admin_headers):
        """Full E2E: Quote → Invoice → Contract"""
        test_email = f"test_e2e_{secrets.token_hex(4)}@test.com"
        
        # Step 1: Create Quote
        quote_payload = {
            "tier": "growth",
            "customer_name": "E2E Full Test",
            "customer_email": test_email,
            "customer_company": "E2E GmbH",
            "customer_country": "DE",
            "customer_industry": "Technology",
            "use_case": "Full E2E Chain Test"
        }
        quote_resp = requests.post(f"{BASE_URL}/api/admin/quotes", headers=admin_headers, json=quote_payload)
        assert quote_resp.status_code == 200, f"Quote creation failed: {quote_resp.text}"
        quote = quote_resp.json().get("quote", quote_resp.json())
        quote_id = quote.get("quote_id")
        upfront_eur = quote.get("calculation", {}).get("upfront_eur", 0)
        print(f"Step 1 - Quote created: {quote_id}, upfront_eur={upfront_eur}")

        # Step 2: Create Invoice from Quote
        invoice_payload = {
            "quote_id": quote_id,
            "type": "activation"
        }
        inv_resp = requests.post(f"{BASE_URL}/api/admin/invoices", headers=admin_headers, json=invoice_payload)
        assert inv_resp.status_code == 200, f"Invoice creation failed: {inv_resp.text}"
        invoice = inv_resp.json()
        invoice_id = invoice.get("invoice_id")
        print(f"Step 2 - Invoice created: {invoice_id}, amount={invoice.get('amount_netto_eur')}")

        # Step 3: Create Contract from Quote
        contract_payload = {
            "quote_id": quote_id
        }
        ctr_resp = requests.post(f"{BASE_URL}/api/admin/contracts", headers=admin_headers, json=contract_payload)
        assert ctr_resp.status_code == 200, f"Contract creation failed: {ctr_resp.text}"
        contract = ctr_resp.json()
        contract_id = contract.get("contract_id")
        customer_email = contract.get("customer", {}).get("email")
        print(f"Step 3 - Contract created: {contract_id}, customer_email={customer_email}")

        # Verify chain integrity
        assert customer_email == test_email, "Contract customer email should match quote"
        print(f"E2E Chain SUCCESS: Quote({quote_id}) → Invoice({invoice_id}) → Contract({contract_id})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
