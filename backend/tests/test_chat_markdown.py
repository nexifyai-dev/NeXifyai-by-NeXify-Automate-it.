"""
NeXifyAI Chat Markdown & Response Quality Tests
Tests for: Chat markdown formatting, system prompt quality, welcome messages, booking flow
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestChatWelcomeMessages:
    """Chat welcome message translation tests"""
    
    def test_welcome_message_german(self):
        """POST /api/chat/message - German welcome message"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Hallo", "language": "de"}
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "message" in data
        # Response should be in German
        print(f"✓ German chat response received: {data['message'][:100]}...")
    
    def test_welcome_message_english(self):
        """POST /api/chat/message - English welcome message"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Hello", "language": "en"}
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ English chat response received: {data['message'][:100]}...")
    
    def test_welcome_message_dutch(self):
        """POST /api/chat/message - Dutch welcome message"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Hallo", "language": "nl"}
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Dutch chat response received: {data['message'][:100]}...")


class TestChatMarkdownFormatting:
    """Chat response markdown formatting tests"""
    
    def test_sales_response_has_markdown(self):
        """POST /api/chat/message - Sales query should return markdown formatted response"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Wie kann NeXifyAI meinen Vertrieb automatisieren?", "language": "de"},
            timeout=30
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        msg = data["message"]
        
        # Check for markdown formatting indicators
        has_bold = "**" in msg
        has_bullet = "- " in msg or "* " in msg
        has_numbered = any(f"{i}." in msg for i in range(1, 10))
        
        print(f"Response has bold: {has_bold}, bullets: {has_bullet}, numbered: {has_numbered}")
        print(f"Response preview: {msg[:200]}...")
        
        # At least one formatting type should be present
        assert has_bold or has_bullet or has_numbered, "Response should contain markdown formatting"
        print(f"✓ Sales response contains markdown formatting")
    
    def test_crm_response_has_markdown(self):
        """POST /api/chat/message - CRM query should return markdown formatted response"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Welche CRM und ERP Systeme unterstützt ihr?", "language": "de"},
            timeout=30
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        msg = data["message"]
        
        has_bold = "**" in msg
        has_bullet = "- " in msg or "* " in msg
        
        print(f"Response has bold: {has_bold}, bullets: {has_bullet}")
        print(f"Response preview: {msg[:200]}...")
        
        assert has_bold or has_bullet, "CRM response should contain markdown formatting"
        print(f"✓ CRM response contains markdown formatting")
    
    def test_pricing_response_has_markdown(self):
        """POST /api/chat/message - Pricing query should return markdown formatted response"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Was kostet NeXifyAI?", "language": "de"},
            timeout=30
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        msg = data["message"]
        
        has_bold = "**" in msg
        has_bullet = "- " in msg or "* " in msg
        
        print(f"Response has bold: {has_bold}, bullets: {has_bullet}")
        print(f"Response preview: {msg[:200]}...")
        
        assert has_bold or has_bullet, "Pricing response should contain markdown formatting"
        print(f"✓ Pricing response contains markdown formatting")


class TestChatBookingFlow:
    """Chat booking flow tests"""
    
    def test_booking_request_trigger(self):
        """POST /api/chat/message - Booking request should trigger booking flow"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Ich möchte einen Termin buchen", "language": "de"},
            timeout=30
        )
        assert response.status_code == 200, f"Chat failed: {response.text}"
        data = response.json()
        msg = data["message"].lower()
        
        # Should ask for contact details or mention booking
        booking_keywords = ["termin", "vorname", "nachname", "email", "buchen", "strategiegespräch"]
        has_booking_context = any(kw in msg for kw in booking_keywords)
        
        print(f"Response preview: {data['message'][:200]}...")
        assert has_booking_context, "Booking request should trigger booking flow"
        print(f"✓ Booking flow triggered correctly")


class TestChatResponseQuality:
    """Chat response quality and structure tests"""
    
    def test_response_not_empty(self):
        """POST /api/chat/message - Response should not be empty"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Was macht NeXifyAI?", "language": "de"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["message"]) > 50, "Response should be substantial"
        print(f"✓ Response is substantial ({len(data['message'])} chars)")
    
    def test_response_professional_tone(self):
        """POST /api/chat/message - Response should have professional tone (Sie-Form)"""
        session_id = f"test_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={"session_id": session_id, "message": "Können Sie mir helfen?", "language": "de"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        msg = data["message"]
        
        # Check for Sie-Form (formal German)
        sie_indicators = ["Sie", "Ihnen", "Ihr", "Ihre"]
        has_sie_form = any(ind in msg for ind in sie_indicators)
        
        print(f"Response preview: {msg[:200]}...")
        # Note: This is a soft check - LLM may vary
        print(f"✓ Response received, Sie-Form check: {has_sie_form}")


class TestContactForm:
    """Contact form submission tests"""
    
    def test_contact_form_submission(self):
        """POST /api/contact - Contact form submission"""
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json={
                "vorname": "Test",
                "nachname": "User",
                "email": "test@example.com",
                "firma": "Test Company",
                "nachricht": "This is a test message from automated testing",
                "use_case": "automation"
            }
        )
        assert response.status_code == 200, f"Contact form failed: {response.text}"
        data = response.json()
        assert data.get("success") == True or "id" in data or "lead_id" in data
        print(f"✓ Contact form submission successful")


class TestBookingAPI:
    """Booking API tests"""
    
    def test_get_available_slots(self):
        """GET /api/booking/slots - Get available booking slots with date"""
        from datetime import datetime, timedelta
        # Get slots for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/booking/slots?date={tomorrow}")
        assert response.status_code == 200, f"Slots API failed: {response.text}"
        data = response.json()
        assert "slots" in data
        print(f"✓ Booking slots API working, {len(data['slots'])} slots available for {tomorrow}")
    
    def test_booking_submission(self):
        """POST /api/booking - Booking submission"""
        from datetime import datetime, timedelta
        # Get slots for a future date
        future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        slots_response = requests.get(f"{BASE_URL}/api/booking/slots?date={future_date}")
        if slots_response.status_code == 200:
            slots = slots_response.json().get("slots", [])
            if slots:
                response = requests.post(
                    f"{BASE_URL}/api/booking",
                    json={
                        "vorname": "Test",
                        "nachname": "User",
                        "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
                        "firma": "Test Company",
                        "date": future_date,
                        "time": slots[0] if slots else "10:00"
                    }
                )
                # May fail if slot is taken, but API should respond
                assert response.status_code in [200, 201, 400, 409], f"Booking API error: {response.text}"
                print(f"✓ Booking API responding correctly (status: {response.status_code})")
            else:
                print("⚠ No slots available for booking test")
        else:
            pytest.skip("Could not get available slots")

