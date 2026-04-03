"""
Test Customer Portal P1: Contracts + Projects
- Customer contract endpoints (list, detail, accept, decline, change-request)
- Customer project endpoints (list, detail, chat)
- Admin contract endpoints (create, list, detail, send)
"""
import pytest
import requests
import os
import secrets

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"

# Test customer email from test_credentials.md
TEST_CUSTOMER_EMAIL = "max@testfirma.de"
TEST_CONTRACT_ID = "ctr_fa24ac23eb394673"
TEST_PROJECT_ID = "prj_6c4e346089384828"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin JWT token."""
    r = requests.post(f"{BASE_URL}/api/admin/login", data={
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin auth headers."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestAdminContractEndpoints:
    """Admin contract management endpoints."""
    
    def test_admin_list_contracts(self, admin_headers):
        """GET /api/admin/contracts - List all contracts."""
        r = requests.get(f"{BASE_URL}/api/admin/contracts", headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert "contracts" in data
        assert "total" in data
        print(f"✅ Admin contracts list: {data['total']} contracts found")
    
    def test_admin_list_contracts_by_status(self, admin_headers):
        """GET /api/admin/contracts?status=sent - Filter by status."""
        r = requests.get(f"{BASE_URL}/api/admin/contracts?status=sent", headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert "contracts" in data
        # All returned contracts should have status=sent
        for c in data["contracts"]:
            assert c.get("status") == "sent", f"Expected status=sent, got {c.get('status')}"
        print(f"✅ Admin contracts filtered by status=sent: {len(data['contracts'])} contracts")
    
    def test_admin_create_contract(self, admin_headers):
        """POST /api/admin/contracts - Create new contract."""
        payload = {
            "customer": {
                "email": f"TEST_contract_{secrets.token_hex(4)}@test.de",
                "name": "Test Kunde",
                "company": "Test GmbH"
            },
            "tier_key": "starter",
            "contract_type": "standard",
            "notes": "Test contract created by pytest"
        }
        r = requests.post(f"{BASE_URL}/api/admin/contracts", json=payload, headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert "contract_id" in data
        assert "contract_number" in data
        assert data["status"] == "draft"
        assert data["customer"]["email"] == payload["customer"]["email"].lower()
        print(f"✅ Contract created: {data['contract_number']} (ID: {data['contract_id']})")
        return data["contract_id"]
    
    def test_admin_get_contract_detail(self, admin_headers):
        """GET /api/admin/contracts/{id} - Get contract detail."""
        # First get a contract ID
        r = requests.get(f"{BASE_URL}/api/admin/contracts?limit=1", headers=admin_headers)
        assert r.status_code == 200
        contracts = r.json().get("contracts", [])
        if not contracts:
            pytest.skip("No contracts available for detail test")
        
        contract_id = contracts[0]["contract_id"]
        r = requests.get(f"{BASE_URL}/api/admin/contracts/{contract_id}", headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert data["contract_id"] == contract_id
        assert "appendices_detail" in data
        assert "evidence_list" in data
        assert "document_hash" in data
        assert "legal_module_definitions" in data
        # Verify legal modules structure
        assert len(data["legal_module_definitions"]) >= 4  # At least 4 required modules
        print(f"✅ Contract detail: {data.get('contract_number')} with {len(data.get('appendices_detail', []))} appendices")
    
    def test_admin_update_contract_status(self, admin_headers):
        """PATCH /api/admin/contracts/{id} - Update contract status."""
        # Create a test contract first
        payload = {
            "customer": {"email": f"TEST_update_{secrets.token_hex(4)}@test.de", "name": "Update Test"},
            "tier_key": "starter",
            "contract_type": "standard"
        }
        r = requests.post(f"{BASE_URL}/api/admin/contracts", json=payload, headers=admin_headers)
        assert r.status_code == 200
        contract_id = r.json()["contract_id"]
        
        # Update status to review
        r = requests.patch(f"{BASE_URL}/api/admin/contracts/{contract_id}", 
                          json={"status": "review"}, headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        assert r.json().get("updated") == True
        
        # Verify update
        r = requests.get(f"{BASE_URL}/api/admin/contracts/{contract_id}", headers=admin_headers)
        assert r.json()["status"] == "review"
        assert r.json()["version"] == 2  # Version should increment
        print(f"✅ Contract status updated to 'review', version incremented to 2")
    
    def test_admin_add_appendix(self, admin_headers):
        """POST /api/admin/contracts/{id}/appendices - Add appendix."""
        # Create a test contract
        payload = {
            "customer": {"email": f"TEST_appendix_{secrets.token_hex(4)}@test.de", "name": "Appendix Test"},
            "tier_key": "growth",
            "contract_type": "standard"
        }
        r = requests.post(f"{BASE_URL}/api/admin/contracts", json=payload, headers=admin_headers)
        assert r.status_code == 200
        contract_id = r.json()["contract_id"]
        
        # Add appendix
        appendix_payload = {
            "appendix_type": "scope",
            "title": "Leistungsumfang KI-Agenten",
            "content": {"description": "2 KI-Agenten für Vertrieb und Support"},
            "pricing": {"amount": 499, "currency": "EUR", "type": "monthly"}
        }
        r = requests.post(f"{BASE_URL}/api/admin/contracts/{contract_id}/appendices", 
                         json=appendix_payload, headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert "appendix_id" in data
        assert data["title"] == appendix_payload["title"]
        print(f"✅ Appendix added: {data['appendix_id']}")
    
    def test_admin_send_contract(self, admin_headers):
        """POST /api/admin/contracts/{id}/send - Send contract to customer."""
        # Create a test contract
        payload = {
            "customer": {"email": f"TEST_send_{secrets.token_hex(4)}@test.de", "name": "Send Test"},
            "tier_key": "starter",
            "contract_type": "standard"
        }
        r = requests.post(f"{BASE_URL}/api/admin/contracts", json=payload, headers=admin_headers)
        assert r.status_code == 200
        contract_id = r.json()["contract_id"]
        
        # Send contract
        r = requests.post(f"{BASE_URL}/api/admin/contracts/{contract_id}/send", 
                         json={}, headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        # Either sent=True or gate_blocked=True (legal gate)
        assert "sent" in data or "gate_blocked" in data
        if data.get("sent"):
            assert "contract_link" in data
            print(f"✅ Contract sent, link: {data['contract_link'][:50]}...")
        else:
            print(f"⚠️ Contract blocked by legal gate: {data.get('message', '')}")
    
    def test_admin_get_evidence(self, admin_headers):
        """GET /api/admin/contracts/{id}/evidence - Get evidence package."""
        # Use existing test contract
        r = requests.get(f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID}/evidence", headers=admin_headers)
        if r.status_code == 404:
            pytest.skip("Test contract not found")
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert "evidence" in data
        assert "count" in data
        print(f"✅ Evidence for contract: {data['count']} records")


class TestCustomerContractEndpoints:
    """Customer contract endpoints - requires customer JWT."""
    
    @pytest.fixture
    def customer_token(self, admin_headers):
        """Create a customer JWT via magic link flow simulation.
        Since we can't actually click magic links, we'll test with admin token
        for contracts that belong to the admin email, or skip if not possible."""
        # For testing, we need to create a contract for a customer and get their token
        # The customer portal uses magic links, so we'll test the endpoints that work
        # with the existing test data
        
        # Check if there's a contract for the test customer
        r = requests.get(f"{BASE_URL}/api/admin/contracts?customer_email={TEST_CUSTOMER_EMAIL}", 
                        headers=admin_headers)
        if r.status_code == 200 and r.json().get("contracts"):
            # We have contracts for test customer, but need customer JWT
            # For now, we'll test the admin endpoints and note that customer endpoints
            # require magic link auth
            return None
        return None
    
    def test_customer_contracts_requires_auth(self):
        """GET /api/customer/contracts - Requires authentication."""
        r = requests.get(f"{BASE_URL}/api/customer/contracts")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer contracts endpoint requires authentication")
    
    def test_customer_contract_detail_requires_auth(self):
        """GET /api/customer/contracts/{id} - Requires authentication."""
        r = requests.get(f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer contract detail requires authentication")
    
    def test_customer_accept_requires_auth(self):
        """POST /api/customer/contracts/{id}/accept - Requires authentication."""
        r = requests.post(f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}/accept", json={})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer accept endpoint requires authentication")
    
    def test_customer_decline_requires_auth(self):
        """POST /api/customer/contracts/{id}/decline - Requires authentication."""
        r = requests.post(f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}/decline", json={})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer decline endpoint requires authentication")
    
    def test_customer_change_request_requires_auth(self):
        """POST /api/customer/contracts/{id}/request-change - Requires authentication."""
        r = requests.post(f"{BASE_URL}/api/customer/contracts/{TEST_CONTRACT_ID}/request-change", json={})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer change request endpoint requires authentication")


class TestCustomerProjectEndpoints:
    """Customer project endpoints."""
    
    def test_customer_projects_requires_auth(self):
        """GET /api/customer/projects - Requires authentication."""
        r = requests.get(f"{BASE_URL}/api/customer/projects")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer projects endpoint requires authentication")
    
    def test_customer_project_detail_requires_auth(self):
        """GET /api/customer/projects/{id} - Requires authentication."""
        r = requests.get(f"{BASE_URL}/api/customer/projects/{TEST_PROJECT_ID}")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer project detail requires authentication")
    
    def test_customer_project_chat_requires_auth(self):
        """POST /api/customer/projects/{id}/chat - Requires authentication."""
        r = requests.post(f"{BASE_URL}/api/customer/projects/{TEST_PROJECT_ID}/chat", 
                         json={"content": "Test message"})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("✅ Customer project chat requires authentication")


class TestContractAcceptanceValidation:
    """Test contract acceptance validation logic via admin endpoints."""
    
    def test_contract_legal_modules_structure(self, admin_headers):
        """Verify legal modules are properly defined."""
        # Get any contract detail
        r = requests.get(f"{BASE_URL}/api/admin/contracts?limit=1", headers=admin_headers)
        if r.status_code != 200 or not r.json().get("contracts"):
            pytest.skip("No contracts available")
        
        contract_id = r.json()["contracts"][0]["contract_id"]
        r = requests.get(f"{BASE_URL}/api/admin/contracts/{contract_id}", headers=admin_headers)
        assert r.status_code == 200
        
        data = r.json()
        legal_modules = data.get("legal_module_definitions", [])
        
        # Verify required modules exist
        required_keys = {"agb", "datenschutz", "ki_hinweise", "zahlungsbedingungen"}
        found_keys = {m["key"] for m in legal_modules if m.get("required")}
        assert required_keys.issubset(found_keys), f"Missing required modules: {required_keys - found_keys}"
        
        # Verify structure
        for m in legal_modules:
            assert "key" in m
            assert "label" in m
            assert "required" in m
        
        print(f"✅ Legal modules validated: {len(legal_modules)} modules, {len(found_keys)} required")
    
    def test_contract_document_hash_exists(self, admin_headers):
        """Verify document hash is computed for contracts."""
        r = requests.get(f"{BASE_URL}/api/admin/contracts?limit=1", headers=admin_headers)
        if r.status_code != 200 or not r.json().get("contracts"):
            pytest.skip("No contracts available")
        
        contract_id = r.json()["contracts"][0]["contract_id"]
        r = requests.get(f"{BASE_URL}/api/admin/contracts/{contract_id}", headers=admin_headers)
        assert r.status_code == 200
        
        data = r.json()
        assert "document_hash" in data
        assert len(data["document_hash"]) == 64  # SHA256 hex
        print(f"✅ Document hash: {data['document_hash'][:16]}...")


class TestAdminProjectEndpoints:
    """Admin project endpoints for completeness."""
    
    def test_admin_list_projects(self, admin_headers):
        """GET /api/admin/projects - List projects."""
        r = requests.get(f"{BASE_URL}/api/admin/projects", headers=admin_headers)
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert "projects" in data
        print(f"✅ Admin projects list: {len(data['projects'])} projects")
    
    def test_admin_project_detail(self, admin_headers):
        """GET /api/admin/projects/{id} - Project detail."""
        r = requests.get(f"{BASE_URL}/api/admin/projects/{TEST_PROJECT_ID}", headers=admin_headers)
        if r.status_code == 404:
            pytest.skip("Test project not found")
        assert r.status_code == 200, f"Failed: {r.text}"
        data = r.json()
        assert data["project_id"] == TEST_PROJECT_ID
        print(f"✅ Project detail: {data.get('title', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
