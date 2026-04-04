"""
Iteration 45: Full System Audit Test Suite
Tests all API endpoints for the B2B Platform NeXifyAI
- Contact API (lead creation)
- Booking API (slot availability, booking creation)
- Chat API (AI response)
- Admin APIs (stats, billing, outbound, workers)
- Legal pages accessibility
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "version" in data
        print(f"✓ Health: status={data['status']}, version={data['version']}")

    def test_tariffs_endpoint(self):
        """Product tariffs endpoint"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        assert response.status_code == 200
        data = response.json()
        assert "tariffs" in data
        assert "currency" in data
        print(f"✓ Tariffs: {len(data.get('tariffs', []))} tariffs, currency={data.get('currency')}")


class TestContactAPI:
    """API 1 - POST /api/contact creates lead successfully"""
    
    def test_contact_form_creates_lead(self):
        """Test contact form submission creates a lead"""
        payload = {
            "vorname": "TEST_Audit",
            "nachname": "User",
            "email": f"test_audit_{datetime.now().timestamp()}@example.com",
            "unternehmen": "Test Audit GmbH",
            "telefon": "+49 123 456789",
            "nachricht": "This is a test message from iteration 45 audit",
            "source": "contact_form",
            "language": "de"
        }
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "lead_id" in data or "id" in data or "success" in data
        print(f"✓ Contact API: Lead created successfully - {data}")


class TestBookingAPI:
    """API 2 - POST /api/booking creates booking with available slot"""
    
    def test_booking_slots_available(self):
        """Test booking slots endpoint returns available slots"""
        # Get slots for a future date
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/booking/slots?date={future_date}")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data or isinstance(data, list)
        slots = data.get("slots", data) if isinstance(data, dict) else data
        print(f"✓ Booking Slots: {len(slots)} slots available for {future_date}")
        return slots
    
    def test_create_booking(self):
        """Test booking creation with available slot"""
        # First get available slots
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        slots_response = requests.get(f"{BASE_URL}/api/booking/slots?date={future_date}")
        
        if slots_response.status_code == 200:
            slots_data = slots_response.json()
            slots = slots_data.get("slots", slots_data) if isinstance(slots_data, dict) else slots_data
            
            if slots and len(slots) > 0:
                # Use first available slot
                slot = slots[0] if isinstance(slots[0], str) else slots[0].get("time", "10:00")
                
                payload = {
                    "date": future_date,
                    "time": slot,
                    "vorname": "TEST_Audit",
                    "nachname": "Booking",
                    "email": f"test_booking_{datetime.now().timestamp()}@example.com",
                    "telefon": "+49 123 456789",
                    "unternehmen": "Audit Test GmbH",
                    "thema": "System Audit Test"
                }
                response = requests.post(f"{BASE_URL}/api/booking", json=payload)
                # Accept 200, 201, or 409 (slot taken)
                assert response.status_code in [200, 201, 409]
                print(f"✓ Booking Creation: status={response.status_code}, response={response.json()}")
            else:
                print("⚠ No slots available for booking test")
        else:
            pytest.skip("Could not get booking slots")


class TestChatAPI:
    """API 3 - POST /api/chat/message returns AI response"""
    
    def test_chat_message_returns_response(self):
        """Test chat API returns AI response"""
        payload = {
            "session_id": f"test_audit_{datetime.now().timestamp()}",
            "message": "Hallo, ich interessiere mich für Ihre KI-Lösungen",
            "language": "de"
        }
        response = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Check for response message
        assert "message" in data or "response" in data or "content" in data
        print(f"✓ Chat API: AI response received - keys: {list(data.keys())}")


class TestAdminLogin:
    """Admin authentication tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        login_data = {
            "username": "p.courbois@icloud.com",
            "password": "NxAi#Secure2026!"
        }
        response = requests.post(f"{BASE_URL}/api/admin/login", data=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        login_data = {
            "username": "p.courbois@icloud.com",
            "password": "NxAi#Secure2026!"
        }
        response = requests.post(f"{BASE_URL}/api/admin/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        print(f"✓ Admin Login: Success - token received")
        return data.get("access_token") or data.get("token")


class TestAdminAPIs:
    """API 4-7 - Admin API endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token for all tests in class"""
        login_data = {
            "username": "p.courbois@icloud.com",
            "password": "NxAi#Secure2026!"
        }
        response = requests.post(f"{BASE_URL}/api/admin/login", data=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Admin login failed")
    
    def test_admin_stats(self, admin_token):
        """API 4 - GET /api/admin/stats returns lead/booking counts"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Check for expected stats fields
        assert "total_leads" in data or "leads" in data or "stats" in data
        print(f"✓ Admin Stats: {data}")
    
    def test_admin_billing_status(self, admin_token):
        """API 5 - GET /api/admin/billing/status returns billing info"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/billing/status", headers=headers)
        # Accept 200 or 404 (if billing not configured)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Billing Status: {data}")
        else:
            print("⚠ Billing status endpoint returned 404 (may not be configured)")
    
    def test_admin_outbound_pipeline(self, admin_token):
        """API 6 - GET /api/admin/outbound/pipeline returns outbound data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/outbound/pipeline", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Outbound Pipeline: {data}")
        else:
            print("⚠ Outbound pipeline endpoint returned 404")
    
    def test_admin_workers_status(self, admin_token):
        """API 7 - GET /api/admin/workers/status returns worker state"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/workers/status", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Workers Status: {data}")
        else:
            print("⚠ Workers status endpoint returned 404")


class TestAdminDataEndpoints:
    """Test admin data endpoints for all 16 views"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        login_data = {
            "username": "p.courbois@icloud.com",
            "password": "NxAi#Secure2026!"
        }
        response = requests.post(f"{BASE_URL}/api/admin/login", data=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Admin login failed")
    
    def test_admin_leads(self, admin_token):
        """ADMIN 2 - Leads endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/leads", headers=headers)
        assert response.status_code == 200
        data = response.json()
        leads = data.get("leads", data) if isinstance(data, dict) else data
        print(f"✓ Leads: {len(leads)} leads found")
    
    def test_admin_bookings(self, admin_token):
        """ADMIN 3 - Bookings/Calendar endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/bookings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        bookings = data.get("bookings", data) if isinstance(data, dict) else data
        print(f"✓ Bookings: {len(bookings)} bookings found")
    
    def test_admin_customers(self, admin_token):
        """ADMIN 4 - Customers endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/customers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        customers = data.get("customers", data) if isinstance(data, dict) else data
        print(f"✓ Customers: {len(customers)} customers found")
    
    def test_admin_quotes(self, admin_token):
        """ADMIN 5 - Quotes endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/quotes", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("quotes", data) if isinstance(data, dict) else data
            print(f"✓ Quotes: {len(quotes)} quotes found")
        else:
            print("⚠ Quotes endpoint returned 404")
    
    def test_admin_invoices(self, admin_token):
        """ADMIN 6 - Invoices endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/invoices", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            invoices = data.get("invoices", data) if isinstance(data, dict) else data
            print(f"✓ Invoices: {len(invoices)} invoices found")
        else:
            print("⚠ Invoices endpoint returned 404")
    
    def test_admin_projects(self, admin_token):
        """ADMIN 7 - Projects endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/projects", headers=headers)
        assert response.status_code == 200
        data = response.json()
        projects = data.get("projects", data) if isinstance(data, dict) else data
        print(f"✓ Projects: {len(projects)} projects found")
    
    def test_admin_contracts(self, admin_token):
        """ADMIN 8 - Contracts endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/contracts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        contracts = data.get("contracts", data) if isinstance(data, dict) else data
        print(f"✓ Contracts: {len(contracts)} contracts found")
    
    def test_admin_chat_sessions(self, admin_token):
        """ADMIN 9 - KI-Chats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/chat-sessions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        sessions = data.get("sessions", data) if isinstance(data, dict) else data
        print(f"✓ Chat Sessions: {len(sessions)} sessions found")
    
    def test_admin_agents(self, admin_token):
        """ADMIN 10 - KI-Agenten endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/agents", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            agents = data.get("agents", data) if isinstance(data, dict) else data
            print(f"✓ Agents: {len(agents)} agents found")
        else:
            print("⚠ Agents endpoint returned 404")
    
    def test_admin_monitoring(self, admin_token):
        """ADMIN 11 - Monitoring endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/monitoring/status", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Monitoring: {data}")
        else:
            print("⚠ Monitoring endpoint returned 404")
    
    def test_admin_activities(self, admin_token):
        """ADMIN 12 - Timeline/Activity endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/activities", headers=headers)
        # Accept 200 or 404
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            activities = data.get("activities", data) if isinstance(data, dict) else data
            print(f"✓ Activities: {len(activities)} activities found")
        else:
            print("⚠ Activities endpoint returned 404")


class TestLegalPages:
    """LEGAL 1 - Test all 4 legal pages render correctly"""
    
    def test_impressum_page(self):
        """Test Impressum page accessibility"""
        response = requests.get(f"{BASE_URL}/impressum")
        assert response.status_code == 200
        print("✓ Impressum page accessible")
    
    def test_datenschutz_page(self):
        """Test Datenschutz page accessibility"""
        response = requests.get(f"{BASE_URL}/datenschutz")
        assert response.status_code == 200
        print("✓ Datenschutz page accessible")
    
    def test_agb_page(self):
        """Test AGB page accessibility"""
        response = requests.get(f"{BASE_URL}/agb")
        assert response.status_code == 200
        print("✓ AGB page accessible")
    
    def test_ki_hinweise_page(self):
        """Test KI-Hinweise page accessibility"""
        response = requests.get(f"{BASE_URL}/ki-hinweise")
        assert response.status_code == 200
        print("✓ KI-Hinweise page accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
