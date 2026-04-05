"""
NeXify AI Master Chat Interface Tests - Iteration 65
Tests for Arcee AI + mem0 Brain integration in Admin Panel

Features tested:
- GET /api/admin/nexify-ai/status - Arcee and mem0 configuration status
- GET /api/admin/nexify-ai/conversations - List conversations (requires admin auth)
- POST /api/admin/nexify-ai/chat - Create conversation and stream response from Arcee AI
- POST /api/admin/nexify-ai/memory/search - Search mem0 brain
- DELETE /api/admin/nexify-ai/conversations/{id} - Delete a conversation
- Auth required - all NeXify AI endpoints return 401 without Bearer token
- Regression: Admin API keys at /api/admin/api-keys
- Regression: Legal pages /de/impressum returns 200
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://contract-os.preview.emergentagent.com')

# Admin credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token using form-encoded login."""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={ADMIN_EMAIL}&password={ADMIN_PASSWORD}"
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with Bearer token for authenticated requests."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestNeXifyAIAuth:
    """Test authentication requirements for NeXify AI endpoints."""
    
    def test_status_requires_auth(self):
        """GET /api/admin/nexify-ai/status returns 401 without token."""
        response = requests.get(f"{BASE_URL}/api/admin/nexify-ai/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_conversations_requires_auth(self):
        """GET /api/admin/nexify-ai/conversations returns 401 without token."""
        response = requests.get(f"{BASE_URL}/api/admin/nexify-ai/conversations")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_chat_requires_auth(self):
        """POST /api/admin/nexify-ai/chat returns 401 without token."""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/chat",
            json={"message": "test", "use_memory": False}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_memory_search_requires_auth(self):
        """POST /api/admin/nexify-ai/memory/search returns 401 without token."""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/memory/search",
            json={"query": "test", "top_k": 5}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestNeXifyAIStatus:
    """Test NeXify AI status endpoint."""
    
    def test_status_returns_arcee_config(self, auth_headers):
        """GET /api/admin/nexify-ai/status returns Arcee configuration."""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Status failed: {response.text}"
        data = response.json()
        
        # Verify Arcee configuration
        assert "arcee" in data, "Missing 'arcee' in status response"
        assert data["arcee"]["configured"] == True, "Arcee should be configured"
        assert data["arcee"]["model"] == "trinity-large-preview", f"Expected trinity-large-preview, got {data['arcee']['model']}"
        assert "url" in data["arcee"], "Missing Arcee URL"
        
    def test_status_returns_mem0_config(self, auth_headers):
        """GET /api/admin/nexify-ai/status returns mem0 configuration."""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify mem0 configuration
        assert "mem0" in data, "Missing 'mem0' in status response"
        assert data["mem0"]["configured"] == True, "mem0 should be configured"
        assert "user_id" in data["mem0"], "Missing mem0 user_id"
        assert "agent_id" in data["mem0"], "Missing mem0 agent_id"
        
    def test_status_returns_stats(self, auth_headers):
        """GET /api/admin/nexify-ai/status returns conversation stats."""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats
        assert "stats" in data, "Missing 'stats' in status response"
        assert "conversations" in data["stats"], "Missing conversations count"
        assert "messages" in data["stats"], "Missing messages count"
        assert isinstance(data["stats"]["conversations"], int)
        assert isinstance(data["stats"]["messages"], int)


class TestNeXifyAIConversations:
    """Test NeXify AI conversations CRUD."""
    
    def test_list_conversations(self, auth_headers):
        """GET /api/admin/nexify-ai/conversations returns list of conversations."""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/conversations",
            headers=auth_headers
        )
        assert response.status_code == 200, f"List conversations failed: {response.text}"
        data = response.json()
        
        assert "conversations" in data, "Missing 'conversations' in response"
        assert isinstance(data["conversations"], list), "conversations should be a list"
        
        # If there are conversations, verify structure
        if len(data["conversations"]) > 0:
            convo = data["conversations"][0]
            assert "conversation_id" in convo, "Missing conversation_id"
            assert "title" in convo, "Missing title"
            assert "created_at" in convo, "Missing created_at"
            assert "updated_at" in convo, "Missing updated_at"


class TestNeXifyAIChat:
    """Test NeXify AI chat streaming endpoint."""
    
    def test_chat_creates_conversation_and_streams(self, auth_headers):
        """POST /api/admin/nexify-ai/chat creates conversation and streams response."""
        # Send a simple test message
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/chat",
            headers=auth_headers,
            json={
                "message": "TEST_Hallo, was ist 2+2?",
                "conversation_id": None,
                "use_memory": False
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200, f"Chat failed: {response.status_code}"
        assert response.headers.get("content-type", "").startswith("text/event-stream"), \
            f"Expected text/event-stream, got {response.headers.get('content-type')}"
        
        # Read streaming response
        full_content = ""
        conversation_id = None
        got_done = False
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            try:
                import json
                data = json.loads(line[6:])
                if "content" in data:
                    full_content += data["content"]
                if "conversation_id" in data:
                    conversation_id = data["conversation_id"]
                if data.get("done"):
                    got_done = True
            except:
                continue
        
        # Verify we got a response
        assert len(full_content) > 0, "No content received from streaming response"
        assert conversation_id is not None, "No conversation_id received"
        assert conversation_id.startswith("nxc"), f"conversation_id should start with 'nxc', got {conversation_id}"
        assert got_done, "Did not receive 'done' signal"
        
        print(f"Chat response received: {len(full_content)} chars, conversation_id: {conversation_id}")
        
        # Store conversation_id for cleanup
        return conversation_id


class TestNeXifyAIMemorySearch:
    """Test NeXify AI memory search endpoint."""
    
    def test_memory_search(self, auth_headers):
        """POST /api/admin/nexify-ai/memory/search searches mem0 brain."""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/memory/search",
            headers=auth_headers,
            json={"query": "NeXify Automate pricing", "top_k": 5}
        )
        assert response.status_code == 200, f"Memory search failed: {response.text}"
        data = response.json()
        
        assert "memories" in data, "Missing 'memories' in response"
        assert "count" in data, "Missing 'count' in response"
        assert isinstance(data["memories"], list), "memories should be a list"
        assert isinstance(data["count"], int), "count should be an integer"
        
        print(f"Memory search returned {data['count']} memories")


class TestNeXifyAIConversationDelete:
    """Test NeXify AI conversation deletion."""
    
    def test_delete_conversation(self, auth_headers):
        """DELETE /api/admin/nexify-ai/conversations/{id} deletes a conversation."""
        # First create a test conversation
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/chat",
            headers=auth_headers,
            json={
                "message": "TEST_DELETE_Kurze Testfrage",
                "conversation_id": None,
                "use_memory": False
            },
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200, f"Chat failed: {response.status_code}"
        
        # Extract conversation_id from stream
        conversation_id = None
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            try:
                import json
                data = json.loads(line[6:])
                if "conversation_id" in data:
                    conversation_id = data["conversation_id"]
                    break
            except:
                continue
        
        assert conversation_id is not None, "No conversation_id received"
        
        # Now delete the conversation
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/nexify-ai/conversations/{conversation_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        assert data.get("deleted") == True, "Expected deleted: true"
        
        print(f"Successfully deleted conversation: {conversation_id}")


class TestRegressionApiKeys:
    """Regression test for Admin API keys feature."""
    
    def test_list_api_keys(self, auth_headers):
        """GET /api/admin/api-keys returns list of API keys."""
        response = requests.get(
            f"{BASE_URL}/api/admin/api-keys",
            headers=auth_headers
        )
        assert response.status_code == 200, f"List API keys failed: {response.text}"
        data = response.json()
        
        assert "keys" in data, "Missing 'keys' in response"
        assert isinstance(data["keys"], list), "keys should be a list"
        
        print(f"API keys count: {len(data['keys'])}")


class TestRegressionLegalPages:
    """Regression test for legal pages."""
    
    def test_impressum_de(self):
        """GET /de/impressum returns 200."""
        response = requests.get(f"{BASE_URL}/de/impressum")
        assert response.status_code == 200, f"Impressum DE failed: {response.status_code}"
        
    def test_impressum_nl(self):
        """GET /nl/impressum returns 200."""
        response = requests.get(f"{BASE_URL}/nl/impressum")
        assert response.status_code == 200, f"Impressum NL failed: {response.status_code}"
        
    def test_imprint_en(self):
        """GET /en/imprint returns 200."""
        response = requests.get(f"{BASE_URL}/en/imprint")
        assert response.status_code == 200, f"Imprint EN failed: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
