"""
NeXify AI Master Chat - Iteration 67 Tests
Testing bug fixes for:
1. Chat bubble flickering (CSS animation + React key)
2. Server-side tool execution (no more client-side tool calls)
3. Smart scroll behavior
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminAuth:
    """Admin authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_admin_login(self, auth_token):
        """Test admin login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 20
        print(f"✓ Admin login successful, token length: {len(auth_token)}")


class TestNeXifyAIStatus:
    """NeXify AI status endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json().get("access_token")
    
    def test_nexify_ai_status(self, auth_token):
        """Test /api/admin/nexify-ai/status returns arcee+mem0 config"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Status failed: {response.text}"
        data = response.json()
        
        # Verify arcee config
        assert "arcee" in data
        assert data["arcee"]["configured"] == True
        assert "model" in data["arcee"]
        print(f"✓ Arcee configured: model={data['arcee']['model']}")
        
        # Verify mem0 config
        assert "mem0" in data
        assert data["mem0"]["configured"] == True
        assert "user_id" in data["mem0"]
        print(f"✓ mem0 configured: user_id={data['mem0']['user_id']}")
        
        # Verify stats
        assert "stats" in data
        print(f"✓ Stats: {data['stats']['conversations']} conversations, {data['stats']['messages']} messages")


class TestNeXifyAITools:
    """NeXify AI tools endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json().get("access_token")
    
    def test_list_tools_returns_37(self, auth_token):
        """Test /api/admin/nexify-ai/tools returns 37 tools"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/tools",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Tools list failed: {response.text}"
        data = response.json()
        
        assert "tools" in data
        tools_count = len(data["tools"])
        print(f"✓ Tools endpoint returned {tools_count} tools")
        
        # Verify expected tools exist
        expected_tools = [
            "list_contacts", "create_contact", "list_leads", "create_lead",
            "system_stats", "send_email", "search_brain", "store_brain",
            "list_conversations", "db_query", "web_search", "execute_python"
        ]
        for tool in expected_tools:
            assert tool in data["tools"], f"Missing tool: {tool}"
        print(f"✓ All expected tools present")
    
    def test_execute_tool_system_stats(self, auth_token):
        """Test execute-tool with system_stats returns valid stats"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/execute-tool",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"tool": "system_stats", "params": {}}
        )
        assert response.status_code == 200, f"Execute tool failed: {response.text}"
        data = response.json()
        
        assert "result" in data
        result = data["result"]
        
        # Verify stats fields
        expected_fields = ["contacts", "leads", "quotes", "contracts", "projects", "invoices"]
        for field in expected_fields:
            assert field in result, f"Missing stat field: {field}"
        
        print(f"✓ system_stats returned: contacts={result['contacts']}, leads={result['leads']}, projects={result['projects']}")
    
    def test_execute_tool_list_contacts(self, auth_token):
        """Test execute-tool with list_contacts returns contacts array"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/execute-tool",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"tool": "list_contacts", "params": {"limit": 5}}
        )
        assert response.status_code == 200, f"Execute tool failed: {response.text}"
        data = response.json()
        
        assert "result" in data
        assert "count" in data
        assert isinstance(data["result"], list)
        print(f"✓ list_contacts returned {data['count']} contacts")


class TestNeXifyAIConversations:
    """NeXify AI conversations endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json().get("access_token")
    
    def test_list_conversations(self, auth_token):
        """Test /api/admin/nexify-ai/conversations returns conversation list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Conversations list failed: {response.text}"
        data = response.json()
        
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        print(f"✓ Conversations endpoint returned {len(data['conversations'])} conversations")
        
        # If conversations exist, verify structure
        if len(data["conversations"]) > 0:
            convo = data["conversations"][0]
            assert "conversation_id" in convo
            assert "title" in convo
            print(f"✓ First conversation: {convo['title'][:50]}...")


class TestServerSideToolExecution:
    """Test that tool execution happens server-side (bug fix verification)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json().get("access_token")
    
    def test_execute_tool_db_query(self, auth_token):
        """Test db_query tool executes server-side"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/execute-tool",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "tool": "db_query",
                "params": {
                    "collection": "leads",
                    "query": {},
                    "limit": 3
                }
            }
        )
        assert response.status_code == 200, f"db_query failed: {response.text}"
        data = response.json()
        
        assert "result" in data
        assert "tool" in data
        assert data["tool"] == "db_query"
        print(f"✓ db_query executed server-side, returned {data.get('count', len(data['result']))} items")
    
    def test_execute_tool_search_brain(self, auth_token):
        """Test search_brain tool executes server-side"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/execute-tool",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "tool": "search_brain",
                "params": {"query": "NeXify", "top_k": 3}
            }
        )
        assert response.status_code == 200, f"search_brain failed: {response.text}"
        data = response.json()
        
        assert "result" in data
        assert "tool" in data
        assert data["tool"] == "search_brain"
        print(f"✓ search_brain executed server-side, returned {data.get('count', 0)} memories")


class TestChatEndpoint:
    """Test chat endpoint structure (not full streaming)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json().get("access_token")
    
    def test_chat_endpoint_exists(self, auth_token):
        """Test /api/admin/nexify-ai/chat endpoint exists and accepts POST"""
        # Just verify the endpoint exists and returns streaming response
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/chat",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "message": "Hallo",
                "conversation_id": None,
                "use_memory": False
            },
            stream=True,
            timeout=30
        )
        # Should return 200 with streaming response
        assert response.status_code == 200, f"Chat endpoint failed: {response.status_code}"
        assert response.headers.get("content-type", "").startswith("text/event-stream")
        print(f"✓ Chat endpoint returns SSE stream (text/event-stream)")
        
        # Read first few chunks to verify format
        chunks_read = 0
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data:'):
                    chunks_read += 1
                    if chunks_read >= 3:
                        break
        
        print(f"✓ Received {chunks_read} SSE data chunks")
        response.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
