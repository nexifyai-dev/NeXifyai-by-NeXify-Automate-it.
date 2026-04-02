"""
NeXifyAI Backend Tests - Iteration 10
Testing chat API, booking API, contact API, and admin endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-architecture-lab.preview.emergentagent.com')

class TestHealthAndBasics:
    """Basic health and company endpoints"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ Health check passed - version: {data['version']}")
    
    def test_company_endpoint(self):
        """Test company info endpoint"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NeXifyAI by NeXify"
        assert "email" in data
        print("✓ Company endpoint working")


class TestChatAPI:
    """Chat API tests - LLM-powered responses"""
    
    def test_chat_message_german(self):
        """Test chat message in German"""
        session_id = f"test_session_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "Was bietet ihr an?",
                "language": "de"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 50  # Should have substantial response
        print(f"✓ German chat response received ({len(data['message'])} chars)")
    
    def test_chat_message_english(self):
        """Test chat message in English"""
        session_id = f"test_session_en_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "What services do you offer?",
                "language": "en"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ English chat response received ({len(data['message'])} chars)")
    
    def test_chat_booking_request(self):
        """Test chat booking request triggers booking flow"""
        session_id = f"test_booking_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "Ich möchte einen Termin buchen",
                "language": "de"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should ask for name/email
        msg_lower = data["message"].lower()
        assert any(kw in msg_lower for kw in ["vorname", "nachname", "e-mail", "name"])
        print("✓ Booking request triggers name/email collection")


class TestBookingAPI:
    """Booking API tests"""
    
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
        print(f"✓ Booking slots retrieved for {tomorrow}: {len(data['slots'])} slots")
    
    def test_create_booking(self):
        """Test creating a booking"""
        from datetime import datetime, timedelta
        
        # Find next weekday
        test_date = datetime.now() + timedelta(days=3)
        while test_date.weekday() >= 5:  # Skip weekends
            test_date += timedelta(days=1)
        
        booking_data = {
            "vorname": "TEST_Booking",
            "nachname": "User",
            "email": f"test_booking_{int(time.time())}@example.com",
            "telefon": "+49123456789",
            "unternehmen": "Test Company",
            "date": test_date.strftime("%Y-%m-%d"),
            "time": "10:00",
            "thema": "Test booking"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/booking",
            json=booking_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "booking_id" in data
        print(f"✓ Booking created: {data['booking_id']}")


class TestContactAPI:
    """Contact form API tests"""
    
    def test_submit_contact_form(self):
        """Test contact form submission"""
        contact_data = {
            "vorname": "TEST_Contact",
            "nachname": "User",
            "email": f"test_contact_{int(time.time())}@example.com",
            "telefon": "+49123456789",
            "unternehmen": "Test Company",
            "nachricht": "This is a test message from automated testing. Please ignore.",
            "source": "test",
            "consent": True,
            "datenschutz_akzeptiert": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json=contact_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "lead_id" in data
        print(f"✓ Contact form submitted: {data['lead_id']}")


class TestAdminAPI:
    """Admin API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "p.courbois@icloud.com",
                "password": "NxAi#Secure2026!"
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Admin login failed")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": "p.courbois@icloud.com",
                "password": "NxAi#Secure2026!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print("✓ Admin login successful")
    
    def test_admin_stats(self, admin_token):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "upcoming_bookings" in data
        print(f"✓ Admin stats: {data['total_leads']} leads, {data['upcoming_bookings']} bookings")
    
    def test_admin_leads(self, admin_token):
        """Test admin leads endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        print(f"✓ Admin leads: {data['total']} total")
    
    def test_admin_bookings(self, admin_token):
        """Test admin bookings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "total" in data
        print(f"✓ Admin bookings: {data['total']} total")


class TestAnalytics:
    """Analytics tracking tests"""
    
    def test_track_event(self):
        """Test analytics event tracking"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            json={
                "event": "test_event",
                "properties": {"test": True},
                "session_id": f"test_session_{int(time.time())}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✓ Analytics event tracked")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
