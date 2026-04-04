"""
Iteration 54 - Backend API Tests
Testing critical bug fixes:
1. Login flow and token validation
2. Dashboard stats API (leads_total, leads_new, bookings_total, chat_sessions_total)
3. Admin endpoints authentication
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
            data={
                "username": "p.courbois@icloud.com",
                "password": "1def!xO2022!!"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert len(data["access_token"]) > 0, "Empty access_token"
        print(f"✓ Admin login successful, token length: {len(data['access_token'])}")
    
    def test_admin_login_invalid_credentials(self):
        """Test admin login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "invalid@test.com",
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected with 401")
    
    def test_protected_endpoint_without_token(self):
        """Test that protected endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Protected endpoint correctly requires authentication")


class TestDashboardStats:
    """Dashboard stats API tests - verifying bug fix for stats showing 0"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "p.courbois@icloud.com",
                "password": "1def!xO2022!!"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_stats_endpoint_returns_correct_fields(self, auth_token):
        """Test that stats endpoint returns all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Stats endpoint failed: {response.text}"
        data = response.json()
        
        # Check for required fields (bug fix: frontend reads leads_total, not total_leads)
        required_fields = ["leads_total", "leads_new", "bookings_total", "chat_sessions_total", "recent_leads"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ Stats endpoint returns all required fields")
        print(f"  leads_total: {data['leads_total']}")
        print(f"  leads_new: {data['leads_new']}")
        print(f"  bookings_total: {data['bookings_total']}")
        print(f"  chat_sessions_total: {data['chat_sessions_total']}")
    
    def test_stats_values_are_non_negative(self, auth_token):
        """Test that stats values are non-negative integers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["leads_total"] >= 0, "leads_total should be non-negative"
        assert data["leads_new"] >= 0, "leads_new should be non-negative"
        assert data["bookings_total"] >= 0, "bookings_total should be non-negative"
        assert data["chat_sessions_total"] >= 0, "chat_sessions_total should be non-negative"
        
        print("✓ All stats values are non-negative")
    
    def test_stats_has_real_data(self, auth_token):
        """Test that stats show real data (not all zeros)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # At least one stat should be > 0 (we know there's data in the system)
        total_stats = data["leads_total"] + data["bookings_total"] + data["chat_sessions_total"]
        assert total_stats > 0, "All stats are 0 - data might not be loading correctly"
        
        # Based on previous tests, we expect at least 71 leads
        assert data["leads_total"] >= 70, f"Expected at least 70 leads, got {data['leads_total']}"
        
        print(f"✓ Stats show real data (total leads: {data['leads_total']})")
    
    def test_recent_leads_has_data(self, auth_token):
        """Test that recent_leads array has data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "recent_leads" in data, "Missing recent_leads field"
        assert isinstance(data["recent_leads"], list), "recent_leads should be a list"
        assert len(data["recent_leads"]) > 0, "recent_leads should not be empty"
        
        # Check first lead has required fields
        first_lead = data["recent_leads"][0]
        lead_fields = ["email", "status", "created_at"]
        for field in lead_fields:
            assert field in first_lead, f"Lead missing field: {field}"
        
        print(f"✓ recent_leads has {len(data['recent_leads'])} leads with correct structure")


class TestLeadsAPI:
    """Leads API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "p.courbois@icloud.com",
                "password": "1def!xO2022!!"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_leads(self, auth_token):
        """Test getting leads list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get leads failed: {response.text}"
        data = response.json()
        
        assert "leads" in data, "Missing leads field"
        assert "total" in data, "Missing total field"
        assert isinstance(data["leads"], list), "leads should be a list"
        
        print(f"✓ Get leads successful: {data['total']} total leads")


class TestCustomersAPI:
    """Customers API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "p.courbois@icloud.com",
                "password": "1def!xO2022!!"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_customers(self, auth_token):
        """Test getting customers list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/customers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get customers failed: {response.text}"
        data = response.json()
        
        assert "customers" in data, "Missing customers field"
        assert isinstance(data["customers"], list), "customers should be a list"
        
        print(f"✓ Get customers successful: {len(data['customers'])} customers")
    
    def test_get_customer_casefile(self, auth_token):
        """Test getting customer casefile"""
        # First get a customer email
        response = requests.get(
            f"{BASE_URL}/api/admin/customers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        customers = response.json().get("customers", [])
        
        if not customers:
            pytest.skip("No customers to test casefile")
        
        customer_email = customers[0]["email"]
        
        # Get casefile
        response = requests.get(
            f"{BASE_URL}/api/admin/customers/{customer_email}/casefile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get casefile failed: {response.text}"
        data = response.json()
        
        # Check casefile structure
        required_fields = ["email", "leads", "bookings", "quotes", "invoices", "contracts", "stats"]
        for field in required_fields:
            assert field in data, f"Casefile missing field: {field}"
        
        # Check stats structure
        stats = data["stats"]
        stats_fields = ["total_leads", "total_bookings", "total_quotes", "total_invoices", "total_contracts", "total_emails"]
        for field in stats_fields:
            assert field in stats, f"Stats missing field: {field}"
        
        print(f"✓ Customer casefile loaded for {customer_email}")
        print(f"  Stats: {stats}")


class TestBookingsAPI:
    """Bookings API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "p.courbois@icloud.com",
                "password": "1def!xO2022!!"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_bookings(self, auth_token):
        """Test getting bookings list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get bookings failed: {response.text}"
        data = response.json()
        
        assert "bookings" in data, "Missing bookings field"
        assert "total" in data, "Missing total field"
        
        print(f"✓ Get bookings successful: {data['total']} total bookings")


class TestTokenValidation:
    """Token validation tests - verifying login loop fix"""
    
    def test_invalid_token_returns_401(self):
        """Test that invalid token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("✓ Invalid token correctly returns 401")
    
    def test_expired_token_format_returns_401(self):
        """Test that malformed token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjoxfQ.invalid"}
        )
        assert response.status_code == 401, f"Expected 401 for malformed token, got {response.status_code}"
        print("✓ Malformed token correctly returns 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
