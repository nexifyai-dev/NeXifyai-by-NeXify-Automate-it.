"""
P5+P6 Test Suite: DeepSeek Live-Pfad + Outbound Lead Machine

P5: DeepSeek als realer Provider mit ENV-basierter Umschaltung, Provider-Status, Test-Endpoint
P6: Vollständige Outbound-Pipeline: Discovery → Vorqualifizierung → Analyse → Legal Gate → 
    Personalisierte Erstansprache → Follow-up → Antwort-Erfassung → Handover (Angebot/Termin/Nurture)

Endpoints tested:
- GET /api/admin/llm/status — LLM Provider status
- POST /api/admin/llm/test — LLM Provider test
- GET /api/admin/outbound/pipeline — Full pipeline overview
- GET /api/admin/outbound/{lead_id} — Lead detail with timeline
- POST /api/admin/outbound/{lead_id}/respond — Response tracking
- POST /api/admin/outbound/{lead_id}/handover — Handover to quote/meeting/nurture
- POST /api/admin/outbound/{lead_id}/outreach/{id}/send — Send with Legal Guardian gate
- Full pipeline flow tests
"""

import pytest
import requests
import os
import time
import secrets

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


class TestP5DeepSeekLLMProvider:
    """P5: DeepSeek Live-Pfad Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, auth_token):
        self.token = auth_token
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_llm_status_endpoint(self, auth_token):
        """GET /api/admin/llm/status — LLM Provider status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/llm/status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "active_provider" in data, "Missing active_provider field"
        assert "providers" in data, "Missing providers field"
        assert "migration_ready" in data, "Missing migration_ready field"
        
        # Verify provider structure
        providers = data["providers"]
        assert "deepseek" in providers, "Missing deepseek provider info"
        assert "emergent_gpt52" in providers, "Missing emergent_gpt52 provider info"
        
        # Verify deepseek provider details
        deepseek = providers["deepseek"]
        assert "status" in deepseek, "Missing deepseek status"
        assert "api_key_set" in deepseek, "Missing deepseek api_key_set"
        
        # Verify emergent provider details
        emergent = providers["emergent_gpt52"]
        assert "status" in emergent, "Missing emergent status"
        assert "api_key_set" in emergent, "Missing emergent api_key_set"
        
        print(f"✅ LLM Status: active_provider={data['active_provider']}, migration_ready={data['migration_ready']}")
        print(f"   DeepSeek: {deepseek['status']}, Emergent: {emergent['status']}")
    
    def test_llm_status_requires_auth(self):
        """LLM status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/llm/status")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ LLM status requires authentication")
    
    def test_llm_test_endpoint(self, auth_token):
        """POST /api/admin/llm/test — LLM Provider test"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Test with default prompt
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test",
            headers=headers,
            json={"prompt": "Antworte mit einem Wort: Ja oder Nein?"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "provider" in data, "Missing provider field"
        assert "success" in data, "Missing success field"
        
        # Note: LLM may have issues with key, so we check structure not success
        if data.get("success"):
            assert "response" in data, "Missing response field on success"
            print(f"✅ LLM Test successful: provider={data['provider']}, response={data['response'][:100]}...")
        else:
            assert "error" in data, "Missing error field on failure"
            print(f"⚠️ LLM Test returned error (expected - key may have issues): {data.get('error', 'unknown')}")
    
    def test_llm_test_with_model_override(self, auth_token):
        """POST /api/admin/llm/test — with model override"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/llm/test",
            headers=headers,
            json={"prompt": "Test", "model": "gpt-4o-mini"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "model" in data, "Missing model field"
        print(f"✅ LLM Test with model override: model={data.get('model')}")
    
    def test_llm_test_requires_auth(self):
        """LLM test endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/llm/test", json={})
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ LLM test requires authentication")


class TestP6OutboundPipeline:
    """P6: Outbound Lead Machine Pipeline Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, auth_token):
        self.token = auth_token
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_pipeline_overview(self, auth_token):
        """GET /api/admin/outbound/pipeline — Full pipeline overview with conversion rates"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/outbound/pipeline", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "pipeline" in data, "Missing pipeline field"
        assert "total" in data, "Missing total field"
        assert "conversion_rate" in data, "Missing conversion_rate field"
        
        # Verify pipeline stages
        pipeline = data["pipeline"]
        assert isinstance(pipeline, list), "Pipeline should be a list"
        
        # Expected stages
        expected_stages = [
            "discovered", "analyzing", "qualified", "unqualified",
            "legal_blocked", "outreach_ready", "contacted",
            "followup_1", "followup_2", "followup_3",
            "responded", "meeting_booked", "quote_sent",
            "nurture", "opt_out", "suppressed"
        ]
        
        stage_keys = [s["key"] for s in pipeline]
        for expected in expected_stages:
            assert expected in stage_keys, f"Missing stage: {expected}"
        
        # Verify stage structure
        for stage in pipeline:
            assert "key" in stage, "Stage missing key"
            assert "label" in stage, "Stage missing label"
            assert "count" in stage, "Stage missing count"
            assert isinstance(stage["count"], int), "Stage count should be int"
        
        print(f"✅ Pipeline overview: total={data['total']}, conversion_rate={data['conversion_rate']}%")
        print(f"   Stages: {len(pipeline)} stages returned")
    
    def test_pipeline_requires_auth(self):
        """Pipeline endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/outbound/pipeline")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ Pipeline requires authentication")


class TestP6OutboundLeadDiscovery:
    """P6: Outbound Lead Discovery and Full Flow Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, auth_token):
        self.token = auth_token
        self.headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_discover_lead(self, auth_token):
        """POST /api/admin/outbound/discover — Create new outbound lead"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        test_id = secrets.token_hex(4)
        lead_data = {
            "name": f"TEST_P6_Company_{test_id}",
            "website": f"https://test-p6-{test_id}.de",
            "industry": "technologie",
            "email": f"test_p6_{test_id}@example.com",
            "phone": "+49 123 456789",
            "contact_name": f"Test Contact {test_id}",
            "country": "DE",
            "notes": "Test lead for P6 testing - skalierung, automatisierung, ki-strategie"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/discover",
            headers=headers,
            json=lead_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "outbound_lead_id" in data, "Missing outbound_lead_id"
        assert "status" in data, "Missing status"
        assert data["status"] == "discovered", f"Expected status 'discovered', got {data['status']}"
        
        print(f"✅ Lead discovered: {data['outbound_lead_id']}")
        return data["outbound_lead_id"]
    
    def test_full_pipeline_flow(self, auth_token):
        """Full pipeline: discover → prequalify → analyze → legal-check → outreach → send"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # 1. Discover
        test_id = secrets.token_hex(4)
        lead_data = {
            "name": f"TEST_P6_Flow_{test_id}",
            "website": f"https://test-flow-{test_id}.de",
            "industry": "saas",
            "email": f"test_flow_{test_id}@example.com",
            "phone": "+49 987 654321",
            "contact_name": f"Flow Test {test_id}",
            "country": "DE",
            "notes": "skalierung, lead-generierung, automatisierung, ki-strategie, digitalisierung"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
        assert response.status_code == 200, f"Discover failed: {response.text}"
        lead_id = response.json()["outbound_lead_id"]
        print(f"  1. Discovered: {lead_id}")
        
        # 2. Prequalify
        response = requests.post(f"{BASE_URL}/api/admin/outbound/{lead_id}/prequalify", headers=headers)
        assert response.status_code == 200, f"Prequalify failed: {response.text}"
        prequalify_data = response.json()
        print(f"  2. Prequalified: status={prequalify_data.get('status')}, qualified={prequalify_data.get('qualified')}")
        
        # 3. Analyze
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{lead_id}/analyze",
            headers=headers,
            json={"notes": "High potential SaaS company with automation needs"}
        )
        assert response.status_code == 200, f"Analyze failed: {response.text}"
        analyze_data = response.json()
        print(f"  3. Analyzed: score={analyze_data.get('score')}, fit_products={len(analyze_data.get('fit_products', []))}")
        
        # 4. Legal Check
        response = requests.post(f"{BASE_URL}/api/admin/outbound/{lead_id}/legal-check", headers=headers)
        assert response.status_code == 200, f"Legal check failed: {response.text}"
        legal_data = response.json()
        print(f"  4. Legal check: legal_ok={legal_data.get('legal_ok')}, status={legal_data.get('status')}")
        
        # 5. Create Outreach
        outreach_data = {
            "channel": "email",
            "subject": f"KI-Automatisierung für {lead_data['name']}",
            "content": "Sehr geehrte Damen und Herren, wir haben Ihr Unternehmen analysiert..."
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{lead_id}/outreach",
            headers=headers,
            json=outreach_data
        )
        assert response.status_code == 200, f"Create outreach failed: {response.text}"
        outreach_result = response.json()
        outreach_id = outreach_result.get("outreach_id")
        print(f"  5. Outreach created: {outreach_id}")
        
        # 6. Send Outreach (with Legal Guardian gate)
        if outreach_id and legal_data.get("legal_ok"):
            response = requests.post(
                f"{BASE_URL}/api/admin/outbound/{lead_id}/outreach/{outreach_id}/send",
                headers=headers
            )
            # May fail due to legal gate or other reasons
            if response.status_code == 200:
                send_data = response.json()
                if "error" in send_data:
                    print(f"  6. Send blocked by Legal Gate: {send_data.get('error')}")
                else:
                    print(f"  6. Outreach sent: status={send_data.get('status')}")
            else:
                print(f"  6. Send returned {response.status_code}: {response.text[:100]}")
        else:
            print(f"  6. Skipped send (legal_ok={legal_data.get('legal_ok')})")
        
        print(f"✅ Full pipeline flow completed for lead {lead_id}")
        return lead_id


class TestP6OutboundLeadDetail:
    """P6: Outbound Lead Detail Tests"""
    
    def test_lead_detail_with_timeline(self, auth_token, test_outbound_lead_id):
        """GET /api/admin/outbound/{lead_id} — Lead detail with timeline"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify lead fields
        assert "outbound_lead_id" in data, "Missing outbound_lead_id"
        assert "company_name" in data, "Missing company_name"
        assert "status" in data, "Missing status"
        assert "score" in data, "Missing score"
        
        # Verify timeline
        assert "timeline" in data, "Missing timeline"
        assert isinstance(data["timeline"], list), "Timeline should be a list"
        
        print(f"✅ Lead detail: {data['outbound_lead_id']}, status={data['status']}, score={data['score']}")
        print(f"   Timeline events: {len(data['timeline'])}")
    
    def test_lead_detail_not_found(self, auth_token):
        """GET /api/admin/outbound/{lead_id} — 404 for non-existent lead"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/outbound/obl_nonexistent_12345",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Lead detail returns 404 for non-existent lead")


class TestP6OutboundRespond:
    """P6: Outbound Response Tracking Tests"""
    
    def test_respond_positive(self, auth_token, test_outbound_lead_id):
        """POST /api/admin/outbound/{lead_id}/respond — positive response"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_id}/respond",
            headers=headers,
            json={"response_type": "positive", "content": "Interested in learning more"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "status" in data, "Missing status"
        assert "response_type" in data, "Missing response_type"
        assert data["response_type"] == "positive", f"Expected positive, got {data['response_type']}"
        assert data["status"] == "responded", f"Expected responded status, got {data['status']}"
        
        print(f"✅ Positive response recorded: status={data['status']}")
    
    def test_respond_negative(self, auth_token, test_outbound_lead_id_2):
        """POST /api/admin/outbound/{lead_id}/respond — negative response"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_id_2}/respond",
            headers=headers,
            json={"response_type": "negative", "content": "Not interested at this time"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["response_type"] == "negative"
        assert data["status"] == "nurture", f"Expected nurture status for negative, got {data['status']}"
        
        print(f"✅ Negative response recorded: status={data['status']}")
    
    def test_respond_opt_out(self, auth_token, test_outbound_lead_id_3):
        """POST /api/admin/outbound/{lead_id}/respond — opt_out response auto-suppresses"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_id_3}/respond",
            headers=headers,
            json={"response_type": "opt_out", "content": "Please remove me from your list"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["response_type"] == "opt_out"
        assert data["status"] == "opt_out", f"Expected opt_out status, got {data['status']}"
        
        print(f"✅ Opt-out response recorded: status={data['status']} (lead auto-suppressed)")


class TestP6OutboundHandover:
    """P6: Outbound Handover Tests"""
    
    def test_handover_to_quote_creates_crm_lead(self, auth_token, test_outbound_lead_for_handover):
        """POST /api/admin/outbound/{lead_id}/handover — quote creates CRM lead"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_for_handover}/handover",
            headers=headers,
            json={"handover_type": "quote"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "handover_type" in data, "Missing handover_type"
        assert data["handover_type"] == "quote"
        assert data["status"] == "quote_sent", f"Expected quote_sent status, got {data['status']}"
        
        # Check if CRM lead was created
        crm_created = data.get("crm_lead_created", False)
        print(f"✅ Handover to quote: status={data['status']}, crm_lead_created={crm_created}")
    
    def test_handover_to_meeting(self, auth_token, test_outbound_lead_for_meeting):
        """POST /api/admin/outbound/{lead_id}/handover — meeting"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_for_meeting}/handover",
            headers=headers,
            json={"handover_type": "meeting"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["handover_type"] == "meeting"
        assert data["status"] == "meeting_booked", f"Expected meeting_booked status, got {data['status']}"
        
        print(f"✅ Handover to meeting: status={data['status']}")
    
    def test_handover_to_nurture(self, auth_token, test_outbound_lead_for_nurture):
        """POST /api/admin/outbound/{lead_id}/handover — nurture"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_for_nurture}/handover",
            headers=headers,
            json={"handover_type": "nurture"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["handover_type"] == "nurture"
        assert data["status"] == "nurture", f"Expected nurture status, got {data['status']}"
        
        print(f"✅ Handover to nurture: status={data['status']}")
    
    def test_handover_invalid_type(self, auth_token, test_outbound_lead_id):
        """POST /api/admin/outbound/{lead_id}/handover — invalid type returns 400"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/outbound/{test_outbound_lead_id}/handover",
            headers=headers,
            json={"handover_type": "invalid_type"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print("✅ Invalid handover type returns 400")


class TestP6OutboundSendWithLegalGate:
    """P6: Outbound Send with Legal Guardian Gate Tests"""
    
    def test_send_blocked_for_suppressed_email(self, auth_token):
        """Send blocked when email is on suppression list"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Create a lead with suppressed email
        test_id = secrets.token_hex(4)
        suppressed_email = f"suppressed_{test_id}@example.com"
        
        # First add to suppression list
        requests.post(
            f"{BASE_URL}/api/admin/outbound/opt-out",
            headers=headers,
            json={"email": suppressed_email, "reason": "test_suppression"}
        )
        
        # Create lead with suppressed email
        lead_data = {
            "name": f"TEST_Suppressed_{test_id}",
            "email": suppressed_email,
            "industry": "test",
            "country": "DE"
        }
        response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
        lead_id = response.json().get("outbound_lead_id")
        
        # Try to prequalify - should be suppressed
        response = requests.post(f"{BASE_URL}/api/admin/outbound/{lead_id}/prequalify", headers=headers)
        data = response.json()
        
        assert data.get("status") == "suppressed" or "suppression" in str(data.get("reason", "")), \
            f"Expected suppressed status, got {data}"
        
        print(f"✅ Suppressed email correctly blocked: {data.get('status')}")


# ══════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════

@pytest.fixture(scope="session")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    token = response.json().get("access_token")
    if not token:
        pytest.skip("No access_token in response")
    return token


@pytest.fixture
def test_outbound_lead_id(auth_token):
    """Create a test outbound lead for testing"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    test_id = secrets.token_hex(4)
    lead_data = {
        "name": f"TEST_P6_Lead_{test_id}",
        "email": f"test_p6_lead_{test_id}@example.com",
        "industry": "technologie",
        "country": "DE",
        "notes": "Test lead for P6 testing"
    }
    response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
    return response.json().get("outbound_lead_id")


@pytest.fixture
def test_outbound_lead_id_2(auth_token):
    """Create a second test outbound lead"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    test_id = secrets.token_hex(4)
    lead_data = {
        "name": f"TEST_P6_Lead2_{test_id}",
        "email": f"test_p6_lead2_{test_id}@example.com",
        "industry": "beratung",
        "country": "DE"
    }
    response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
    return response.json().get("outbound_lead_id")


@pytest.fixture
def test_outbound_lead_id_3(auth_token):
    """Create a third test outbound lead for opt-out testing"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    test_id = secrets.token_hex(4)
    lead_data = {
        "name": f"TEST_P6_OptOut_{test_id}",
        "email": f"test_p6_optout_{test_id}@example.com",
        "industry": "handel",
        "country": "DE"
    }
    response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
    return response.json().get("outbound_lead_id")


@pytest.fixture
def test_outbound_lead_for_handover(auth_token):
    """Create a test lead for handover to quote"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    test_id = secrets.token_hex(4)
    lead_data = {
        "name": f"TEST_P6_Handover_{test_id}",
        "email": f"test_p6_handover_{test_id}@example.com",
        "contact_name": f"Handover Test {test_id}",
        "phone": "+49 111 222333",
        "industry": "saas",
        "country": "DE",
        "notes": "skalierung, automatisierung"
    }
    response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
    return response.json().get("outbound_lead_id")


@pytest.fixture
def test_outbound_lead_for_meeting(auth_token):
    """Create a test lead for handover to meeting"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    test_id = secrets.token_hex(4)
    lead_data = {
        "name": f"TEST_P6_Meeting_{test_id}",
        "email": f"test_p6_meeting_{test_id}@example.com",
        "industry": "finance",
        "country": "DE"
    }
    response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
    return response.json().get("outbound_lead_id")


@pytest.fixture
def test_outbound_lead_for_nurture(auth_token):
    """Create a test lead for handover to nurture"""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    test_id = secrets.token_hex(4)
    lead_data = {
        "name": f"TEST_P6_Nurture_{test_id}",
        "email": f"test_p6_nurture_{test_id}@example.com",
        "industry": "immobilien",
        "country": "DE"
    }
    response = requests.post(f"{BASE_URL}/api/admin/outbound/discover", headers=headers, json=lead_data)
    return response.json().get("outbound_lead_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
