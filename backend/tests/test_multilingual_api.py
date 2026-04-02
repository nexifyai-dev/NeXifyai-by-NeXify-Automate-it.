"""
NeXifyAI Multilingual API Tests
Tests for:
- Chat endpoint with language parameter (DE/NL/EN)
- Admin login and dashboard
- Contact form
- Booking endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://e511dfe9-fc84-4edd-9e5e-6ba9f2cea19f.preview.emergentagent.com')
BASE_URL = BASE_URL.rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


class TestHealthAndCompany:
    """Basic health and company info tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ Health check passed: {data}")
    
    def test_company_endpoint(self):
        """Test /api/company returns company info"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NeXifyAI by NeXify"
        assert "kvk" in data
        print(f"✓ Company info: {data['name']}")


class TestChatWithLanguage:
    """Test chat endpoint with language parameter - NEW FEATURE"""
    
    def test_chat_german(self):
        """Test chat with German language parameter"""
        session_id = f"test_de_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Was bietet ihr an?",
            "language": "de"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        print(f"✓ German chat response received ({len(data['message'])} chars)")
    
    def test_chat_english(self):
        """Test chat with English language parameter"""
        session_id = f"test_en_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What services do you offer?",
            "language": "en"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        print(f"✓ English chat response received ({len(data['message'])} chars)")
    
    def test_chat_dutch(self):
        """Test chat with Dutch language parameter"""
        session_id = f"test_nl_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Welke diensten bieden jullie aan?",
            "language": "nl"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        print(f"✓ Dutch chat response received ({len(data['message'])} chars)")
    
    def test_chat_default_language(self):
        """Test chat without language parameter defaults to German"""
        session_id = f"test_default_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Hallo"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Default language chat works")


class TestAdminAuth:
    """Test admin authentication"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"✓ Admin login successful, token received")
        return data["access_token"]
    
    def test_admin_login_invalid(self):
        """Test admin login with wrong credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "wrong@email.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401
        print(f"✓ Invalid login correctly rejected")
    
    def test_admin_me_endpoint(self):
        """Test /api/admin/me with valid token"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = login_response.json()["access_token"]
        
        # Then check /me
        response = requests.get(
            f"{BASE_URL}/api/admin/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Admin /me endpoint works: {data['email']}")
    
    def test_admin_stats(self):
        """Test /api/admin/stats with valid token"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = login_response.json()["access_token"]
        
        # Then check stats
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "upcoming_bookings" in data
        print(f"✓ Admin stats: {data['total_leads']} leads, {data['upcoming_bookings']} upcoming bookings")


class TestContactForm:
    """Test contact form submission"""
    
    def test_contact_form_success(self):
        """Test successful contact form submission"""
        response = requests.post(f"{BASE_URL}/api/contact", json={
            "vorname": "Test",
            "nachname": "User",
            "email": f"test_{int(time.time())}@example.com",
            "telefon": "+31612345678",
            "unternehmen": "Test Company",
            "nachricht": "This is a test message for multilingual testing.",
            "source": "test",
            "consent": True,
            "datenschutz_akzeptiert": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "lead_id" in data
        print(f"✓ Contact form submitted: {data['lead_id']}")
    
    def test_contact_form_validation(self):
        """Test contact form validation"""
        response = requests.post(f"{BASE_URL}/api/contact", json={
            "vorname": "T",  # Too short
            "nachname": "User",
            "email": "invalid-email",  # Invalid email
            "nachricht": "Short"  # Too short
        })
        assert response.status_code == 422  # Validation error
        print(f"✓ Contact form validation works")


class TestBooking:
    """Test booking endpoints"""
    
    def test_get_booking_slots(self):
        """Test getting available booking slots"""
        # Get slots for tomorrow
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.get(f"{BASE_URL}/api/booking/slots?date={tomorrow}")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "date" in data
        print(f"✓ Booking slots for {tomorrow}: {len(data['slots'])} available")
    
    def test_create_booking(self):
        """Test creating a booking"""
        from datetime import datetime, timedelta
        
        # Find next weekday
        test_date = datetime.now() + timedelta(days=3)
        while test_date.weekday() >= 5:  # Skip weekends
            test_date += timedelta(days=1)
        
        response = requests.post(f"{BASE_URL}/api/booking", json={
            "vorname": "Test",
            "nachname": "Booking",
            "email": f"test_booking_{int(time.time())}@example.com",
            "telefon": "+31612345678",
            "unternehmen": "Test Company",
            "date": test_date.strftime("%Y-%m-%d"),
            "time": "10:00",
            "thema": "Multilingual test booking",
            "datenschutz_akzeptiert": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "booking_id" in data
        print(f"✓ Booking created: {data['booking_id']}")


class TestAnalytics:
    """Test analytics tracking"""
    
    def test_track_event(self):
        """Test analytics event tracking"""
        response = requests.post(f"{BASE_URL}/api/analytics/track", json={
            "event": "test_event",
            "properties": {"test": True, "language": "de"},
            "session_id": f"test_session_{int(time.time())}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✓ Analytics event tracked")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
