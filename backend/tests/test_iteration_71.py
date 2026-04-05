"""
Iteration 71 - Backend API Tests
Testing: Scroll fix, Connection status, Monitoring, Stats API, View persistence
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://contract-os.preview.emergentagent.com')

class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "p.courbois@icloud.com", "password": "1def!xO2022!!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        return data["access_token"]


class TestStatsAPI:
    """Stats API endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "p.courbois@icloud.com", "password": "1def!xO2022!!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    def test_stats_returns_contacts_total(self, auth_token):
        """Stats API returns contacts_total"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "contacts_total" in data
        assert isinstance(data["contacts_total"], int)
    
    def test_stats_returns_quotes_total(self, auth_token):
        """Stats API returns quotes_total"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "quotes_total" in data
        assert isinstance(data["quotes_total"], int)
    
    def test_stats_returns_contracts_total(self, auth_token):
        """Stats API returns contracts_total"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "contracts_total" in data
        assert isinstance(data["contracts_total"], int)
    
    def test_stats_returns_invoices_total(self, auth_token):
        """Stats API returns invoices_total"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "invoices_total" in data
        assert isinstance(data["invoices_total"], int)
    
    def test_stats_returns_all_counts(self, auth_token):
        """Stats API returns all expected count fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        expected_fields = [
            "leads_total", "leads_new", "bookings_total",
            "contacts_total", "quotes_total", "contracts_total",
            "invoices_total", "projects_total", "chat_sessions_total"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestNeXifyAIStatus:
    """NeXify AI status endpoint tests - connection indicators"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "p.courbois@icloud.com", "password": "1def!xO2022!!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    def test_nexify_ai_status_arcee_connected(self, auth_token):
        """Arcee AI should be connected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "arcee" in data
        assert data["arcee"]["connected"] == True
    
    def test_nexify_ai_status_mem0_connected(self, auth_token):
        """mem0 Brain should be connected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "mem0" in data
        assert data["mem0"]["connected"] == True
    
    def test_nexify_ai_status_whatsapp_disconnected(self, auth_token):
        """WhatsApp should be disconnected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "whatsapp" in data
        assert data["whatsapp"]["connected"] == False
        assert data["whatsapp"]["status"] == "disconnected"
    
    def test_nexify_ai_status_database_connected(self, auth_token):
        """MongoDB should be connected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/nexify-ai/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert data["database"]["connected"] == True


class TestMonitoringStatus:
    """Monitoring status endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "p.courbois@icloud.com", "password": "1def!xO2022!!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    def test_monitoring_status_revolut_configured(self, auth_token):
        """Revolut should show 'configured' status, not 'ok'"""
        response = requests.get(
            f"{BASE_URL}/api/admin/monitoring/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "systems" in data
        assert "payments" in data["systems"]
        assert data["systems"]["payments"]["revolut"]["status"] == "configured"
    
    def test_monitoring_status_object_storage_configured(self, auth_token):
        """Object Storage should show 'configured' status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/monitoring/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "systems" in data
        assert "object_storage" in data["systems"]
        assert data["systems"]["object_storage"]["status"] == "configured"
    
    def test_monitoring_status_overall_operational(self, auth_token):
        """Overall status should be operational"""
        response = requests.get(
            f"{BASE_URL}/api/admin/monitoring/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "operational"


class TestHealthEndpoint:
    """Health check endpoint"""
    
    def test_health_check(self):
        """Health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
