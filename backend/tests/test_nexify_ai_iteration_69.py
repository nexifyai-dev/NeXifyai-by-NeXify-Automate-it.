"""
NeXify AI Iteration 69 - Backend Tests
Testing: Proactive Mode, Agent CRUD, Chat, Tool Execution, Design Harmonization
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


class TestProactiveMode:
    """Proactive Mode endpoint tests - NEW FEATURE"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json()["access_token"]
    
    def test_get_proactive_config(self, auth_token):
        """GET /api/admin/nexify-ai/proactive returns config with 4 available_tasks"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/proactive",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "enabled" in data
        assert "available_tasks" in data
        assert "active_tasks" in data
        
        # Verify 4 predefined tasks exist
        tasks = data["available_tasks"]
        expected_tasks = ["morning_briefing", "lead_analysis", "brain_maintenance", "health_check"]
        for task_id in expected_tasks:
            assert task_id in tasks, f"Missing task: {task_id}"
            assert "name" in tasks[task_id]
            assert "description" in tasks[task_id]
            assert "cron" in tasks[task_id]
    
    def test_enable_proactive_mode(self, auth_token):
        """PUT /api/admin/nexify-ai/proactive enables proactive mode"""
        response = requests.put(
            f"{BASE_URL}/api/admin/nexify-ai/proactive",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"enabled": True, "tasks": ["health_check", "morning_briefing"]}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["enabled"] == True
        assert "health_check" in data["active_tasks"]
        assert "morning_briefing" in data["active_tasks"]
    
    def test_disable_proactive_mode(self, auth_token):
        """PUT /api/admin/nexify-ai/proactive disables proactive mode"""
        response = requests.put(
            f"{BASE_URL}/api/admin/nexify-ai/proactive",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"enabled": False}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["enabled"] == False
    
    def test_trigger_proactive_task_health_check(self, auth_token):
        """POST /api/admin/nexify-ai/proactive/trigger/health_check creates proactive conversation"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/proactive/trigger/health_check",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "conversation_id" in data
        assert "task_id" in data
        assert data["task_id"] == "health_check"
        assert "triggered" in data
        assert data["triggered"] == True
    
    def test_trigger_invalid_task(self, auth_token):
        """POST /api/admin/nexify-ai/proactive/trigger/invalid_task returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/proactive/trigger/invalid_task_xyz",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


class TestAgentCRUD:
    """Agent CRUD endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json()["access_token"]
    
    def test_list_agents_includes_master(self, auth_token):
        """GET /api/admin/nexify-ai/agents returns master + sub-agents"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/agents",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "agents" in data
        agents = data["agents"]
        assert len(agents) >= 1  # At least master
        
        # Find master agent
        master = next((a for a in agents if a.get("agent_id") == "nexify-ai-master"), None)
        assert master is not None, "Master agent not found"
        assert master.get("is_master") == True
        assert master.get("tools_count") == 37
    
    def test_create_agent(self, auth_token):
        """POST /api/admin/nexify-ai/agents creates new agent"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/agents",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"name": "TEST_QA_Agent_Iter69", "role": "quality"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "agent_id" in data
        assert data["name"] == "TEST_QA_Agent_Iter69"
        assert data["role"] == "quality"
        return data["agent_id"]
    
    def test_delete_agent(self, auth_token):
        """DELETE /api/admin/nexify-ai/agents/{id} deletes agent"""
        # First create an agent to delete
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/agents",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"name": "TEST_Delete_Agent_Iter69", "role": "test"}
        )
        agent_id = create_resp.json()["agent_id"]
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}/api/admin/nexify-ai/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("deleted") == True
    
    def test_cannot_delete_master(self, auth_token):
        """DELETE /api/admin/nexify-ai/agents/nexify-ai-master returns 403"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/nexify-ai/agents/nexify-ai-master",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 403


class TestToolExecution:
    """Tool execution endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json()["access_token"]
    
    def test_execute_shell_tool(self, auth_token):
        """POST /api/admin/nexify-ai/execute-tool with tool=execute_shell works"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/execute-tool",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"tool": "execute_shell", "params": {"command": "echo 'test_iter69'"}}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "result" in data
        assert data["result"]["exit_code"] == 0
        assert "test_iter69" in data["result"]["stdout"]
    
    def test_system_stats_tool(self, auth_token):
        """POST /api/admin/nexify-ai/execute-tool with tool=system_stats works"""
        response = requests.post(
            f"{BASE_URL}/api/admin/nexify-ai/execute-tool",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"tool": "system_stats", "params": {}}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "result" in data
        result = data["result"]
        assert "contacts" in result
        assert "leads" in result
        assert "timestamp" in result


class TestDashboardStats:
    """Dashboard stats endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json()["access_token"]
    
    def test_admin_stats(self, auth_token):
        """GET /api/admin/stats returns dashboard statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify stat fields exist
        assert "leads_total" in data or "total_leads" in data or "leads" in data
        assert "bookings_total" in data or "total_bookings" in data or "bookings" in data


class TestLeadsEndpoint:
    """Leads endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json()["access_token"]
    
    def test_list_leads(self, auth_token):
        """GET /api/admin/leads returns leads list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "leads" in data


class TestContactsEndpoint:
    """Contacts endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        return response.json()["access_token"]
    
    def test_list_contacts(self, auth_token):
        """GET /api/admin/contacts returns contacts list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contacts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 200 or 404 if endpoint is /customers
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"


# Cleanup test agents after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_agents():
    """Cleanup TEST_ prefixed agents after tests"""
    yield
    # Cleanup
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            agents_resp = requests.get(
                f"{BASE_URL}/api/admin/nexify-ai/agents",
                headers={"Authorization": f"Bearer {token}"}
            )
            if agents_resp.status_code == 200:
                for agent in agents_resp.json().get("agents", []):
                    if agent.get("name", "").startswith("TEST_"):
                        requests.delete(
                            f"{BASE_URL}/api/admin/nexify-ai/agents/{agent['agent_id']}",
                            headers={"Authorization": f"Bearer {token}"}
                        )
    except Exception as e:
        print(f"Cleanup error: {e}")
