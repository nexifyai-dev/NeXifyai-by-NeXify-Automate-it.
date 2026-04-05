"""
NeXifyAI E2E Audit - Iteration 75
Comprehensive backend API tests for Oracle System, NeXify AI, Admin Dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


class TestAdminAuth:
    """Admin authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin auth token"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_admin_login_success(self):
        """Test admin login returns token"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 20
        print(f"PASS: Admin login successful, token length: {len(data['access_token'])}")
    
    def test_admin_login_invalid_credentials(self):
        """Test login with wrong password fails"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert resp.status_code in [401, 400]
        print("PASS: Invalid credentials rejected")


class TestAdminDashboard:
    """Admin dashboard and stats tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_admin_stats(self, auth_headers):
        """Test GET /api/admin/stats returns dashboard data"""
        resp = requests.get(f"{BASE_URL}/api/admin/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Verify stat fields exist
        expected_fields = ["leads_total", "leads_new", "contacts_total", "quotes_total", 
                          "contracts_total", "invoices_total", "bookings_total", "chat_sessions_total"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"PASS: Admin stats returned - leads_total={data.get('leads_total')}, contacts={data.get('contacts_total')}")
    
    def test_audit_health(self, auth_headers):
        """Test GET /api/admin/audit/health returns system health"""
        resp = requests.get(f"{BASE_URL}/api/admin/audit/health", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "overall" in data or "checks" in data
        print(f"PASS: Audit health returned - overall={data.get('overall')}")


class TestOracleSystem:
    """Oracle Command Center API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_oracle_health(self, auth_headers):
        """Test Oracle health - Supabase and DeepSeek connectivity"""
        resp = requests.get(f"{BASE_URL}/api/admin/oracle/health", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "supabase" in data
        assert "deepseek" in data
        assert data["supabase"]["connected"] == True, "Supabase not connected"
        assert data["deepseek"]["connected"] == True, "DeepSeek not connected"
        print(f"PASS: Oracle health - Supabase={data['supabase']['connected']}, DeepSeek={data['deepseek']['connected']}")
    
    def test_oracle_dashboard(self, auth_headers):
        """Test Oracle dashboard returns counts and status"""
        resp = requests.get(f"{BASE_URL}/api/admin/oracle/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "counts" in data
        assert "oracle_status" in data
        counts = data["counts"]
        # Verify 6 stat card fields
        expected_counts = ["brain_notes", "knowledge_entries", "memory_entries", 
                          "ai_agents", "oracle_tasks_total", "audit_logs"]
        for field in expected_counts:
            assert field in counts, f"Missing count: {field}"
        print(f"PASS: Oracle dashboard - brain_notes={counts.get('brain_notes')}, ai_agents={counts.get('ai_agents')}")
    
    def test_oracle_agents(self, auth_headers):
        """Test Oracle agents list - should have 33+ AI agents"""
        resp = requests.get(f"{BASE_URL}/api/admin/oracle/agents", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "oracle_agents" in data
        assert "ai_agents" in data
        ai_count = len(data.get("ai_agents", []))
        assert ai_count >= 30, f"Expected 30+ AI agents, got {ai_count}"
        print(f"PASS: Oracle agents - oracle_agents={len(data.get('oracle_agents', []))}, ai_agents={ai_count}")
    
    def test_oracle_brain_search(self, auth_headers):
        """Test Brain search functionality"""
        resp = requests.get(f"{BASE_URL}/api/admin/oracle/brain?q=architecture&limit=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "notes" in data
        print(f"PASS: Brain search returned {len(data.get('notes', []))} notes")
    
    def test_oracle_tasks_list(self, auth_headers):
        """Test Oracle tasks list"""
        resp = requests.get(f"{BASE_URL}/api/admin/oracle/tasks?limit=50", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
        print(f"PASS: Oracle tasks returned {len(data.get('tasks', []))} tasks")
    
    def test_oracle_task_creation(self, auth_headers):
        """Test creating Oracle task with valid type"""
        task_data = {
            "title": "TEST_Iter75_Task",
            "description": "Test task from iteration 75",
            "task_type": "general",
            "priority": 5
        }
        resp = requests.post(f"{BASE_URL}/api/admin/oracle/tasks", headers=auth_headers, json=task_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("created") == True
        assert "task_id" in data
        print(f"PASS: Task created - task_id={data.get('task_id')}, type={data.get('type')}")


class TestOracleEngine:
    """Oracle Autonomous Engine tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_engine_status(self, auth_headers):
        """Test Engine status returns pipeline stats and scheduler jobs"""
        resp = requests.get(f"{BASE_URL}/api/admin/oracle/engine/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline" in data
        assert "scheduler" in data
        pipeline = data["pipeline"]
        assert "pending" in pipeline
        assert "running" in pipeline
        assert "total" in pipeline
        # Verify scheduler has 11 jobs
        scheduler = data.get("scheduler", {})
        jobs_count = scheduler.get("count", 0)
        assert jobs_count >= 10, f"Expected 10+ scheduler jobs, got {jobs_count}"
        print(f"PASS: Engine status - pending={pipeline.get('pending')}, running={pipeline.get('running')}, scheduler_jobs={jobs_count}")
    
    def test_font_audit(self, auth_headers):
        """Test Font-Audit button returns audit results"""
        resp = requests.post(f"{BASE_URL}/api/admin/oracle/engine/font-audit", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "audit" in data
        audit = data["audit"]
        assert "files_scanned" in audit
        assert "unique_fonts" in audit
        assert "issue_count" in audit or "issues" in audit
        print(f"PASS: Font audit - files_scanned={audit.get('files_scanned')}, fonts={audit.get('unique_fonts')}, issues={audit.get('issue_count', len(audit.get('issues', [])))}")
    
    def test_knowledge_sync(self, auth_headers):
        """Test Knowledge-Sync button"""
        resp = requests.post(f"{BASE_URL}/api/admin/oracle/engine/sync-knowledge", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("synced") == True
        print("PASS: Knowledge sync completed")


class TestNeXifyAI:
    """NeXify AI Chat tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_nexify_ai_status(self, auth_headers):
        """Test NeXify AI status endpoint"""
        resp = requests.get(f"{BASE_URL}/api/admin/nexify-ai/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        print(f"PASS: NeXify AI status returned")
    
    def test_nexify_ai_conversations(self, auth_headers):
        """Test NeXify AI conversations list"""
        resp = requests.get(f"{BASE_URL}/api/admin/nexify-ai/conversations", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "conversations" in data
        print(f"PASS: NeXify AI conversations - count={len(data.get('conversations', []))}")
    
    def test_nexify_ai_chat(self, auth_headers):
        """Test NeXify AI chat endpoint with Systemstatus query"""
        chat_data = {
            "message": "Systemstatus",
            "use_memory": True
        }
        resp = requests.post(f"{BASE_URL}/api/admin/nexify-ai/chat", headers=auth_headers, json=chat_data, timeout=60)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data or "content" in data or "message" in data
        print(f"PASS: NeXify AI chat responded")


class TestCRMEndpoints:
    """CRM-related endpoints tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_leads_list(self, auth_headers):
        """Test leads list endpoint"""
        resp = requests.get(f"{BASE_URL}/api/admin/leads", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "leads" in data
        print(f"PASS: Leads list - count={len(data.get('leads', []))}")
    
    def test_contacts_list(self, auth_headers):
        """Test contacts list endpoint"""
        resp = requests.get(f"{BASE_URL}/api/admin/contacts", headers=auth_headers)
        assert resp.status_code == 200
        print("PASS: Contacts endpoint accessible")
    
    def test_contracts_list(self, auth_headers):
        """Test contracts list endpoint"""
        resp = requests.get(f"{BASE_URL}/api/admin/contracts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "contracts" in data
        print(f"PASS: Contracts list - count={len(data.get('contracts', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
