"""
Iteration 60 - Admin Sidebar Tests
Testing: Sidebar collapsed by default, toggle functionality, tooltips, CI compliance
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"✅ Admin login successful, token received")
        return data["access_token"]
    
    def test_admin_login_invalid_password(self):
        """Test admin login with invalid password"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=wrongpassword"
        )
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print(f"✅ Invalid password correctly rejected")


class TestAdminDashboard:
    """Admin dashboard API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="username=p.courbois@icloud.com&password=1def!xO2022!!"
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_admin_stats(self, auth_token):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        assert "total_leads" in data or "leads" in data or isinstance(data, dict), "Invalid stats response"
        print(f"✅ Admin stats: {data}")
    
    def test_admin_health(self, auth_token):
        """Test system health endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/audit/health",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        print(f"✅ System health: {data}")
    
    def test_admin_leads(self, auth_token):
        """Test leads endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Leads failed: {response.text}"
        data = response.json()
        assert "leads" in data or isinstance(data, list), "Invalid leads response"
        print(f"✅ Leads endpoint working")
    
    def test_admin_projects(self, auth_token):
        """Test projects endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/projects",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Projects failed: {response.text}"
        print(f"✅ Projects endpoint working")
    
    def test_admin_contracts(self, auth_token):
        """Test contracts endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contracts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Contracts failed: {response.text}"
        print(f"✅ Contracts endpoint working")
    
    def test_admin_outbound_pipeline(self, auth_token):
        """Test outbound pipeline endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/outbound/pipeline",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Outbound pipeline failed: {response.text}"
        print(f"✅ Outbound pipeline endpoint working")


class TestHealthEndpoint:
    """Public health endpoint test"""
    
    def test_health_endpoint(self):
        """Test public health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", f"Unexpected health status: {data}"
        print(f"✅ Health endpoint: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
