"""
Iteration 44: Booking Modal, Chat, Contact Form, Legal Pages API Tests
Tests for:
- API 1: /api/health returns 200 with status 'healthy'
- API 2: /api/booking/slots?date=2026-04-10 returns 200 with slots array
- API 3: /api/product/tariffs returns 200
- CHAT 4: POST /api/chat/message returns valid response
- CONTACT 1: Contact form submits with source='contact_form' and language='de'
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAPI:
    """API 1: Health endpoint tests"""
    
    def test_health_returns_200(self):
        """API 1 - /api/health returns 200 with status 'healthy'"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "healthy", f"Expected status 'healthy', got {data.get('status')}"
        assert "version" in data, "Response should contain version"
        assert "timestamp" in data, "Response should contain timestamp"
        print(f"PASSED: Health API returns 200 with status=healthy, version={data.get('version')}")


class TestBookingAPI:
    """API 2: Booking slots endpoint tests"""
    
    def test_booking_slots_returns_200(self):
        """API 2 - /api/booking/slots?date=2026-04-10 returns 200 with slots array"""
        response = requests.get(f"{BASE_URL}/api/booking/slots?date=2026-04-10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "date" in data, "Response should contain date"
        assert "slots" in data, "Response should contain slots"
        assert isinstance(data["slots"], list), "Slots should be a list"
        print(f"PASSED: Booking slots API returns 200 with {len(data['slots'])} slots for 2026-04-10")
    
    def test_booking_slots_weekday(self):
        """Test booking slots for a weekday returns available times"""
        # 2026-04-13 is a Monday
        response = requests.get(f"{BASE_URL}/api/booking/slots?date=2026-04-13")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2026-04-13"
        # Should have some slots available
        print(f"PASSED: Booking slots for 2026-04-13 (Monday) returns {len(data['slots'])} slots")


class TestTariffsAPI:
    """API 3: Product tariffs endpoint tests"""
    
    def test_tariffs_returns_200(self):
        """API 3 - /api/product/tariffs returns 200"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "tariffs" in data, "Response should contain tariffs"
        assert "company" in data, "Response should contain company info"
        assert "currency" in data, "Response should contain currency"
        assert data["currency"] == "EUR", "Currency should be EUR"
        print(f"PASSED: Tariffs API returns 200 with {len(data['tariffs'])} tariffs")
    
    def test_tariffs_structure(self):
        """Verify tariff structure contains required fields"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        data = response.json()
        tariffs = data.get("tariffs", {})
        if tariffs:
            first_tariff = list(tariffs.values())[0]
            required_fields = ["tariff_number", "name", "reference_monthly_eur", "features"]
            for field in required_fields:
                assert field in first_tariff, f"Tariff should contain {field}"
        print(f"PASSED: Tariff structure verified with required fields")


class TestChatAPI:
    """CHAT 4: Chat message endpoint tests"""
    
    def test_chat_message_returns_valid_response(self):
        """CHAT 4 - POST /api/chat/message returns valid response"""
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        payload = {
            "session_id": session_id,
            "message": "Hallo, ich interessiere mich für KI-Automation",
            "language": "de"
        }
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert isinstance(data["message"], str), "Message should be a string"
        assert len(data["message"]) > 0, "Message should not be empty"
        print(f"PASSED: Chat API returns valid response with message length {len(data['message'])}")
    
    def test_chat_message_with_context(self):
        """Test chat message with context parameter"""
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        payload = {
            "session_id": session_id,
            "message": "Was kostet ein KI-Agent?",
            "language": "de",
            "context": {"source": "test"}
        }
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "qualification" in data
        print(f"PASSED: Chat API with context returns valid response")


class TestContactAPI:
    """CONTACT 1: Contact form endpoint tests"""
    
    def test_contact_form_with_source_and_language(self):
        """CONTACT 1 - Contact form submits with source='contact_form' and language='de'"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "vorname": "Test",
            "nachname": "User",
            "email": f"test-{unique_id}@example.com",
            "telefon": "+49123456789",
            "unternehmen": "Test GmbH",
            "nachricht": "Dies ist eine Testnachricht für die Kontaktformular-Validierung.",
            "source": "contact_form",
            "language": "de",
            "consent": True,
            "datenschutz_akzeptiert": True
        }
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert "lead_id" in data, "Response should contain lead_id"
        print(f"PASSED: Contact form submitted successfully with lead_id={data.get('lead_id')}")
    
    def test_contact_form_validation(self):
        """Test contact form validation for required fields"""
        payload = {
            "vorname": "T",  # Too short
            "nachname": "User",
            "email": "invalid-email",  # Invalid email
            "nachricht": "Short",  # Too short
            "source": "contact_form",
            "language": "de"
        }
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        print(f"PASSED: Contact form validation works correctly")


class TestCompanyAPI:
    """Additional API tests for company info"""
    
    def test_company_info(self):
        """Test /api/company returns company information"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "email" in data
        assert "phone" in data
        print(f"PASSED: Company API returns valid info: {data.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
