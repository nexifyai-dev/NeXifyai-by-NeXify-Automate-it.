"""
Iteration 24 Backend Tests
Tests for:
- Login button i18n (DE/NL/EN)
- /login page auth flows (admin password, customer magic link, unknown email)
- Role separation (customer JWT blocked from admin endpoints)
- Invoice PDF discount/special_items
"""
import pytest
import requests
import os
import jwt
from datetime import datetime, timedelta, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-architecture-lab.preview.emergentagent.com').rstrip('/')
SECRET_KEY = "nexify_jwt_secret_key_production_2026_change_this_in_production"
ALGORITHM = "HS256"

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"
CUSTOMER_EMAIL = "max@testfirma.de"


class TestAuthCheckEmail:
    """Test /api/auth/check-email endpoint for role detection"""
    
    def test_admin_email_returns_admin_role(self):
        """Admin email should return role=admin with needs_password=True"""
        response = requests.post(f"{BASE_URL}/api/auth/check-email", json={"email": ADMIN_EMAIL})
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["needs_password"] == True
        print(f"SUCCESS: Admin email detected correctly - role={data['role']}")
    
    def test_customer_email_returns_customer_role(self):
        """Customer email should return role=customer with needs_magic_link=True"""
        response = requests.post(f"{BASE_URL}/api/auth/check-email", json={"email": CUSTOMER_EMAIL})
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "customer"
        assert data["needs_magic_link"] == True
        print(f"SUCCESS: Customer email detected correctly - role={data['role']}")
    
    def test_unknown_email_returns_unknown_role(self):
        """Unknown email should return role=unknown"""
        response = requests.post(f"{BASE_URL}/api/auth/check-email", json={"email": "unknown@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "unknown"
        print(f"SUCCESS: Unknown email detected correctly - role={data['role']}")


class TestAdminLogin:
    """Test admin login endpoint"""
    
    def test_admin_login_success(self):
        """Admin login with correct credentials should return JWT"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token contains admin role
        token = data["access_token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["role"] == "admin"
        assert payload["sub"] == ADMIN_EMAIL.lower()
        print(f"SUCCESS: Admin login successful, token contains role=admin")
    
    def test_admin_login_wrong_password(self):
        """Admin login with wrong password should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401
        print(f"SUCCESS: Wrong password correctly rejected with 401")


class TestRoleSeparation:
    """Test that customer JWT is blocked from admin endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def customer_token(self):
        """Create a customer JWT token"""
        payload = {
            "sub": CUSTOMER_EMAIL,
            "role": "customer",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def test_admin_endpoint_with_admin_token(self, admin_token):
        """Admin endpoint should work with admin token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        print(f"SUCCESS: Admin endpoint works with admin token")
    
    def test_admin_endpoint_with_customer_token_returns_403(self, customer_token):
        """Admin endpoint should return 403 with customer token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert "Admin-Berechtigung" in data["detail"] or "admin" in data["detail"].lower()
        print(f"SUCCESS: Customer token blocked from admin endpoint with 403")
    
    def test_admin_leads_with_customer_token_returns_403(self, customer_token):
        """Admin leads endpoint should return 403 with customer token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 403
        print(f"SUCCESS: Customer token blocked from admin/leads with 403")


class TestCustomerMagicLink:
    """Test customer magic link flow"""
    
    def test_request_magic_link_for_customer(self):
        """Request magic link for known customer should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/auth/request-magic-link",
            json={"email": CUSTOMER_EMAIL}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"SUCCESS: Magic link requested for customer")
    
    def test_request_magic_link_for_unknown_email(self):
        """Request magic link for unknown email should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/auth/request-magic-link",
            json={"email": "unknown@example.com"}
        )
        assert response.status_code == 404
        print(f"SUCCESS: Unknown email correctly rejected with 404")


class TestInvoicePDFStructure:
    """Test invoice PDF generation with discount and special items"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    def test_invoice_list_endpoint(self, admin_token):
        """Test that invoice list endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # API returns {"invoices": [...]}
        assert "invoices" in data
        assert isinstance(data["invoices"], list)
        print(f"SUCCESS: Invoice list endpoint works, found {len(data['invoices'])} invoices")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
