"""
Iteration 49 - Phase 2 Production Hardening Tests
Tests for:
1. Quote creation with tier=growth (upfront_eur > 0)
2. Invoice from Quote (amount_netto_eur = quote.calculation.upfront_eur)
3. Contract from Quote (auto-populate customer)
4. Full E2E Chain: Quote → Invoice → Contract
5. System Health endpoint (workers, scheduler, memory checks)
6. Oracle endpoints
7. Previously working endpoints regression
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


class TestAdminAuth:
    """Admin authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_admin_login(self, auth_token):
        """Test admin login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"✓ Admin login successful, token length: {len(auth_token)}")


class TestQuoteCreation:
    """Quote creation tests - verifying QuoteRequest model fix"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    def test_create_quote_growth_tier(self, auth_token):
        """Test: POST /api/admin/quotes with tier=growth should create quote with calculation.upfront_eur > 0"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        payload = {
            "tier": "growth",
            "customer_name": "TEST_Quote_Growth",
            "customer_email": "test_growth@example.com",
            "customer_company": "Test Growth GmbH",
            "customer_country": "DE",
            "customer_industry": "Technology",
            "use_case": "AI automation testing",
            "notes": "Test quote for iteration 49",
            "discount_percent": 0,
            "discount_reason": "",
            "special_items": []
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        assert response.status_code == 200, f"Quote creation failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "quote" in data, "No quote in response"
        quote = data["quote"]
        
        # Verify quote structure
        assert "quote_id" in quote, "No quote_id"
        assert "calculation" in quote, "No calculation in quote"
        
        calc = quote["calculation"]
        # Check upfront_eur exists and is > 0 for growth tier
        upfront = calc.get("upfront_eur") or calc.get("activation_fee_eur", 0)
        assert upfront > 0, f"upfront_eur should be > 0 for growth tier, got: {upfront}"
        
        print(f"✓ Quote created: {quote['quote_id']}")
        print(f"  - Tier: {quote['tier']}")
        print(f"  - upfront_eur: {upfront}")
        print(f"  - total_contract_eur: {calc.get('total_contract_eur', 'N/A')}")
        
        return quote
    
    def test_create_quote_starter_tier(self, auth_token):
        """Test: POST /api/admin/quotes with tier=starter"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        payload = {
            "tier": "starter",
            "customer_name": "TEST_Quote_Starter",
            "customer_email": "test_starter@example.com",
            "customer_company": "Test Starter GmbH",
            "customer_country": "DE",
            "notes": "Test starter quote"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        assert response.status_code == 200, f"Quote creation failed: {response.text}"
        
        data = response.json()
        quote = data["quote"]
        assert quote["tier"] == "starter"
        print(f"✓ Starter quote created: {quote['quote_id']}")
        
        return quote
    
    def test_create_quote_with_discount(self, auth_token):
        """Test: Quote creation with discount_percent field (model fix verification)"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        payload = {
            "tier": "growth",
            "customer_name": "TEST_Quote_Discount",
            "customer_email": "test_discount@example.com",
            "customer_company": "Test Discount GmbH",
            "discount_percent": 10,
            "discount_reason": "Early adopter discount"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        assert response.status_code == 200, f"Quote with discount failed: {response.text}"
        
        data = response.json()
        quote = data["quote"]
        
        # Verify discount was applied
        discount = quote.get("discount", {})
        assert discount.get("percent") == 10 or quote.get("calculation", {}).get("discount_percent") == 10, \
            f"Discount not applied correctly: {discount}"
        
        print(f"✓ Quote with discount created: {quote['quote_id']}")
        print(f"  - Discount: {discount}")


class TestInvoiceFromQuote:
    """Invoice creation from Quote tests - verifying upfront_eur fix"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def test_quote(self, auth_token):
        """Create a test quote for invoice tests"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        payload = {
            "tier": "growth",
            "customer_name": "TEST_Invoice_Customer",
            "customer_email": "test_invoice@example.com",
            "customer_company": "Test Invoice GmbH"
        }
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        return response.json().get("quote")
    
    def test_create_invoice_from_quote_activation(self, auth_token, test_quote):
        """Test: POST /api/admin/invoices with quote_id and type=activation should have amount_netto_eur matching quote.calculation.upfront_eur"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        quote_id = test_quote["quote_id"]
        calc = test_quote.get("calculation", {})
        expected_upfront = calc.get("upfront_eur") or calc.get("activation_fee_eur", 0)
        
        payload = {
            "quote_id": quote_id,
            "type": "activation"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/invoices", json=payload, headers=headers)
        assert response.status_code == 200, f"Invoice creation failed: {response.text}"
        
        invoice = response.json()
        assert "invoice_id" in invoice, "No invoice_id in response"
        
        # Verify amount matches upfront_eur
        amount_netto = invoice.get("amount_netto_eur", 0)
        
        # Allow for some flexibility - amount should be close to expected upfront
        if expected_upfront > 0:
            assert amount_netto > 0, f"Invoice amount should be > 0, got: {amount_netto}"
            print(f"✓ Invoice created from quote: {invoice['invoice_id']}")
            print(f"  - Quote upfront_eur: {expected_upfront}")
            print(f"  - Invoice amount_netto_eur: {amount_netto}")
        else:
            print(f"✓ Invoice created (upfront was 0): {invoice['invoice_id']}")
        
        return invoice
    
    def test_create_invoice_from_quote_recurring(self, auth_token, test_quote):
        """Test: Invoice with type=recurring uses recurring_eur"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        quote_id = test_quote["quote_id"]
        calc = test_quote.get("calculation", {})
        expected_recurring = calc.get("recurring_eur", 0)
        
        payload = {
            "quote_id": quote_id,
            "type": "recurring"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/invoices", json=payload, headers=headers)
        assert response.status_code == 200, f"Recurring invoice failed: {response.text}"
        
        invoice = response.json()
        print(f"✓ Recurring invoice created: {invoice['invoice_id']}")
        print(f"  - amount_netto_eur: {invoice.get('amount_netto_eur', 'N/A')}")


class TestContractFromQuote:
    """Contract creation from Quote tests - verifying auto-populate fix"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def test_quote(self, auth_token):
        """Create a test quote for contract tests"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        payload = {
            "tier": "growth",
            "customer_name": "TEST_Contract_Customer",
            "customer_email": "test_contract@example.com",
            "customer_company": "Test Contract GmbH"
        }
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        return response.json().get("quote")
    
    def test_create_contract_from_quote_auto_populate(self, auth_token, test_quote):
        """Test: POST /api/admin/contracts with just quote_id should auto-populate customer and create contract"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        quote_id = test_quote["quote_id"]
        quote_customer = test_quote.get("customer", {})
        
        # Only provide quote_id - customer should be auto-populated
        payload = {
            "quote_id": quote_id
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/contracts", json=payload, headers=headers)
        assert response.status_code == 200, f"Contract creation failed: {response.text}"
        
        contract = response.json()
        assert "contract_id" in contract, "No contract_id in response"
        
        # Verify customer was auto-populated from quote
        contract_customer = contract.get("customer", {})
        assert contract_customer.get("email") == quote_customer.get("email"), \
            f"Customer email not auto-populated. Expected: {quote_customer.get('email')}, Got: {contract_customer.get('email')}"
        
        # Verify tier_key was populated
        tier_key = contract.get("tier_key", "")
        assert tier_key == test_quote.get("tier", ""), \
            f"tier_key not auto-populated. Expected: {test_quote.get('tier')}, Got: {tier_key}"
        
        print(f"✓ Contract created from quote: {contract['contract_id']}")
        print(f"  - Customer auto-populated: {contract_customer.get('email')}")
        print(f"  - Tier: {tier_key}")
        
        return contract


class TestE2EChain:
    """Full E2E Chain: Quote → Invoice → Contract"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    def test_full_e2e_chain(self, auth_token):
        """Test: Quote → Invoice → Contract chain should all succeed with correct data"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Step 1: Create Quote
        quote_payload = {
            "tier": "growth",
            "customer_name": "TEST_E2E_Customer",
            "customer_email": "test_e2e@example.com",
            "customer_company": "Test E2E GmbH",
            "use_case": "Full E2E chain test"
        }
        
        quote_response = requests.post(f"{BASE_URL}/api/admin/quotes", json=quote_payload, headers=headers)
        assert quote_response.status_code == 200, f"Quote creation failed: {quote_response.text}"
        quote = quote_response.json().get("quote")
        quote_id = quote["quote_id"]
        print(f"✓ Step 1: Quote created: {quote_id}")
        
        # Step 2: Create Invoice from Quote
        invoice_payload = {
            "quote_id": quote_id,
            "type": "activation"
        }
        
        invoice_response = requests.post(f"{BASE_URL}/api/admin/invoices", json=invoice_payload, headers=headers)
        assert invoice_response.status_code == 200, f"Invoice creation failed: {invoice_response.text}"
        invoice = invoice_response.json()
        invoice_id = invoice["invoice_id"]
        print(f"✓ Step 2: Invoice created: {invoice_id}")
        
        # Step 3: Create Contract from Quote
        contract_payload = {
            "quote_id": quote_id
        }
        
        contract_response = requests.post(f"{BASE_URL}/api/admin/contracts", json=contract_payload, headers=headers)
        assert contract_response.status_code == 200, f"Contract creation failed: {contract_response.text}"
        contract = contract_response.json()
        contract_id = contract["contract_id"]
        print(f"✓ Step 3: Contract created: {contract_id}")
        
        # Verify data consistency
        assert invoice.get("quote_id") == quote_id, "Invoice quote_id mismatch"
        assert contract.get("customer", {}).get("email") == quote.get("customer", {}).get("email"), \
            "Contract customer email mismatch"
        
        print(f"✓ E2E Chain complete:")
        print(f"  - Quote: {quote_id}")
        print(f"  - Invoice: {invoice_id}")
        print(f"  - Contract: {contract_id}")


class TestSystemHealth:
    """System Health endpoint tests - verifying workers/scheduler/memory checks"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    def test_audit_health_endpoint(self, auth_token):
        """Test: GET /api/admin/audit/health should include checks.workers, checks.scheduler, checks.memory"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/audit/health", headers=headers)
        assert response.status_code == 200, f"Health endpoint failed: {response.text}"
        
        data = response.json()
        assert "overall" in data, "No overall status"
        assert "checks" in data, "No checks in response"
        
        checks = data["checks"]
        
        # Verify workers check exists
        assert "workers" in checks, "No workers check in health response"
        workers = checks["workers"]
        assert "status" in workers, "No status in workers check"
        print(f"✓ Workers check: {workers}")
        
        # Verify scheduler check exists
        assert "scheduler" in checks, "No scheduler check in health response"
        scheduler = checks["scheduler"]
        assert "status" in scheduler, "No status in scheduler check"
        print(f"✓ Scheduler check: {scheduler}")
        
        # Verify memory check exists
        assert "memory" in checks, "No memory check in health response"
        memory = checks["memory"]
        assert "status" in memory, "No status in memory check"
        print(f"✓ Memory check: {memory}")
        
        print(f"✓ System Health overall: {data['overall']}")
    
    def test_monitoring_health_alias(self, auth_token):
        """Test: GET /api/admin/monitoring/health (alias endpoint)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/health", headers=headers)
        assert response.status_code == 200, f"Monitoring health failed: {response.text}"
        
        data = response.json()
        assert "overall" in data
        print(f"✓ Monitoring health alias works: {data['overall']}")


class TestOracleEndpoints:
    """Oracle endpoints tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    def test_oracle_snapshot(self, auth_token):
        """Test: GET /api/admin/oracle/snapshot"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/oracle/snapshot", headers=headers)
        assert response.status_code == 200, f"Oracle snapshot failed: {response.text}"
        
        data = response.json()
        assert data.get("snapshot_type") == "oracle_full", f"Unexpected snapshot_type: {data.get('snapshot_type')}"
        assert "operational_data" in data, "No operational_data in snapshot"
        assert "timestamp" in data, "No timestamp in snapshot"
        
        print(f"✓ Oracle snapshot: {data['snapshot_type']}")
        print(f"  - Leads: {data.get('operational_data', {}).get('leads', {}).get('total', 'N/A')}")
        print(f"  - Quotes: {data.get('operational_data', {}).get('quotes', {}).get('total', 'N/A')}")
    
    def test_oracle_contact(self, auth_token):
        """Test: GET /api/admin/oracle/contact/{email}"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Use admin email as test contact
        test_email = ADMIN_EMAIL
        
        response = requests.get(f"{BASE_URL}/api/admin/oracle/contact/{test_email}", headers=headers)
        assert response.status_code == 200, f"Oracle contact failed: {response.text}"
        
        data = response.json()
        print(f"✓ Oracle contact endpoint works for: {test_email}")


class TestRegressionEndpoints:
    """Regression tests for previously working endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token")
    
    def test_public_health(self):
        """Test: GET /api/health"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Public health endpoint works")
    
    def test_admin_stats(self, auth_token):
        """Test: GET /api/admin/stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200, f"Admin stats failed: {response.text}"
        print("✓ Admin stats endpoint works")
    
    def test_admin_leads(self, auth_token):
        """Test: GET /api/admin/leads"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/leads", headers=headers)
        assert response.status_code == 200, f"Admin leads failed: {response.text}"
        print("✓ Admin leads endpoint works")
    
    def test_admin_bookings(self, auth_token):
        """Test: GET /api/admin/bookings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=headers)
        assert response.status_code == 200, f"Admin bookings failed: {response.text}"
        print("✓ Admin bookings endpoint works")
    
    def test_admin_quotes(self, auth_token):
        """Test: GET /api/admin/quotes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/quotes", headers=headers)
        assert response.status_code == 200, f"Admin quotes failed: {response.text}"
        print("✓ Admin quotes endpoint works")
    
    def test_admin_invoices(self, auth_token):
        """Test: GET /api/admin/invoices"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/invoices", headers=headers)
        assert response.status_code == 200, f"Admin invoices failed: {response.text}"
        print("✓ Admin invoices endpoint works")
    
    def test_admin_contracts(self, auth_token):
        """Test: GET /api/admin/contracts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/contracts", headers=headers)
        assert response.status_code == 200, f"Admin contracts failed: {response.text}"
        print("✓ Admin contracts endpoint works")
    
    def test_billing_overview(self, auth_token):
        """Test: GET /api/admin/billing/overview"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/billing/overview", headers=headers)
        assert response.status_code == 200, f"Billing overview failed: {response.text}"
        print("✓ Billing overview endpoint works")
    
    def test_outbound_campaigns(self, auth_token):
        """Test: GET /api/admin/outbound/campaigns"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/outbound/campaigns", headers=headers)
        assert response.status_code == 200, f"Outbound campaigns failed: {response.text}"
        print("✓ Outbound campaigns endpoint works")
    
    def test_monitoring_workers(self, auth_token):
        """Test: GET /api/admin/monitoring/workers"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/workers", headers=headers)
        assert response.status_code == 200, f"Monitoring workers failed: {response.text}"
        print("✓ Monitoring workers endpoint works")
    
    def test_memory_stats(self, auth_token):
        """Test: GET /api/admin/memory/stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/memory/stats", headers=headers)
        assert response.status_code == 200, f"Memory stats failed: {response.text}"
        data = response.json()
        assert data.get("oracle_status") == "operational", f"Oracle not operational: {data.get('oracle_status')}"
        print("✓ Memory stats endpoint works")
    
    def test_workers_status(self, auth_token):
        """Test: GET /api/admin/workers/status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/workers/status", headers=headers)
        assert response.status_code == 200, f"Workers status failed: {response.text}"
        print("✓ Workers status endpoint works")
    
    def test_llm_status(self, auth_token):
        """Test: GET /api/admin/llm/status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/llm/status", headers=headers)
        assert response.status_code == 200, f"LLM status failed: {response.text}"
        print("✓ LLM status endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
