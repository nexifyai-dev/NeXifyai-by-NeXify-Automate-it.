"""
Test Oracle Autonomous Engine - Iteration 74
Tests for the NEW Oracle Engine features:
- Engine status endpoint with pipeline stats and scheduler jobs
- Engine trigger (cycle start)
- Font audit
- Knowledge sync
- Task creation with valid types
- Health check (Supabase + DeepSeek connectivity)
"""
import os
import pytest
import requests
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


class TestOracleEngineAuth:
    """Authentication tests for Oracle Engine endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_admin_login_success(self):
        """Test admin login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 20


class TestOracleHealth:
    """Oracle Health endpoint tests - Supabase + DeepSeek connectivity"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_oracle_health_endpoint(self, headers):
        """GET /api/admin/oracle/health returns supabase.connected=true and deepseek.connected=true"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/health", headers=headers)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        
        # Verify Supabase connection
        assert "supabase" in data, "Missing supabase in health response"
        assert data["supabase"]["connected"] == True, f"Supabase not connected: {data['supabase']}"
        
        # Verify DeepSeek connection
        assert "deepseek" in data, "Missing deepseek in health response"
        assert data["deepseek"]["configured"] == True, "DeepSeek not configured"
        assert data["deepseek"]["connected"] == True, f"DeepSeek not connected: {data['deepseek']}"
        
        # Verify timestamp
        assert "timestamp" in data


class TestOracleEngineStatus:
    """Oracle Engine Status endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_engine_status_returns_pipeline_stats(self, headers):
        """GET /api/admin/oracle/engine/status returns pipeline stats"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/engine/status", headers=headers)
        assert response.status_code == 200, f"Engine status failed: {response.text}"
        data = response.json()
        
        # Verify pipeline stats
        assert "pipeline" in data, "Missing pipeline in engine status"
        pipeline = data["pipeline"]
        assert "pending" in pipeline, "Missing pending count"
        assert "running" in pipeline, "Missing running count"
        assert "completed_24h" in pipeline, "Missing completed_24h count"
        assert "failed_24h" in pipeline, "Missing failed_24h count"
        assert "reassigned_24h" in pipeline, "Missing reassigned_24h count"
        assert "total" in pipeline, "Missing total count"
        
        # Verify counts are integers
        assert isinstance(pipeline["pending"], int)
        assert isinstance(pipeline["total"], int)
    
    def test_engine_status_returns_scheduler_jobs(self, headers):
        """GET /api/admin/oracle/engine/status returns scheduler.jobs array with 11 jobs"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/engine/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify scheduler info
        assert "scheduler" in data, "Missing scheduler in engine status"
        scheduler = data["scheduler"]
        
        # Check for jobs array
        assert "jobs" in scheduler, "Missing jobs array in scheduler"
        jobs = scheduler["jobs"]
        assert isinstance(jobs, list), "jobs should be a list"
        
        # Verify 11 jobs are registered
        assert len(jobs) >= 11, f"Expected at least 11 jobs, got {len(jobs)}"
        
        # Verify job structure
        for job in jobs:
            assert "id" in job, "Job missing id"
            assert "name" in job, "Job missing name"
            assert "trigger" in job, "Job missing trigger"
        
        # Check for Oracle-specific jobs
        job_ids = [j["id"] for j in jobs]
        assert "oracle_process" in job_ids, "Missing oracle_process job"
        assert "oracle_knowledge_sync" in job_ids, "Missing oracle_knowledge_sync job"
        assert "oracle_derive_tasks" in job_ids, "Missing oracle_derive_tasks job"
        assert "oracle_font_audit" in job_ids, "Missing oracle_font_audit job"
    
    def test_engine_status_returns_recent_tasks(self, headers):
        """GET /api/admin/oracle/engine/status returns recent_tasks"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/engine/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify recent tasks
        assert "recent_tasks" in data, "Missing recent_tasks in engine status"
        assert isinstance(data["recent_tasks"], list)


class TestOracleEngineTrigger:
    """Oracle Engine Trigger endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_engine_trigger_cycle(self, headers):
        """POST /api/admin/oracle/engine/trigger triggers processing cycle"""
        # Note: This endpoint may take 60+ seconds due to DeepSeek calls
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/engine/trigger",
            headers=headers,
            timeout=120  # Long timeout for DeepSeek processing
        )
        assert response.status_code == 200, f"Engine trigger failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "triggered" in data, "Missing triggered flag"
        assert data["triggered"] == True, "Trigger should return true"
        assert "stats" in data, "Missing stats in trigger response"
        assert "timestamp" in data, "Missing timestamp"


class TestOracleFontAudit:
    """Oracle Font Audit endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_font_audit_returns_audit_results(self, headers):
        """POST /api/admin/oracle/engine/font-audit returns audit with files_scanned, unique_fonts, issues"""
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/engine/font-audit",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"Font audit failed: {response.text}"
        data = response.json()
        
        # Verify audit structure
        assert "audit" in data, "Missing audit in response"
        audit = data["audit"]
        
        # Verify required fields
        assert "files_scanned" in audit, "Missing files_scanned"
        assert "unique_fonts" in audit, "Missing unique_fonts"
        assert "issues" in audit, "Missing issues"
        assert "issue_count" in audit, "Missing issue_count"
        
        # Verify types
        assert isinstance(audit["files_scanned"], int), "files_scanned should be int"
        assert isinstance(audit["unique_fonts"], int), "unique_fonts should be int"
        assert isinstance(audit["issues"], list), "issues should be list"
        assert isinstance(audit["issue_count"], int), "issue_count should be int"
        
        # Verify files were actually scanned
        assert audit["files_scanned"] > 0, "Should have scanned at least 1 CSS file"
        
        # Verify timestamp
        assert "timestamp" in data


class TestOracleKnowledgeSync:
    """Oracle Knowledge Sync endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_knowledge_sync_triggers_successfully(self, headers):
        """POST /api/admin/oracle/engine/sync-knowledge triggers sync"""
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/engine/sync-knowledge",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"Knowledge sync failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert "synced" in data, "Missing synced flag"
        assert data["synced"] == True, "Sync should return true"
        assert "timestamp" in data


class TestOracleTaskCreation:
    """Oracle Task Creation endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_create_task_with_valid_type_general(self, headers):
        """POST /api/admin/oracle/tasks with type 'general' works"""
        task_data = {
            "title": f"TEST_Task_General_{int(time.time())}",
            "description": "Test task created by iteration 74 testing",
            "task_type": "general",
            "priority": 5
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=headers,
            json=task_data,
            timeout=30
        )
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert "task_id" in data, "Missing task_id in response"
        assert "status" in data, "Missing status in response"
        assert data["status"] == "pending", "New task should be pending"
        assert "type" in data, "Missing type in response"
        assert data["type"] == "general", "Type should be general"
        assert "created" in data, "Missing created flag"
        assert data["created"] == True
    
    def test_create_task_with_valid_type_improvement(self, headers):
        """POST /api/admin/oracle/tasks with type 'improvement' works"""
        task_data = {
            "title": f"TEST_Task_Improvement_{int(time.time())}",
            "description": "Improvement task for testing",
            "task_type": "improvement",
            "priority": 7
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=headers,
            json=task_data,
            timeout=30
        )
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        data = response.json()
        assert data["type"] == "improvement"
    
    def test_create_task_with_valid_type_monitoring(self, headers):
        """POST /api/admin/oracle/tasks with type 'monitoring' works"""
        task_data = {
            "title": f"TEST_Task_Monitoring_{int(time.time())}",
            "description": "Monitoring task for testing",
            "task_type": "monitoring",
            "priority": 6
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=headers,
            json=task_data,
            timeout=30
        )
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        data = response.json()
        assert data["type"] == "monitoring"


class TestOracleDashboard:
    """Oracle Dashboard endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_dashboard_returns_counts(self, headers):
        """GET /api/admin/oracle/dashboard returns counts for all stat cards"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/dashboard", headers=headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify counts
        assert "counts" in data, "Missing counts in dashboard"
        counts = data["counts"]
        
        # Verify all 6 stat card values
        assert "brain_notes" in counts, "Missing brain_notes count"
        assert "knowledge_entries" in counts, "Missing knowledge_entries count"
        assert "memory_entries" in counts, "Missing memory_entries count"
        assert "ai_agents" in counts, "Missing ai_agents count"
        assert "oracle_tasks_total" in counts, "Missing oracle_tasks_total count"
        assert "audit_logs" in counts, "Missing audit_logs count"
        
        # Verify counts are positive integers
        assert isinstance(counts["brain_notes"], int)
        assert isinstance(counts["ai_agents"], int)
        assert counts["ai_agents"] >= 33, f"Expected at least 33 AI agents, got {counts['ai_agents']}"


class TestOracleAgents:
    """Oracle Agents endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_agents_returns_33_plus_ai_agents(self, headers):
        """GET /api/admin/oracle/agents returns 33+ AI agents from Supabase"""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/agents", headers=headers)
        assert response.status_code == 200, f"Agents endpoint failed: {response.text}"
        data = response.json()
        
        # Verify AI agents from Supabase
        assert "ai_agents" in data, "Missing ai_agents in response"
        ai_agents = data["ai_agents"]
        assert isinstance(ai_agents, list)
        assert len(ai_agents) >= 33, f"Expected at least 33 AI agents, got {len(ai_agents)}"
        
        # Verify agent structure
        if ai_agents:
            agent = ai_agents[0]
            assert "name" in agent, "Agent missing name"
            assert "role" in agent, "Agent missing role"


class TestOracleBrain:
    """Oracle Brain endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_brain_search_works(self, headers):
        """GET /api/admin/oracle/brain with search query works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/oracle/brain?q=architecture&limit=20",
            headers=headers
        )
        assert response.status_code == 200, f"Brain search failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "notes" in data, "Missing notes in response"
        assert "count" in data, "Missing count in response"
        assert isinstance(data["notes"], list)


class TestOracleTasks:
    """Oracle Tasks endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json().get("access_token", "")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_tasks_list_returns_tasks(self, headers):
        """GET /api/admin/oracle/tasks returns tasks list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/oracle/tasks?limit=50",
            headers=headers
        )
        assert response.status_code == 200, f"Tasks list failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "tasks" in data, "Missing tasks in response"
        assert "count" in data, "Missing count in response"
        assert isinstance(data["tasks"], list)
        
        # Verify task structure if tasks exist
        if data["tasks"]:
            task = data["tasks"][0]
            assert "id" in task, "Task missing id"
            assert "type" in task, "Task missing type"
            assert "status" in task, "Task missing status"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
