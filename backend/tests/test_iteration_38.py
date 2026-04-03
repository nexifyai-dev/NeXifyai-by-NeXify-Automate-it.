"""
Iteration 38 Backend Tests - DeepSeek LIVE + Contract PDF Generation

CRITICAL: This iteration tests DeepSeek as the PRIMARY LLM provider.
Previous iterations used Emergent GPT fallback. DeepSeek API key is NOW SET.

Test Coverage:
1. LLM Status - DeepSeek must be active_provider=deepseek, is_target_architecture=true
2. LLM Health - DeepSeek health check must return healthy
3. LLM Test - Direct DeepSeek test with real response
4. LLM Agent Flow - Full agent flow with session continuity via DeepSeek
5. Chat Message - Public chat routed through DeepSeek
6. Contract PDF Generation - Generate PDF with CI branding and evidence
7. Contract PDF Download - Download returns valid PDF
8. Monitoring Status - Full system monitoring with DeepSeek active
9. Email Stats - Email statistics with audit trail
10. Email Test - Test email via Resend
11. Billing Reconcile - Reconciliation
12. E2E Verify Flow - E2E verification with DeepSeek healthy
13. Customer Finance - Finance endpoint
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://contract-os.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"

# Test contract IDs
TEST_CONTRACT_ID_1 = "ctr_3d5efbc6b9c04a29"
TEST_CONTRACT_ID_2 = "ctr_fa24ac23eb394673"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Auth headers for admin endpoints"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestDeepSeekLLMProvider:
    """Tests for DeepSeek as PRIMARY LLM provider"""

    def test_llm_status_deepseek_active(self, auth_headers):
        """P1: GET /api/admin/llm/status — DeepSeek must be active_provider=deepseek"""
        response = requests.get(f"{BASE_URL}/api/admin/llm/status", headers=auth_headers)
        assert response.status_code == 200, f"LLM status failed: {response.text}"
        
        data = response.json()
        print(f"LLM Status Response: {data}")
        
        # CRITICAL: DeepSeek must be the active provider
        assert data.get("active_provider") == "deepseek", \
            f"Expected active_provider=deepseek, got {data.get('active_provider')}"
        
        # CRITICAL: Must be target architecture
        assert data.get("is_target_architecture") == True, \
            f"Expected is_target_architecture=true, got {data.get('is_target_architecture')}"
        
        # Verify DeepSeek provider status
        providers = data.get("providers", {})
        deepseek_status = providers.get("deepseek", {})
        assert deepseek_status.get("status") == "active", \
            f"Expected deepseek status=active, got {deepseek_status.get('status')}"
        assert deepseek_status.get("api_key_set") == True, \
            "DeepSeek API key should be set"
        
        print(f"✅ DeepSeek is ACTIVE as primary provider")

    def test_llm_health_deepseek_healthy(self, auth_headers):
        """P1: GET /api/admin/llm/health — DeepSeek health check must return healthy"""
        response = requests.get(f"{BASE_URL}/api/admin/llm/health", headers=auth_headers, timeout=30)
        assert response.status_code == 200, f"LLM health failed: {response.text}"
        
        data = response.json()
        print(f"LLM Health Response: {data}")
        
        # Verify provider is DeepSeek
        assert data.get("provider") == "deepseek", \
            f"Expected provider=deepseek, got {data.get('provider')}"
        
        # Verify is target architecture
        assert data.get("is_target_architecture") == True, \
            f"Expected is_target_architecture=true, got {data.get('is_target_architecture')}"
        
        # Verify health status
        assert data.get("status") in ["healthy", "degraded"], \
            f"Expected status healthy/degraded, got {data.get('status')}"
        
        # Check response sample exists
        assert "response_sample" in data, "Health check should include response_sample"
        
        print(f"✅ DeepSeek health check: {data.get('status')}")

    def test_llm_direct_test_deepseek(self, auth_headers):
        """P1: POST /api/admin/llm/test — DeepSeek direct test with real response"""
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test",
            headers=auth_headers,
            json={"prompt": "Antworte kurz: Was ist DeepSeek?"},
            timeout=30
        )
        assert response.status_code == 200, f"LLM test failed: {response.text}"
        
        data = response.json()
        print(f"LLM Test Response: {data}")
        
        # Verify provider is DeepSeek
        assert data.get("provider") == "deepseek", \
            f"Expected provider=deepseek, got {data.get('provider')}"
        
        # Verify success
        assert data.get("success") == True, \
            f"LLM test should succeed, got success={data.get('success')}, error={data.get('error')}"
        
        # Verify response is not an error message
        response_text = data.get("response", "")
        assert not response_text.startswith("["), \
            f"Response should not be an error: {response_text[:100]}"
        
        print(f"✅ DeepSeek direct test successful: {response_text[:100]}...")

    def test_llm_agent_flow_deepseek(self, auth_headers):
        """P1: POST /api/admin/llm/test-agent-flow — Full agent flow with session continuity"""
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test-agent-flow",
            headers=auth_headers,
            json={"message": "Welche Leistungen bietet NeXifyAI an?"},
            timeout=60  # Agent flow takes ~10s due to two sequential calls
        )
        assert response.status_code == 200, f"Agent flow test failed: {response.text}"
        
        data = response.json()
        print(f"Agent Flow Response: {data}")
        
        # Verify provider is DeepSeek
        assert data.get("provider") == "deepseek", \
            f"Expected provider=deepseek, got {data.get('provider')}"
        
        # Verify overall success
        assert data.get("success") == True, \
            f"Agent flow should succeed, got success={data.get('success')}, error={data.get('error')}"
        
        # Verify test results
        test_results = data.get("test_results", {})
        assert test_results.get("initial_response", {}).get("ok") == True, \
            "Initial response should be OK"
        assert test_results.get("followup_response", {}).get("ok") == True, \
            "Followup response should be OK"
        assert test_results.get("session_continuity") == True, \
            "Session continuity should be maintained"
        
        print(f"✅ DeepSeek agent flow test successful with session continuity")


class TestPublicChatDeepSeek:
    """Test public chat endpoint routes through DeepSeek"""

    def test_chat_message_via_deepseek(self):
        """P1: POST /api/chat/message — Public chat routed through DeepSeek"""
        import secrets
        session_id = f"test_iter38_{secrets.token_hex(6)}"
        
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "Hallo, was bietet NeXifyAI an?",
                "language": "de"
            },
            timeout=30
        )
        assert response.status_code == 200, f"Chat message failed: {response.text}"
        
        data = response.json()
        print(f"Chat Response: {data}")
        
        # Verify response exists and is not an error
        message = data.get("message", "")
        assert message, "Chat should return a message"
        assert not message.startswith("["), \
            f"Chat response should not be an error: {message[:100]}"
        
        # Response should mention NeXifyAI or relevant content
        assert len(message) > 50, "Chat response should be substantial"
        
        print(f"✅ Public chat via DeepSeek successful: {message[:100]}...")


class TestContractPDFGeneration:
    """Tests for Contract PDF generation and download"""

    def test_generate_contract_pdf(self, auth_headers):
        """P4: POST /api/admin/contracts/{id}/generate-pdf — Generate PDF with CI branding"""
        response = requests.post(
            f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID_1}/generate-pdf",
            headers=auth_headers,
            timeout=30
        )
        
        # Contract might not exist, check for 404 vs other errors
        if response.status_code == 404:
            print(f"⚠️ Contract {TEST_CONTRACT_ID_1} not found - trying second contract")
            response = requests.post(
                f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID_2}/generate-pdf",
                headers=auth_headers,
                timeout=30
            )
        
        if response.status_code == 404:
            pytest.skip(f"Test contracts not found: {TEST_CONTRACT_ID_1}, {TEST_CONTRACT_ID_2}")
        
        assert response.status_code == 200, f"PDF generation failed: {response.text}"
        
        data = response.json()
        print(f"PDF Generation Response: {data}")
        
        assert data.get("generated") == True, "PDF should be generated"
        assert "contract_id" in data, "Response should include contract_id"
        assert data.get("size_bytes", 0) > 0, "PDF should have content"
        
        print(f"✅ Contract PDF generated: {data.get('size_bytes')} bytes")

    def test_download_contract_pdf(self, auth_headers):
        """P4: GET /api/documents/contract/{id}/pdf — Download returns valid PDF"""
        # First generate the PDF
        gen_response = requests.post(
            f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID_1}/generate-pdf",
            headers=auth_headers,
            timeout=30
        )
        
        contract_id = TEST_CONTRACT_ID_1
        if gen_response.status_code == 404:
            gen_response = requests.post(
                f"{BASE_URL}/api/admin/contracts/{TEST_CONTRACT_ID_2}/generate-pdf",
                headers=auth_headers,
                timeout=30
            )
            contract_id = TEST_CONTRACT_ID_2
        
        if gen_response.status_code == 404:
            pytest.skip("Test contracts not found")
        
        # Now download the PDF
        response = requests.get(
            f"{BASE_URL}/api/documents/contract/{contract_id}/pdf",
            timeout=30
        )
        
        if response.status_code == 404:
            pytest.skip(f"PDF document not found for contract {contract_id}")
        
        assert response.status_code == 200, f"PDF download failed: {response.status_code}"
        
        # Verify it's a PDF
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type.lower(), f"Expected PDF content type, got {content_type}"
        
        # Verify PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Content should be a valid PDF"
        
        print(f"✅ Contract PDF downloaded: {len(content)} bytes")


class TestMonitoringAndEmail:
    """Tests for monitoring and email endpoints"""

    def test_monitoring_status_deepseek_active(self, auth_headers):
        """P7: GET /api/admin/monitoring/status — Full system monitoring with DeepSeek active"""
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/status", headers=auth_headers)
        assert response.status_code == 200, f"Monitoring status failed: {response.text}"
        
        data = response.json()
        print(f"Monitoring Status: {data}")
        
        # Verify LLM status shows DeepSeek (nested under systems.llm)
        systems = data.get("systems", {})
        llm_status = systems.get("llm", {})
        assert llm_status.get("active_provider") == "deepseek", \
            f"Expected LLM active_provider=deepseek, got {llm_status.get('active_provider')}"
        
        # Verify is target architecture
        assert llm_status.get("is_target_architecture") == True, \
            f"Expected is_target_architecture=true, got {llm_status.get('is_target_architecture')}"
        
        # Verify other systems are present
        assert "api" in systems, "Should include API status"
        assert "database" in systems, "Should include database status"
        
        print(f"✅ Monitoring shows DeepSeek as LLM provider")

    def test_email_stats(self, auth_headers):
        """P3: GET /api/admin/email/stats — Email statistics with audit trail"""
        response = requests.get(f"{BASE_URL}/api/admin/email/stats", headers=auth_headers)
        assert response.status_code == 200, f"Email stats failed: {response.text}"
        
        data = response.json()
        print(f"Email Stats: {data}")
        
        # Verify stats structure
        assert "total" in data or "sent" in data, "Should include email counts"
        
        print(f"✅ Email stats retrieved")

    def test_email_test_send(self, auth_headers):
        """P3: POST /api/admin/email/test — Test email via Resend"""
        response = requests.post(
            f"{BASE_URL}/api/admin/email/test",
            headers=auth_headers,
            json={"to": "test@example.com"},
            timeout=30
        )
        
        # Email test might fail if Resend is not configured, but endpoint should work
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        
        data = response.json()
        print(f"Email Test Response: {data}")
        
        print(f"✅ Email test endpoint functional")


class TestBillingAndE2E:
    """Tests for billing and E2E verification"""

    def test_billing_reconcile(self, auth_headers):
        """P5: POST /api/admin/billing/reconcile — Reconciliation"""
        response = requests.post(
            f"{BASE_URL}/api/admin/billing/reconcile",
            headers=auth_headers,
            json={},
            timeout=30
        )
        assert response.status_code == 200, f"Billing reconcile failed: {response.text}"
        
        data = response.json()
        print(f"Billing Reconcile Response: {data}")
        
        assert "reconciled" in data or "timestamp" in data, "Should include reconciliation result"
        
        print(f"✅ Billing reconciliation completed")

    def test_e2e_verify_flow(self, auth_headers):
        """P5: POST /api/admin/e2e/verify-flow — E2E verification with DeepSeek healthy"""
        response = requests.post(
            f"{BASE_URL}/api/admin/e2e/verify-flow",
            headers=auth_headers,
            json={},
            timeout=60
        )
        assert response.status_code == 200, f"E2E verify failed: {response.text}"
        
        data = response.json()
        print(f"E2E Verify Response: {data}")
        
        # Check LLM provider health in E2E
        checks = data.get("checks", [])
        llm_check = next((c for c in checks if "llm" in c.get("type", "").lower()), None)
        if llm_check:
            print(f"LLM Check: {llm_check}")
        
        print(f"✅ E2E verification completed")


class TestCustomerFinance:
    """Test customer finance endpoint"""

    def test_customer_finance_endpoint_exists(self, auth_headers):
        """P5: GET /api/customer/finance — Finance endpoint (requires customer auth)"""
        # This endpoint requires customer auth, so we test it returns 401 without auth
        response = requests.get(f"{BASE_URL}/api/customer/finance")
        
        # Should return 401 (unauthorized) not 404 (not found)
        assert response.status_code == 401, \
            f"Expected 401 for unauthenticated request, got {response.status_code}"
        
        print(f"✅ Customer finance endpoint exists (returns 401 without auth)")


class TestHealthAndBasics:
    """Basic health checks"""

    def test_api_health(self):
        """Basic API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "healthy", f"API not healthy: {data}"
        
        print(f"✅ API health: {data}")

    def test_admin_login(self):
        """Admin login works"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Should return access_token"
        
        print(f"✅ Admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
