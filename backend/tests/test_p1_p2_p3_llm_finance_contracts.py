"""
Test Suite for P1 (DeepSeek LLM Provider), P2 (Portal Finance), P3 (Contract OS Enhancement)
Iteration 35 - Testing new features:
- P1: LLM Provider abstraction with DeepSeek/Emergent GPT fallback
- P2: Customer Portal Finance view (invoices, payment status, bank info)
- P3: Contract OS enhancements (versions, evidence trail, signature preview)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"
TEST_CONTRACT_ID = "ctr_fa24ac23eb394673"
TEST_CUSTOMER_EMAIL = "max@testfirma.de"


class TestAdminAuth:
    """Admin authentication for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_admin_login(self, admin_token):
        """Verify admin login works"""
        assert admin_token is not None
        assert len(admin_token) > 20
        print(f"✅ Admin login successful, token length: {len(admin_token)}")


class TestP1LLMProviderStatus:
    """P1: LLM Provider Status Endpoint Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("access_token")
    
    def test_llm_status_endpoint(self, admin_token):
        """GET /api/admin/llm/status - Returns provider info, migration status, metrics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/llm/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"LLM status failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "active_provider" in data, "Missing active_provider"
        assert "is_target_architecture" in data, "Missing is_target_architecture"
        assert "providers" in data, "Missing providers"
        assert "migration_ready" in data, "Missing migration_ready"
        
        # Verify provider details
        providers = data["providers"]
        assert "deepseek" in providers, "Missing deepseek provider info"
        assert "emergent_gpt" in providers, "Missing emergent_gpt provider info"
        
        # Since DEEPSEEK_API_KEY is not set, should be using emergent_gpt fallback
        assert data["active_provider"] == "emergent_gpt_fallback", f"Expected emergent_gpt_fallback, got {data['active_provider']}"
        assert data["is_target_architecture"] == False, "Should not be target architecture without DeepSeek"
        
        print(f"✅ LLM Status: active_provider={data['active_provider']}, migration_ready={data['migration_ready']}")
        print(f"   DeepSeek status: {providers['deepseek']['status']}")
        print(f"   Emergent GPT status: {providers['emergent_gpt']['status']}")
    
    def test_llm_status_requires_auth(self):
        """LLM status endpoint requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/llm/status")
        assert response.status_code in (401, 403), "Should require auth"
        print("✅ LLM status correctly requires authentication")


class TestP1LLMHealthCheck:
    """P1: LLM Health Check Endpoint Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("access_token")
    
    def test_llm_health_endpoint(self, admin_token):
        """GET /api/admin/llm/health - Live health check against active provider"""
        response = requests.get(
            f"{BASE_URL}/api/admin/llm/health",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=60  # LLM calls can be slow
        )
        assert response.status_code == 200, f"LLM health check failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "status" in data, "Missing status"
        assert "provider" in data, "Missing provider"
        assert "is_target_architecture" in data, "Missing is_target_architecture"
        
        # Should be using emergent_gpt_fallback
        assert data["provider"] == "emergent_gpt_fallback", f"Expected emergent_gpt_fallback, got {data['provider']}"
        
        # Status should be healthy or degraded (not error)
        assert data["status"] in ("healthy", "degraded", "not_configured"), f"Unexpected status: {data['status']}"
        
        print(f"✅ LLM Health: status={data['status']}, provider={data['provider']}")
        if "response_sample" in data:
            print(f"   Response sample: {data['response_sample'][:50]}...")


class TestP1LLMTest:
    """P1: LLM Test Endpoint Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("access_token")
    
    def test_llm_test_endpoint_default(self, admin_token):
        """POST /api/admin/llm/test - LLM test with default prompt"""
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
            timeout=60
        )
        assert response.status_code == 200, f"LLM test failed: {response.text}"
        data = response.json()
        
        assert "provider" in data, "Missing provider"
        assert "response" in data, "Missing response"
        assert "success" in data, "Missing success"
        
        print(f"✅ LLM Test (default): provider={data['provider']}, success={data['success']}")
        print(f"   Response: {data['response'][:100]}...")
    
    def test_llm_test_endpoint_custom_prompt(self, admin_token):
        """POST /api/admin/llm/test - LLM test with custom prompt"""
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"prompt": "Was ist 2+2? Antworte nur mit der Zahl."},
            timeout=60
        )
        assert response.status_code == 200, f"LLM test failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True or "4" in data.get("response", ""), "Custom prompt test should work"
        print(f"✅ LLM Test (custom prompt): success={data['success']}")


class TestP1LLMAgentFlow:
    """P1: LLM Agent Flow Test Endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("access_token")
    
    def test_llm_agent_flow_endpoint(self, admin_token):
        """POST /api/admin/llm/test-agent-flow - Full agent flow test with session continuity"""
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test-agent-flow",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
            timeout=120  # Agent flow can be slow (2 LLM calls)
        )
        assert response.status_code == 200, f"LLM agent flow test failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "provider" in data, "Missing provider"
        assert "session_id" in data, "Missing session_id"
        assert "test_results" in data, "Missing test_results"
        assert "success" in data, "Missing success"
        
        # Verify test results structure
        results = data["test_results"]
        assert "initial_response" in results, "Missing initial_response"
        assert "followup_response" in results, "Missing followup_response"
        assert "session_continuity" in results, "Missing session_continuity"
        
        print(f"✅ LLM Agent Flow: provider={data['provider']}, success={data['success']}")
        print(f"   Initial response OK: {results['initial_response']['ok']}")
        print(f"   Followup response OK: {results['followup_response']['ok']}")
        print(f"   Session continuity: {results['session_continuity']}")


class TestP2CustomerFinance:
    """P2: Customer Portal Finance Endpoint Tests"""
    
    @pytest.fixture(scope="class")
    def customer_token(self):
        """Get customer JWT token via admin portal-access + verify-token flow"""
        # First get admin token
        admin_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        admin_token = admin_response.json().get("access_token")
        
        # Generate customer portal magic link
        portal_response = requests.post(
            f"{BASE_URL}/api/admin/customers/portal-access",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": TEST_CUSTOMER_EMAIL}
        )
        if portal_response.status_code != 200:
            pytest.skip(f"Could not get customer portal access: {portal_response.text}")
        
        # Extract magic token from portal URL
        portal_url = portal_response.json().get("portal_url", "")
        magic_token = portal_url.split("/portal/")[-1] if "/portal/" in portal_url else None
        if not magic_token:
            pytest.skip("Could not extract magic token from portal URL")
        
        # Verify magic token to get JWT
        verify_response = requests.post(
            f"{BASE_URL}/api/auth/verify-token",
            json={"token": magic_token}
        )
        if verify_response.status_code != 200:
            pytest.skip(f"Could not verify token: {verify_response.text}")
        
        return verify_response.json().get("access_token")
    
    def test_customer_finance_endpoint(self, customer_token):
        """GET /api/customer/finance - Full finance data"""
        response = requests.get(
            f"{BASE_URL}/api/customer/finance",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200, f"Customer finance failed: {response.text}"
        data = response.json()
        
        # Verify required top-level fields
        assert "summary" in data, "Missing summary"
        assert "invoices" in data, "Missing invoices"
        assert "quotes" in data, "Missing quotes"
        assert "contracts" in data, "Missing contracts"
        assert "bank_transfer_info" in data, "Missing bank_transfer_info"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_invoices" in summary, "Missing total_invoices"
        assert "total_outstanding_eur" in summary, "Missing total_outstanding_eur"
        assert "total_paid_eur" in summary, "Missing total_paid_eur"
        assert "open_invoices" in summary, "Missing open_invoices"
        assert "overdue_invoices" in summary, "Missing overdue_invoices"
        
        # Verify bank transfer info
        bank_info = data["bank_transfer_info"]
        assert "iban" in bank_info, "Missing IBAN"
        assert "bic" in bank_info, "Missing BIC"
        assert "bank_name" in bank_info, "Missing bank_name"
        assert "account_holder" in bank_info, "Missing account_holder"
        
        print(f"✅ Customer Finance: {summary['total_invoices']} invoices, {summary['open_invoices']} open")
        print(f"   Outstanding: {summary['total_outstanding_eur']}€, Paid: {summary['total_paid_eur']}€")
        print(f"   Bank: {bank_info['account_holder']} - {bank_info['iban'][:10]}...")
    
    def test_customer_finance_invoice_structure(self, customer_token):
        """Verify invoice data structure in finance endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/customer/finance",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        data = response.json()
        
        if len(data["invoices"]) > 0:
            inv = data["invoices"][0]
            # Verify invoice fields
            required_fields = [
                "invoice_id", "invoice_number", "payment_status", 
                "payment_status_label", "payment_status_severity",
                "amount_net", "amount_vat", "amount_gross",
                "date", "due_date", "is_overdue", "reminder_count", "reminder_level"
            ]
            for field in required_fields:
                assert field in inv, f"Missing invoice field: {field}"
            
            # Verify payment status severity is valid
            assert inv["payment_status_severity"] in ("success", "warning", "error", "neutral"), \
                f"Invalid severity: {inv['payment_status_severity']}"
            
            print(f"✅ Invoice structure verified: {inv['invoice_number']}")
            print(f"   Status: {inv['payment_status_label']} ({inv['payment_status_severity']})")
            print(f"   Amount: {inv['amount_gross']}€, Due: {inv['due_date']}")
        else:
            print("⚠️ No invoices found for test customer")
    
    def test_customer_finance_requires_customer_auth(self):
        """Finance endpoint requires customer auth, not admin"""
        # Get admin token
        admin_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        admin_token = admin_response.json().get("access_token")
        
        # Try to access finance with admin token (should fail)
        response = requests.get(
            f"{BASE_URL}/api/customer/finance",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should be 403 Forbidden (admin can't access customer endpoints)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Finance endpoint correctly rejects admin token")


class TestP3ContractOSEnhancements:
    """P3: Contract OS Enhancement Tests - versions, evidence, signature preview"""
    
    @pytest.fixture(scope="class")
    def customer_token(self):
        """Get customer JWT token via admin portal-access + verify-token flow"""
        admin_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        admin_token = admin_response.json().get("access_token")
        
        portal_response = requests.post(
            f"{BASE_URL}/api/admin/customers/portal-access",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": TEST_CUSTOMER_EMAIL}
        )
        if portal_response.status_code != 200:
            pytest.skip(f"Could not get customer portal access: {portal_response.text}")
        
        portal_url = portal_response.json().get("portal_url", "")
        magic_token = portal_url.split("/portal/")[-1] if "/portal/" in portal_url else None
        if not magic_token:
            pytest.skip("Could not extract magic token from portal URL")
        
        verify_response = requests.post(
            f"{BASE_URL}/api/auth/verify-token",
            json={"token": magic_token}
        )
        if verify_response.status_code != 200:
            pytest.skip(f"Could not verify token: {verify_response.text}")
        
        return verify_response.json().get("access_token")
    
    def test_contract_detail_enhanced_fields(self, customer_token):
        """GET /api/customer/contracts/{id} - Returns enhanced fields"""
        response = requests.get(
            f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        
        if response.status_code == 404:
            pytest.skip(f"Test contract {TEST_CONTRACT_ID} not found for customer")
        
        assert response.status_code == 200, f"Contract detail failed: {response.text}"
        data = response.json()
        
        # Verify enhanced fields exist
        assert "versions" in data, "Missing versions field"
        assert "evidence_trail" in data, "Missing evidence_trail field"
        assert "has_pdf" in data, "Missing has_pdf field"
        
        # Verify versions structure
        assert isinstance(data["versions"], list), "versions should be a list"
        
        # Verify evidence_trail structure
        assert isinstance(data["evidence_trail"], list), "evidence_trail should be a list"
        
        print(f"✅ Contract detail enhanced: {data.get('contract_number', TEST_CONTRACT_ID)}")
        print(f"   Versions: {len(data['versions'])}")
        print(f"   Evidence trail entries: {len(data['evidence_trail'])}")
        print(f"   Has PDF: {data['has_pdf']}")
        
        # Check for signature_preview if contract is accepted
        if data.get("status") == "accepted" and data.get("signature"):
            assert "signature_preview" in data, "Missing signature_preview for accepted contract"
            print(f"   Signature preview: {data['signature_preview'].get('type', 'N/A')}")
        
        # Check for change_request_detail if change requested
        if data.get("change_request"):
            assert "change_request_detail" in data, "Missing change_request_detail"
            print(f"   Change request: {data['change_request_detail'].get('text', '')[:50]}...")
    
    def test_contract_evidence_trail_structure(self, customer_token):
        """Verify evidence trail structure in contract detail"""
        response = requests.get(
            f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        
        if response.status_code == 404:
            pytest.skip(f"Test contract {TEST_CONTRACT_ID} not found")
        
        data = response.json()
        evidence_trail = data.get("evidence_trail", [])
        
        if len(evidence_trail) > 0:
            evidence = evidence_trail[0]
            expected_fields = [
                "evidence_id", "action", "timestamp", "ip_address",
                "user_agent", "document_hash", "contract_version"
            ]
            for field in expected_fields:
                assert field in evidence, f"Missing evidence field: {field}"
            
            print(f"✅ Evidence trail structure verified")
            print(f"   Latest action: {evidence['action']} at {evidence['timestamp']}")
        else:
            print("⚠️ No evidence trail entries for test contract")
    
    def test_contract_versions_structure(self, customer_token):
        """Verify versions structure in contract detail"""
        response = requests.get(
            f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        
        if response.status_code == 404:
            pytest.skip(f"Test contract {TEST_CONTRACT_ID} not found")
        
        data = response.json()
        versions = data.get("versions", [])
        
        if len(versions) > 0:
            version = versions[0]
            expected_fields = ["version", "status", "timestamp"]
            for field in expected_fields:
                assert field in version, f"Missing version field: {field}"
            
            print(f"✅ Versions structure verified: {len(versions)} version(s)")
        else:
            print("⚠️ No version history for test contract")


class TestCustomerContractsList:
    """Test customer contracts list endpoint"""
    
    @pytest.fixture(scope="class")
    def customer_token(self):
        admin_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        admin_token = admin_response.json().get("access_token")
        
        portal_response = requests.post(
            f"{BASE_URL}/api/admin/customers/portal-access",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": TEST_CUSTOMER_EMAIL}
        )
        if portal_response.status_code != 200:
            pytest.skip(f"Could not get customer portal access")
        
        portal_url = portal_response.json().get("portal_url", "")
        magic_token = portal_url.split("/portal/")[-1] if "/portal/" in portal_url else None
        if not magic_token:
            pytest.skip("Could not extract magic token from portal URL")
        
        verify_response = requests.post(
            f"{BASE_URL}/api/auth/verify-token",
            json={"token": magic_token}
        )
        if verify_response.status_code != 200:
            pytest.skip(f"Could not verify token")
        
        return verify_response.json().get("access_token")
    
    def test_customer_contracts_list(self, customer_token):
        """GET /api/customer/contracts - List customer contracts"""
        response = requests.get(
            f"{BASE_URL}/api/customer/contracts",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200, f"Contracts list failed: {response.text}"
        data = response.json()
        
        assert "contracts" in data, "Missing contracts field"
        assert isinstance(data["contracts"], list), "contracts should be a list"
        
        print(f"✅ Customer contracts list: {len(data['contracts'])} contracts")
        
        if len(data["contracts"]) > 0:
            contract = data["contracts"][0]
            print(f"   First contract: {contract.get('contract_number', contract.get('contract_id'))}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
