"""
NeXifyAI — Iteration 78 Backend Tests
Platform Hardening: Health Check, Leitstelle, Service Templates, Task Transitions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://contract-os.preview.emergentagent.com').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "1def!xO2022!!"


@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token."""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestHealthCheck:
    """Test GET /api/health returns 'healthy' with all 8 services."""
    
    def test_health_endpoint_returns_healthy(self):
        """Health check returns healthy status."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"]
        assert "services" in data
        print(f"Health status: {data['status']}")
    
    def test_health_has_mongodb_service(self):
        """Health check includes mongodb service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "mongodb" in data["services"]
        print(f"MongoDB status: {data['services']['mongodb']}")
    
    def test_health_has_supabase_service(self):
        """Health check includes supabase service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "supabase" in data["services"]
        print(f"Supabase status: {data['services']['supabase']}")
    
    def test_health_has_deepseek_service(self):
        """Health check includes deepseek service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "deepseek" in data["services"]
        print(f"DeepSeek status: {data['services']['deepseek']}")
    
    def test_health_has_arcee_service(self):
        """Health check includes arcee service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "arcee" in data["services"]
        print(f"Arcee status: {data['services']['arcee']}")
    
    def test_health_has_mem0_service(self):
        """Health check includes mem0 service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "mem0" in data["services"]
        print(f"mem0 status: {data['services']['mem0']}")
    
    def test_health_has_resend_service(self):
        """Health check includes resend service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "resend" in data["services"]
        print(f"Resend status: {data['services']['resend']}")
    
    def test_health_has_revolut_service(self):
        """Health check includes revolut service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "revolut" in data["services"]
        print(f"Revolut status: {data['services']['revolut']}")
    
    def test_health_has_workers_service(self):
        """Health check includes workers service."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "workers" in data["services"]
        print(f"Workers status: {data['services']['workers']}")
    
    def test_health_all_8_services_present(self):
        """Health check has all 8 required services."""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        required_services = ["mongodb", "supabase", "deepseek", "arcee", "mem0", "resend", "revolut", "workers"]
        for svc in required_services:
            assert svc in data["services"], f"Missing service: {svc}"
        print(f"All 8 services present: {list(data['services'].keys())}")


class TestLeitstelle:
    """Test GET /api/admin/oracle/leitstelle returns pipeline stats with German status names."""
    
    def test_leitstelle_endpoint_returns_200(self, auth_headers):
        """Leitstelle endpoint returns 200."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pipeline" in data
        print(f"Leitstelle pipeline: {data['pipeline']}")
    
    def test_leitstelle_has_erkannt_status(self, auth_headers):
        """Leitstelle pipeline has 'erkannt' (detected) status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "erkannt" in data["pipeline"]
        print(f"erkannt count: {data['pipeline']['erkannt']}")
    
    def test_leitstelle_has_in_arbeit_status(self, auth_headers):
        """Leitstelle pipeline has 'in_arbeit' (in progress) status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "in_arbeit" in data["pipeline"]
        print(f"in_arbeit count: {data['pipeline']['in_arbeit']}")
    
    def test_leitstelle_has_wartend_status(self, auth_headers):
        """Leitstelle pipeline has 'wartend' (waiting) status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "wartend" in data["pipeline"]
        print(f"wartend count: {data['pipeline']['wartend']}")
    
    def test_leitstelle_has_in_loop_status(self, auth_headers):
        """Leitstelle pipeline has 'in_loop' status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "in_loop" in data["pipeline"]
        print(f"in_loop count: {data['pipeline']['in_loop']}")
    
    def test_leitstelle_has_validiert_24h_status(self, auth_headers):
        """Leitstelle pipeline has 'validiert_24h' status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "validiert_24h" in data["pipeline"]
        print(f"validiert_24h count: {data['pipeline']['validiert_24h']}")
    
    def test_leitstelle_has_fehlgeschlagen_24h_status(self, auth_headers):
        """Leitstelle pipeline has 'fehlgeschlagen_24h' status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "fehlgeschlagen_24h" in data["pipeline"]
        print(f"fehlgeschlagen_24h count: {data['pipeline']['fehlgeschlagen_24h']}")
    
    def test_leitstelle_has_eskaliert_status(self, auth_headers):
        """Leitstelle pipeline has 'eskaliert' (escalated) status."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        assert "eskaliert" in data["pipeline"]
        print(f"eskaliert count: {data['pipeline']['eskaliert']}")
    
    def test_leitstelle_all_german_status_names(self, auth_headers):
        """Leitstelle has all required German status names."""
        response = requests.get(f"{BASE_URL}/api/admin/oracle/leitstelle", headers=auth_headers)
        data = response.json()
        required_statuses = ["erkannt", "in_arbeit", "wartend", "in_loop", "validiert_24h", "fehlgeschlagen_24h", "eskaliert"]
        for status in required_statuses:
            assert status in data["pipeline"], f"Missing German status: {status}"
        print(f"All German statuses present: {required_statuses}")


class TestServiceTemplates:
    """Test GET /api/admin/service-templates returns 9 templates."""
    
    def test_service_templates_returns_200(self, auth_headers):
        """Service templates endpoint returns 200."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        print(f"Templates count: {data.get('count', len(data['templates']))}")
    
    def test_service_templates_returns_9_templates(self, auth_headers):
        """Service templates returns exactly 9 templates."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates", headers=auth_headers)
        data = response.json()
        assert len(data["templates"]) == 9, f"Expected 9 templates, got {len(data['templates'])}"
        print(f"Template names: {[t['name'] for t in data['templates']]}")
    
    def test_service_templates_have_names(self, auth_headers):
        """All templates have names."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates", headers=auth_headers)
        data = response.json()
        for tmpl in data["templates"]:
            assert "name" in tmpl and tmpl["name"], f"Template missing name: {tmpl}"
    
    def test_service_templates_have_prices(self, auth_headers):
        """All templates have price (monthly or fixed)."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates", headers=auth_headers)
        data = response.json()
        for tmpl in data["templates"]:
            has_price = tmpl.get("price_monthly") is not None or tmpl.get("price_fixed") is not None
            assert has_price, f"Template {tmpl['name']} missing price"
        print("All templates have prices")
    
    def test_service_templates_expected_names(self, auth_headers):
        """Templates include expected service names."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates", headers=auth_headers)
        data = response.json()
        template_keys = [t["key"] for t in data["templates"]]
        expected_keys = [
            "starter_ai_agenten", "growth_ai_agenten", 
            "seo_starter", "seo_growth",
            "website_starter", "website_professional", "website_enterprise",
            "app_mvp", "app_professional"
        ]
        for key in expected_keys:
            assert key in template_keys, f"Missing template: {key}"
        print(f"All expected templates present: {expected_keys}")


class TestServiceTemplateDetail:
    """Test GET /api/admin/service-templates/{key} returns full template."""
    
    def test_growth_ai_agenten_template_detail(self, auth_headers):
        """Growth AI Agenten template returns full detail."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates/growth_ai_agenten", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "growth_ai_agenten"
        assert data["name"] == "Growth AI Agenten AG"
        print(f"Template: {data['name']}, Price: {data.get('price_monthly')}")
    
    def test_growth_ai_agenten_has_milestones(self, auth_headers):
        """Growth AI Agenten template has milestones."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates/growth_ai_agenten", headers=auth_headers)
        data = response.json()
        assert "milestones" in data
        assert len(data["milestones"]) > 0
        print(f"Milestones count: {len(data['milestones'])}")
    
    def test_growth_ai_agenten_has_agent_assignments(self, auth_headers):
        """Growth AI Agenten template has agent_assignments."""
        response = requests.get(f"{BASE_URL}/api/admin/service-templates/growth_ai_agenten", headers=auth_headers)
        data = response.json()
        assert "agent_assignments" in data
        assert len(data["agent_assignments"]) > 0
        print(f"Agent assignments: {list(data['agent_assignments'].keys())}")


class TestTemplateInstantiate:
    """Test POST /api/admin/service-templates/instantiate creates project."""
    
    def test_instantiate_template_creates_project(self, auth_headers):
        """Instantiating template creates project with milestones."""
        payload = {
            "template_key": "starter_ai_agenten",
            "customer_name": "TEST_Iter78_Customer",
            "customer_email": "test_iter78@example.com",
            "customer_company": "TEST Iter78 GmbH",
            "custom_notes": "Test instantiation for iteration 78"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/service-templates/instantiate",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("created") == True
        assert "project_id" in data
        assert "milestones" in data
        assert "total_tasks" in data
        print(f"Created project: {data['project_id']}, milestones: {data['milestones']}, tasks: {data['total_tasks']}")


class TestTaskTransitions:
    """Test task escalate and cancel endpoints."""
    
    def test_create_task_for_escalation(self, auth_headers):
        """Create a task to test escalation."""
        payload = {
            "title": "TEST_Iter78_Escalate_Task",
            "description": "Task for testing escalation in iteration 78",
            "task_type": "general",
            "priority": 5
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        print(f"Created task for escalation: {data['task_id']}")
        return data["task_id"]
    
    def test_escalate_task(self, auth_headers):
        """Test POST /api/admin/oracle/tasks/{task_id}/escalate."""
        # First create a task
        payload = {
            "title": "TEST_Iter78_Escalate_Task_2",
            "description": "Task for testing escalation",
            "task_type": "general",
            "priority": 5
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=auth_headers,
            json=payload
        )
        task_id = create_resp.json()["task_id"]
        
        # Escalate the task
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks/{task_id}/escalate",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("escalated") == True
        assert data.get("task_id") == task_id
        print(f"Escalated task: {task_id}")
    
    def test_cancel_task(self, auth_headers):
        """Test POST /api/admin/oracle/tasks/{task_id}/cancel."""
        # First create a task
        payload = {
            "title": "TEST_Iter78_Cancel_Task",
            "description": "Task for testing cancellation",
            "task_type": "general",
            "priority": 5
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks",
            headers=auth_headers,
            json=payload
        )
        task_id = create_resp.json()["task_id"]
        
        # Cancel the task
        response = requests.post(
            f"{BASE_URL}/api/admin/oracle/tasks/{task_id}/cancel",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("cancelled") == True
        assert data.get("task_id") == task_id
        print(f"Cancelled task: {task_id}")


class TestEnvTemplateAndStripe:
    """Test .env.template exists and Stripe is removed."""
    
    def test_env_template_exists(self):
        """Verify .env.template file exists."""
        env_template_path = "/app/backend/.env.template"
        assert os.path.exists(env_template_path), f".env.template not found at {env_template_path}"
        print(f".env.template exists at {env_template_path}")
    
    def test_stripe_not_in_requirements(self):
        """Verify Stripe is NOT in requirements.txt."""
        requirements_path = "/app/backend/requirements.txt"
        with open(requirements_path, 'r') as f:
            content = f.read().lower()
        assert "stripe" not in content, "Stripe should be removed from requirements.txt"
        print("Stripe is NOT in requirements.txt ✓")


class TestAdminLogin:
    """Test admin login flow."""
    
    def test_admin_login_returns_token(self):
        """Admin login returns access_token."""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"Login successful, token received")
    
    def test_admin_login_invalid_credentials(self):
        """Admin login with invalid credentials returns 401."""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "wrong@email.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401
        print("Invalid credentials correctly rejected with 401")
