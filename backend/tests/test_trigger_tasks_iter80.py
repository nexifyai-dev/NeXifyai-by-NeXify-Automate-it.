"""
NeXifyAI — Trigger.dev Tasks API Tests (Iteration 80)
Tests for P0.2: Trigger.dev Tasks Admin UI backend endpoints
- GET /api/admin/trigger/tasks - List available tasks
- GET /api/admin/trigger/status - Get trigger system status
- POST /api/admin/trigger/run - Execute a task (fallback mode)
- GET /api/admin/trigger/runs - List recent runs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTriggerTasksAPI:
    """Trigger.dev Tasks API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_health_check(self):
        """Test health endpoint returns healthy status with all services"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("status") == "healthy"
        assert "services" in data
        services = data["services"]
        
        # Verify key services are present and ok
        expected_services = ["mongodb", "supabase", "deepseek", "arcee", "mem0", "resend", "revolut", "workers"]
        for svc in expected_services:
            assert svc in services, f"Missing service: {svc}"
            assert services[svc].get("status") == "ok", f"Service {svc} not ok"
        
        print(f"✓ Health check passed - {len(services)} services all OK")
    
    def test_trigger_tasks_list(self):
        """Test GET /api/admin/trigger/tasks returns 6 tasks with descriptions"""
        response = self.session.get(f"{BASE_URL}/api/admin/trigger/tasks")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "configured" in data
        assert "tasks" in data
        assert "count" in data
        
        # Verify 6 tasks
        assert data["count"] == 6, f"Expected 6 tasks, got {data['count']}"
        
        # Verify expected task IDs
        expected_tasks = [
            "deep-research",
            "generate-report",
            "generate-and-translate-copy",
            "analyze-contract",
            "competitor-monitor",
            "generate-pdf-and-upload"
        ]
        
        tasks = data["tasks"]
        for task_id in expected_tasks:
            assert task_id in tasks, f"Missing task: {task_id}"
            task = tasks[task_id]
            assert "name" in task, f"Task {task_id} missing name"
            assert "description" in task, f"Task {task_id} missing description"
            assert "max_duration" in task, f"Task {task_id} missing max_duration"
            assert "payload_schema" in task, f"Task {task_id} missing payload_schema"
        
        print(f"✓ Trigger tasks list passed - {data['count']} tasks with descriptions")
    
    def test_trigger_status(self):
        """Test GET /api/admin/trigger/status returns configured=false, fallback_mode=true"""
        response = self.session.get(f"{BASE_URL}/api/admin/trigger/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "configured" in data
        assert "tasks_available" in data
        assert "total_runs" in data
        assert "active_runs" in data
        assert "fallback_mode" in data
        
        # Verify fallback mode (no TRIGGER_DEV_API_KEY)
        assert data["configured"] == False, "Expected configured=false (no API key)"
        assert data["fallback_mode"] == True, "Expected fallback_mode=true"
        assert data["tasks_available"] == 6, f"Expected 6 tasks, got {data['tasks_available']}"
        assert isinstance(data["total_runs"], int), "total_runs should be int"
        
        print(f"✓ Trigger status passed - fallback_mode=true, {data['total_runs']} total runs")
    
    def test_trigger_runs_list(self):
        """Test GET /api/admin/trigger/runs returns list of recent runs"""
        response = self.session.get(f"{BASE_URL}/api/admin/trigger/runs?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "success" in data
        assert data["success"] == True
        assert "runs" in data
        assert "total" in data
        
        runs = data["runs"]
        assert isinstance(runs, list), "runs should be a list"
        
        # If there are runs, verify structure
        if len(runs) > 0:
            run = runs[0]
            assert "run_id" in run, "Run missing run_id"
            assert "task_id" in run, "Run missing task_id"
            assert "status" in run, "Run missing status"
            assert "triggered_at" in run, "Run missing triggered_at"
            print(f"✓ Trigger runs list passed - {len(runs)} runs found")
        else:
            print("✓ Trigger runs list passed - 0 runs (empty)")
    
    def test_trigger_run_deep_research_fallback(self):
        """Test POST /api/admin/trigger/run executes in fallback mode via DeepSeek"""
        payload = {
            "task_id": "deep-research",
            "payload": {
                "initialQuery": "Test query for iteration 80",
                "depth": 1,
                "breadth": 1,
                "language": "de"
            }
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/trigger/run",
            json=payload,
            timeout=120  # DeepSeek can take time
        )
        assert response.status_code == 200, f"Run failed: {response.text}"
        data = response.json()
        
        # Verify success
        assert data.get("success") == True, f"Expected success=true, got {data}"
        assert "run_id" in data, "Missing run_id"
        assert data.get("fallback") == True, "Expected fallback=true (local execution)"
        assert "result" in data, "Missing result"
        assert len(data.get("result", "")) > 100, "Result too short"
        
        print(f"✓ Trigger run (deep-research) passed - run_id={data['run_id']}, fallback=true, result={len(data['result'])} chars")
    
    def test_trigger_run_unknown_task(self):
        """Test POST /api/admin/trigger/run with unknown task returns error"""
        payload = {
            "task_id": "unknown-task-xyz",
            "payload": {}
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/trigger/run",
            json=payload
        )
        assert response.status_code == 200  # Returns 200 with success=false
        data = response.json()
        
        assert data.get("success") == False, "Expected success=false for unknown task"
        assert "error" in data, "Expected error message"
        
        print(f"✓ Unknown task error handling passed - error: {data.get('error')}")


class TestNeXifyAIStatus:
    """Test NeXify AI status endpoint for DeepSeek primary configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        self.session = requests.Session()
        login_response = self.session.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        token = login_response.json().get("access_token")
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
    
    def test_nexify_ai_status_deepseek_primary(self):
        """Test that DeepSeek is configured as primary LLM"""
        response = self.session.get(f"{BASE_URL}/api/admin/nexify-ai/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify DeepSeek is primary
        assert data.get("master_llm") == "deepseek", f"Expected master_llm=deepseek, got {data.get('master_llm')}"
        
        # Verify DeepSeek configuration
        deepseek = data.get("deepseek", {})
        assert deepseek.get("configured") == True, "DeepSeek should be configured"
        assert deepseek.get("connected") == True, "DeepSeek should be connected"
        assert deepseek.get("primary") == True, "DeepSeek should be primary"
        
        # Verify Arcee as fallback
        arcee = data.get("arcee", {})
        assert arcee.get("configured") == True, "Arcee should be configured"
        assert arcee.get("fallback") == True, "Arcee should be fallback"
        
        print(f"✓ NeXify AI status passed - DeepSeek primary, Arcee fallback")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
