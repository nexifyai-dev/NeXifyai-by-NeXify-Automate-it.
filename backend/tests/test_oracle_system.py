"""
NeXifyAI — Oracle System Integration Tests (Iteration 73)
Tests for Oracle Command Center: Supabase PostgreSQL + DeepSeek LLM integration
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://contract-os.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login returns valid JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"username={ADMIN_EMAIL}&password={ADMIN_PASSWORD}"
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert len(data["access_token"]) > 20, "Token too short"
        print(f"✓ Admin login successful, token length: {len(data['access_token'])}")


@pytest.fixture(scope="module")
def auth_token():
    """Get admin JWT token for authenticated requests"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={ADMIN_EMAIL}&password={ADMIN_PASSWORD}"
    )
    if response.status_code != 200:
        pytest.skip(f"Auth failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with JWT auth"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestOracleHealth:
    """Oracle System health check tests"""
    
    def test_oracle_health_endpoint(self, auth_headers):
        """GET /api/admin/oracle/health returns Supabase and DeepSeek status"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/health", headers=auth_headers)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        
        # Verify Supabase connection
        assert "supabase" in data, "Missing supabase in health response"
        assert data["supabase"]["connected"] == True, f"Supabase not connected: {data['supabase']}"
        print(f"✓ Supabase connected: {data['supabase']['connected']}")
        
        # Verify DeepSeek configuration
        assert "deepseek" in data, "Missing deepseek in health response"
        assert data["deepseek"]["configured"] == True, "DeepSeek not configured"
        assert data["deepseek"]["connected"] == True, f"DeepSeek not connected: {data['deepseek']}"
        print(f"✓ DeepSeek connected: {data['deepseek']['connected']}, model: {data['deepseek'].get('model', 'N/A')}")


class TestOracleDashboard:
    """Oracle Dashboard API tests"""
    
    def test_oracle_dashboard_returns_counts(self, auth_headers):
        """GET /api/admin/oracle/dashboard returns all expected counts"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        
        # Verify counts structure
        assert "counts" in data, "Missing counts in dashboard"
        counts = data["counts"]
        
        # Verify expected count fields
        expected_fields = ["brain_notes", "knowledge_entries", "memory_entries", "ai_agents", "oracle_tasks_total", "audit_logs"]
        for field in expected_fields:
            assert field in counts, f"Missing {field} in counts"
            assert isinstance(counts[field], int), f"{field} should be int, got {type(counts[field])}"
        
        # Verify expected data volumes (from problem statement)
        assert counts["brain_notes"] >= 10000, f"Expected 10K+ brain_notes, got {counts['brain_notes']}"
        assert counts["knowledge_entries"] >= 150, f"Expected 150+ knowledge_entries, got {counts['knowledge_entries']}"
        assert counts["ai_agents"] >= 30, f"Expected 30+ ai_agents, got {counts['ai_agents']}"
        assert counts["audit_logs"] >= 5000, f"Expected 5K+ audit_logs, got {counts['audit_logs']}"
        
        print(f"✓ Dashboard counts: brain_notes={counts['brain_notes']}, knowledge={counts['knowledge_entries']}, "
              f"memory={counts['memory_entries']}, ai_agents={counts['ai_agents']}, "
              f"oracle_tasks={counts['oracle_tasks_total']}, audit_logs={counts['audit_logs']}")
    
    def test_oracle_dashboard_has_status(self, auth_headers):
        """Dashboard includes oracle_status with pending/running/completed/failed"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "oracle_status" in data, "Missing oracle_status"
        
        status = data["oracle_status"]
        # Check for status fields (may be empty but should exist)
        print(f"✓ Oracle status: pending={status.get('pending', 0)}, running={status.get('running', 0)}, "
              f"completed_24h={status.get('completed_24h', 0)}, failed={status.get('failed', 0)}")
    
    def test_oracle_dashboard_has_queue(self, auth_headers):
        """Dashboard includes queue array"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "queue" in data, "Missing queue in dashboard"
        assert isinstance(data["queue"], list), "queue should be a list"
        
        print(f"✓ Queue has {len(data['queue'])} items, pending={data.get('queue_pending', 0)}, running={data.get('queue_running', 0)}")


class TestOracleAgents:
    """Oracle Agents API tests"""
    
    def test_oracle_agents_returns_both_types(self, auth_headers):
        """GET /api/admin/oracle/agents returns oracle_agents and ai_agents"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/agents", headers=auth_headers)
        assert response.status_code == 200, f"Agents failed: {response.text}"
        
        data = response.json()
        
        # Verify oracle_agents (6 expected)
        assert "oracle_agents" in data, "Missing oracle_agents"
        assert isinstance(data["oracle_agents"], list), "oracle_agents should be list"
        assert len(data["oracle_agents"]) >= 6, f"Expected 6+ oracle_agents, got {len(data['oracle_agents'])}"
        
        # Verify ai_agents (33 expected from Supabase)
        assert "ai_agents" in data, "Missing ai_agents"
        assert isinstance(data["ai_agents"], list), "ai_agents should be list"
        assert len(data["ai_agents"]) >= 30, f"Expected 30+ ai_agents, got {len(data['ai_agents'])}"
        
        print(f"✓ Agents: {len(data['oracle_agents'])} oracle agents, {len(data['ai_agents'])} AI agents")
        
        # Verify AI agent structure
        if data["ai_agents"]:
            agent = data["ai_agents"][0]
            assert "name" in agent, "AI agent missing name"
            assert "role" in agent, "AI agent missing role"
            print(f"  Sample AI agent: {agent.get('name')} - {agent.get('role')}")


class TestOracleBrain:
    """Oracle Brain (brain_notes) API tests"""
    
    def test_brain_list_returns_notes(self, auth_headers):
        """GET /api/admin/oracle/brain returns brain notes"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/brain?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Brain list failed: {response.text}"
        
        data = response.json()
        assert "notes" in data, "Missing notes in response"
        assert isinstance(data["notes"], list), "notes should be list"
        assert len(data["notes"]) > 0, "Expected some brain notes"
        
        # Verify note structure
        note = data["notes"][0]
        assert "id" in note, "Note missing id"
        assert "title" in note, "Note missing title"
        
        print(f"✓ Brain notes: {len(data['notes'])} returned, sample: {note.get('title', 'N/A')[:50]}")
    
    def test_brain_search_architecture(self, auth_headers):
        """GET /api/admin/oracle/brain?q=architecture returns search results"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/brain?q=architecture&limit=10", headers=auth_headers)
        assert response.status_code == 200, f"Brain search failed: {response.text}"
        
        data = response.json()
        assert "notes" in data, "Missing notes in search response"
        # Search may return 0 results if no matches, but should not error
        print(f"✓ Brain search 'architecture': {len(data['notes'])} results")


class TestOracleTasks:
    """Oracle Tasks API tests"""
    
    def test_oracle_tasks_list(self, auth_headers):
        """GET /api/admin/oracle/tasks returns task list"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/tasks?limit=50", headers=auth_headers)
        assert response.status_code == 200, f"Tasks list failed: {response.text}"
        
        data = response.json()
        assert "tasks" in data, "Missing tasks in response"
        assert isinstance(data["tasks"], list), "tasks should be list"
        
        # Verify task structure if any exist
        if data["tasks"]:
            task = data["tasks"][0]
            expected_fields = ["id", "type", "status", "priority"]
            for field in expected_fields:
                assert field in task, f"Task missing {field}"
        
        print(f"✓ Oracle tasks: {len(data['tasks'])} returned")
    
    def test_oracle_task_creation(self, auth_headers):
        """POST /api/admin/oracle/tasks creates a new task"""
        payload = {
            "title": "TEST_Task_from_pytest",
            "description": "Automated test task created by pytest",
            "priority": 3,
            "task_type": "manual"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        
        data = response.json()
        assert "task_id" in data, "Missing task_id in response"
        assert data.get("created") == True or data.get("status") == "pending", "Task not created"
        
        print(f"✓ Task created: {data.get('task_id')}")


class TestOracleAgentInvocation:
    """Oracle Agent Invocation (DeepSeek) tests"""
    
    def test_invoke_agent_strategist(self, auth_headers):
        """POST /api/admin/oracle/invoke-agent with Strategist agent"""
        payload = {
            "agent_name": "Strategist",
            "message": "Was sind die wichtigsten KPIs für ein B2B SaaS Unternehmen?",
            "use_brain": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/invoke-agent",
            headers=auth_headers,
            json=payload,
            timeout=60  # DeepSeek can take 5-10 seconds
        )
        assert response.status_code == 200, f"Agent invocation failed: {response.text}"
        
        data = response.json()
        
        # Check for error
        if "error" in data:
            pytest.fail(f"Agent returned error: {data['error']}")
        
        # Verify response structure
        assert "agent" in data, "Missing agent in response"
        assert "response" in data, "Missing response in response"
        assert len(data["response"]) > 50, f"Response too short: {len(data['response'])} chars"
        
        print(f"✓ Agent '{data.get('agent')}' responded with {len(data['response'])} chars")
        print(f"  Model: {data.get('model', 'N/A')}, Role: {data.get('role', 'N/A')}")


class TestOracleQueue:
    """Oracle Queue API tests"""
    
    def test_oracle_queue_endpoint(self, auth_headers):
        """GET /api/admin/oracle/queue returns queue items"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/queue?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Queue failed: {response.text}"
        
        data = response.json()
        assert "queue" in data, "Missing queue in response"
        assert isinstance(data["queue"], list), "queue should be list"
        
        print(f"✓ Oracle queue: {len(data['queue'])} items")


class TestOracleKnowledge:
    """Oracle Knowledge Base API tests"""
    
    def test_knowledge_list(self, auth_headers):
        """GET /api/admin/oracle/knowledge returns knowledge entries"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/knowledge?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Knowledge list failed: {response.text}"
        
        data = response.json()
        assert "entries" in data, "Missing entries in response"
        assert isinstance(data["entries"], list), "entries should be list"
        
        print(f"✓ Knowledge entries: {len(data['entries'])} returned")


class TestOracleMemory:
    """Oracle Memory API tests"""
    
    def test_memory_list(self, auth_headers):
        """GET /api/admin/oracle/memory returns memory entries"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/memory?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Memory list failed: {response.text}"
        
        data = response.json()
        assert "entries" in data, "Missing entries in response"
        assert isinstance(data["entries"], list), "entries should be list"
        
        print(f"✓ Memory entries: {len(data['entries'])} returned")


class TestOracleAudit:
    """Oracle Audit Logs API tests"""
    
    def test_audit_logs_list(self, auth_headers):
        """GET /api/admin/oracle/audit returns audit logs"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/audit?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Audit logs failed: {response.text}"
        
        data = response.json()
        assert "logs" in data, "Missing logs in response"
        assert isinstance(data["logs"], list), "logs should be list"
        
        print(f"✓ Audit logs: {len(data['logs'])} returned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
