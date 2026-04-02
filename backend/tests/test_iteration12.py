"""
NeXifyAI Iteration 12 Backend Tests
Focus: Brand AI highlighting, Chat improvements, Core functionality
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-architecture-lab.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


class TestHealthAndCompany:
    """Basic health and company endpoint tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ Health check passed - version: {data['version']}")
    
    def test_company_endpoint(self):
        """Test company endpoint returns company data"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "NeXifyAI" in data["name"]
        print(f"✓ Company endpoint passed - name: {data['name']}")


class TestChatAPI:
    """Chat API tests - focus on welcome messages and LLM responses"""
    
    def test_chat_message_de(self):
        """Test chat message in German"""
        session_id = f"test_de_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "Hallo, was macht NeXifyAI?",
                "language": "de"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 50  # Should have substantial response
        print(f"✓ Chat DE response received ({len(data['message'])} chars)")
        
        # Check for structured response (should have bold or lists)
        msg = data["message"]
        has_structure = "**" in msg or "- " in msg or "1." in msg
        print(f"  Response has structure: {has_structure}")
    
    def test_chat_message_en(self):
        """Test chat message in English"""
        session_id = f"test_en_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "What does NeXifyAI do?",
                "language": "en"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 50
        print(f"✓ Chat EN response received ({len(data['message'])} chars)")
    
    def test_chat_message_nl(self):
        """Test chat message in Dutch"""
        session_id = f"test_nl_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": session_id,
                "message": "Wat doet NeXifyAI?",
                "language": "nl"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 50
        print(f"✓ Chat NL response received ({len(data['message'])} chars)")


class TestBookingAPI:
    """Booking API tests"""
    
    def test_booking_slots(self):
        """Test booking slots endpoint"""
        # Get tomorrow's date
        import datetime
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.get(f"{BASE_URL}/api/booking/slots?date={tomorrow}")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "date" in data
        print(f"✓ Booking slots for {tomorrow}: {len(data['slots'])} available")
    
    def test_create_booking(self):
        """Test creating a booking"""
        import datetime
        # Find next weekday
        today = datetime.datetime.now()
        days_ahead = 1
        while True:
            next_day = today + datetime.timedelta(days=days_ahead)
            if next_day.weekday() < 5:  # Monday = 0, Friday = 4
                break
            days_ahead += 1
        
        booking_date = next_day.strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/booking",
            json={
                "vorname": "TEST_Iteration12",
                "nachname": "Tester",
                "email": "test_iter12@example.com",
                "telefon": "+31612345678",
                "unternehmen": "Test Company",
                "date": booking_date,
                "time": "10:00",
                "thema": "Iteration 12 Test Booking"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "booking_id" in data
        print(f"✓ Booking created: {data['booking_id']}")


class TestContactAPI:
    """Contact form API tests"""
    
    def test_contact_form(self):
        """Test contact form submission"""
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json={
                "vorname": "TEST_Iteration12",
                "nachname": "Contact",
                "email": "test_contact_iter12@example.com",
                "telefon": "+31612345678",
                "unternehmen": "Test Company",
                "nachricht": "This is a test message from iteration 12 testing. Testing VORNAME/NACHNAME labels.",
                "source": "test_iteration12"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "lead_id" in data
        print(f"✓ Contact form submitted: {data['lead_id']}")


class TestAdminAPI:
    """Admin API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"✓ Admin login successful")
    
    def test_admin_me(self, auth_token):
        """Test admin me endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Admin me endpoint: {data['email']}")
    
    def test_admin_stats(self, auth_token):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "upcoming_bookings" in data
        print(f"✓ Admin stats: {data['total_leads']} leads, {data['upcoming_bookings']} upcoming bookings")
    
    def test_admin_leads(self, auth_token):
        """Test admin leads endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        print(f"✓ Admin leads: {data['total']} total")
    
    def test_admin_bookings(self, auth_token):
        """Test admin bookings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "total" in data
        print(f"✓ Admin bookings: {data['total']} total")


class TestAnalytics:
    """Analytics tracking tests"""
    
    def test_track_event(self):
        """Test analytics tracking"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            json={
                "event": "test_iteration12",
                "properties": {"test": True, "iteration": 12},
                "session_id": f"test_session_{int(time.time())}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✓ Analytics event tracked")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
