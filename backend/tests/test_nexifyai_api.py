"""
NeXifyAI Backend API Tests - Iteration 5
Tests all critical endpoints: health, contact, booking, chat, admin auth
"""
import pytest
import requests
import os
import time
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://e511dfe9-fc84-4edd-9e5e-6ba9f2cea19f.preview.emergentagent.com')
BASE_URL = BASE_URL.rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_returns_200(self):
        """Health endpoint should return 200 with status healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        print(f"✓ Health check passed: {data}")


class TestCompanyEndpoint:
    """Company info endpoint tests"""
    
    def test_company_returns_info(self):
        """Company endpoint should return company details"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NeXifyAI by NeXify"
        assert data["tagline"] == "Chat it. Automate it."
        assert "kvk" in data
        assert "vat_id" in data
        print(f"✓ Company info: {data['name']}")


class TestContactEndpoint:
    """Contact form submission tests"""
    
    def test_contact_form_success(self):
        """Contact form should accept valid data"""
        payload = {
            "vorname": "TEST_Max",
            "nachname": "TEST_Mustermann",
            "email": f"test_{int(time.time())}@example.com",
            "telefon": "+49 123 456789",
            "unternehmen": "Test GmbH",
            "nachricht": "Dies ist eine Testanfrage für die API-Validierung. Mindestens 10 Zeichen.",
            "consent": True,
            "datenschutz_akzeptiert": True
        }
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "lead_id" in data
        assert data["lead_id"].startswith("LEAD-")
        print(f"✓ Contact form submitted: {data['lead_id']}")
    
    def test_contact_form_validation_error(self):
        """Contact form should reject invalid data"""
        payload = {
            "vorname": "X",  # Too short
            "nachname": "Y",  # Too short
            "email": "invalid-email",
            "nachricht": "Short"  # Too short
        }
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        assert response.status_code == 422  # Validation error
        print("✓ Contact form validation works")
    
    def test_contact_honeypot_silent_success(self):
        """Honeypot field should silently succeed"""
        payload = {
            "vorname": "Bot",
            "nachname": "Spammer",
            "email": "bot@spam.com",
            "nachricht": "This is spam message with honeypot filled",
            "_hp": "filled_by_bot"  # Honeypot field
        }
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        # Should NOT have lead_id (silently rejected)
        print("✓ Honeypot protection works")


class TestBookingEndpoint:
    """Booking system tests"""
    
    def test_get_available_slots(self):
        """Should return available time slots for a date"""
        # Get a date 3 days from now (weekday)
        future_date = datetime.now() + timedelta(days=3)
        while future_date.weekday() >= 5:  # Skip weekends
            future_date += timedelta(days=1)
        date_str = future_date.strftime("%Y-%m-%d")
        
        response = requests.get(f"{BASE_URL}/api/booking/slots?date={date_str}")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert isinstance(data["slots"], list)
        assert len(data["slots"]) > 0
        print(f"✓ Available slots for {date_str}: {len(data['slots'])} slots")
    
    def test_create_booking_success(self):
        """Should create a booking successfully"""
        # Get a date 5 days from now (weekday)
        future_date = datetime.now() + timedelta(days=5)
        while future_date.weekday() >= 5:
            future_date += timedelta(days=1)
        date_str = future_date.strftime("%Y-%m-%d")
        
        # Get available slots first
        slots_response = requests.get(f"{BASE_URL}/api/booking/slots?date={date_str}")
        slots = slots_response.json().get("slots", ["10:00"])
        time_slot = slots[0] if slots else "10:00"
        
        payload = {
            "vorname": "TEST_Booking",
            "nachname": "TEST_User",
            "email": f"test_booking_{int(time.time())}@example.com",
            "telefon": "+49 123 456789",
            "unternehmen": "Test Booking GmbH",
            "date": date_str,
            "time": time_slot,
            "thema": "KI-Assistenz / Chatbot"
        }
        response = requests.post(f"{BASE_URL}/api/booking", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "booking_id" in data
        assert data["booking_id"].startswith("BK-")
        print(f"✓ Booking created: {data['booking_id']} for {date_str} at {time_slot}")
    
    def test_booking_validation_error(self):
        """Should reject invalid booking data"""
        payload = {
            "vorname": "X",  # Too short
            "nachname": "Y",  # Too short
            "email": "invalid",
            "date": "2026-04-10",
            "time": "10:00"
        }
        response = requests.post(f"{BASE_URL}/api/booking", json=payload)
        assert response.status_code == 422
        print("✓ Booking validation works")


class TestChatEndpoint:
    """Chat/LLM endpoint tests"""
    
    def test_chat_message_success(self):
        """Chat should return LLM response"""
        session_id = f"test_session_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "Was sind eure Leistungen?"
        }
        response = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 10  # Should have substantial response
        assert "qualification" in data
        print(f"✓ Chat response received: {data['message'][:100]}...")
    
    def test_chat_qualification_detection(self):
        """Chat should detect use case from message"""
        session_id = f"test_qual_{int(time.time())}"
        payload = {
            "session_id": session_id,
            "message": "Wir brauchen eine SAP Integration für unser CRM"
        }
        response = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Should detect SAP or CRM use case
        qual = data.get("qualification", {})
        print(f"✓ Chat qualification: {qual}")


class TestAnalyticsEndpoint:
    """Analytics tracking tests"""
    
    def test_track_event(self):
        """Should track analytics event"""
        payload = {
            "event": "test_event",
            "properties": {"test": True, "source": "pytest"},
            "session_id": f"test_analytics_{int(time.time())}"
        }
        response = requests.post(f"{BASE_URL}/api/analytics/track", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✓ Analytics event tracked")


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Admin login should return JWT token"""
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
    
    def test_admin_login_invalid_credentials(self):
        """Admin login should reject invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": "wrong@email.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401
        print("✓ Invalid credentials rejected")
    
    def test_admin_me_with_token(self):
        """Admin /me endpoint should return user info with valid token"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = login_response.json()["access_token"]
        
        # Then get /me
        response = requests.get(
            f"{BASE_URL}/api/admin/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert "role" in data
        print(f"✓ Admin /me: {data}")
    
    def test_admin_me_without_token(self):
        """Admin /me should reject without token"""
        response = requests.get(f"{BASE_URL}/api/admin/me")
        assert response.status_code == 401
        print("✓ Unauthenticated request rejected")


class TestAdminDashboard:
    """Admin dashboard endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin tests"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    def test_admin_stats(self, auth_token):
        """Admin stats should return dashboard data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "new_leads_today" in data
        assert "upcoming_bookings" in data
        assert "by_status" in data
        print(f"✓ Admin stats: {data['total_leads']} total leads, {data['upcoming_bookings']} upcoming bookings")
    
    def test_admin_leads_list(self, auth_token):
        """Admin leads list should return leads"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "leads" in data
        assert isinstance(data["leads"], list)
        print(f"✓ Admin leads: {data['total']} total leads")
    
    def test_admin_bookings_list(self, auth_token):
        """Admin bookings list should return bookings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "bookings" in data
        assert isinstance(data["bookings"], list)
        print(f"✓ Admin bookings: {data['total']} total bookings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
