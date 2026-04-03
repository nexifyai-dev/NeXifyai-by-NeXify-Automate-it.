"""
Iteration 22 Backend Tests - Full CRUD for Admin Panel
Tests: Lead Edit, Customer Edit, Quote Edit, Invoice Edit, Booking Create
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestLeadCRUD:
    """Test Lead CRUD operations - PATCH /api/admin/leads/{lead_id}"""
    
    def test_get_leads_list(self, api_client):
        """Get list of leads to find one to edit"""
        response = api_client.get(f"{BASE_URL}/api/admin/leads")
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        print(f"Found {len(data['leads'])} leads")
    
    def test_create_test_lead(self, api_client):
        """Create a test lead for editing"""
        payload = {
            "vorname": "TEST_Iter22",
            "nachname": "LeadEdit",
            "email": f"test_iter22_lead_{datetime.now().strftime('%H%M%S')}@test.de",
            "unternehmen": "Test GmbH",
            "telefon": "+49 171 1234567",
            "source": "admin",
            "nachricht": "Test lead for iteration 22"
        }
        response = api_client.post(f"{BASE_URL}/api/admin/leads", json=payload)
        assert response.status_code in [200, 201], f"Create lead failed: {response.text}"
        data = response.json()
        assert "lead_id" in data
        pytest.test_lead_id = data["lead_id"]
        print(f"Created test lead: {data['lead_id']}")
    
    def test_patch_lead_full_edit(self, api_client):
        """PATCH /api/admin/leads/{lead_id} - Full lead edit"""
        lead_id = getattr(pytest, 'test_lead_id', None)
        if not lead_id:
            # Get first lead from list
            response = api_client.get(f"{BASE_URL}/api/admin/leads?limit=1")
            leads = response.json().get("leads", [])
            if not leads:
                pytest.skip("No leads available for testing")
            lead_id = leads[0]["lead_id"]
        
        # Edit all fields
        update_payload = {
            "vorname": "TEST_Updated",
            "nachname": "LeadName",
            "email": f"test_updated_{datetime.now().strftime('%H%M%S')}@test.de",
            "unternehmen": "Updated GmbH",
            "telefon": "+49 171 9999999",
            "source": "website",
            "status": "kontaktiert",
            "notes": "Updated via iteration 22 test"
        }
        response = api_client.patch(f"{BASE_URL}/api/admin/leads/{lead_id}", json=update_payload)
        assert response.status_code == 200, f"PATCH lead failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Successfully updated lead {lead_id}")
    
    def test_patch_lead_status_only(self, api_client):
        """PATCH lead with status change only"""
        response = api_client.get(f"{BASE_URL}/api/admin/leads?limit=1")
        leads = response.json().get("leads", [])
        if not leads:
            pytest.skip("No leads available")
        lead_id = leads[0]["lead_id"]
        
        response = api_client.patch(f"{BASE_URL}/api/admin/leads/{lead_id}", json={"status": "qualifiziert"})
        assert response.status_code == 200
        assert response.json().get("success") == True
        print(f"Updated lead status to 'qualifiziert'")


class TestCustomerCRUD:
    """Test Customer CRUD operations - PATCH /api/admin/customers/{email}"""
    
    def test_get_customers_list(self, api_client):
        """Get list of customers"""
        response = api_client.get(f"{BASE_URL}/api/admin/customers")
        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        print(f"Found {len(data['customers'])} customers")
    
    def test_patch_customer_edit(self, api_client):
        """PATCH /api/admin/customers/{email} - Edit customer data"""
        # Use known test customer
        test_email = "max@testfirma.de"
        
        update_payload = {
            "vorname": "Max_Updated",
            "nachname": "Mustermann_Iter22",
            "unternehmen": "Testfirma GmbH Updated",
            "telefon": "+49 171 8888888",
            "branche": "IT & Software"
        }
        response = api_client.patch(
            f"{BASE_URL}/api/admin/customers/{test_email}",
            json=update_payload
        )
        assert response.status_code == 200, f"PATCH customer failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Successfully updated customer {test_email}")
    
    def test_patch_customer_partial(self, api_client):
        """PATCH customer with partial data"""
        test_email = "max@testfirma.de"
        
        response = api_client.patch(
            f"{BASE_URL}/api/admin/customers/{test_email}",
            json={"branche": "Technologie"}
        )
        assert response.status_code == 200
        assert response.json().get("success") == True
        print("Partial customer update successful")
    
    def test_patch_customer_not_found(self, api_client):
        """PATCH non-existent customer returns 404"""
        response = api_client.patch(
            f"{BASE_URL}/api/admin/customers/nonexistent@test.de",
            json={"vorname": "Test"}
        )
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent customer")


class TestQuoteCRUD:
    """Test Quote CRUD operations - PATCH /api/admin/quotes/{quote_id}"""
    
    def test_get_quotes_list(self, api_client):
        """Get list of quotes"""
        response = api_client.get(f"{BASE_URL}/api/admin/quotes")
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        print(f"Found {len(data['quotes'])} quotes")
        if data['quotes']:
            pytest.test_quote_id = data['quotes'][0]['quote_id']
    
    def test_patch_quote_status(self, api_client):
        """PATCH /api/admin/quotes/{quote_id} - Change status"""
        quote_id = getattr(pytest, 'test_quote_id', 'q_47e524121e72a4cd')
        
        response = api_client.patch(
            f"{BASE_URL}/api/admin/quotes/{quote_id}",
            json={"status": "sent", "notes": "Updated via iteration 22 test"}
        )
        # May return 404 if quote doesn't exist
        if response.status_code == 404:
            pytest.skip(f"Quote {quote_id} not found")
        assert response.status_code == 200, f"PATCH quote failed: {response.text}"
        assert response.json().get("success") == True
        print(f"Successfully updated quote status")
    
    def test_patch_quote_discount(self, api_client):
        """PATCH quote with discount and special items"""
        quote_id = getattr(pytest, 'test_quote_id', 'q_47e524121e72a4cd')
        
        update_payload = {
            "discount_percent": 10,
            "discount_reason": "Iteration 22 Test Discount",
            "special_items": [
                {"description": "Test Zusatzleistung", "amount_eur": 100, "type": "add"}
            ]
        }
        response = api_client.patch(f"{BASE_URL}/api/admin/quotes/{quote_id}", json=update_payload)
        if response.status_code == 404:
            pytest.skip(f"Quote {quote_id} not found")
        assert response.status_code == 200, f"PATCH quote discount failed: {response.text}"
        assert response.json().get("success") == True
        print("Successfully updated quote with discount and special items")
    
    def test_patch_quote_customer_fields(self, api_client):
        """PATCH quote customer fields"""
        quote_id = getattr(pytest, 'test_quote_id', 'q_47e524121e72a4cd')
        
        update_payload = {
            "customer_name": "Test Kunde Iter22",
            "customer_email": "test_iter22@example.de",
            "customer_company": "Test Company GmbH",
            "use_case": "AI Automation Testing"
        }
        response = api_client.patch(f"{BASE_URL}/api/admin/quotes/{quote_id}", json=update_payload)
        if response.status_code == 404:
            pytest.skip(f"Quote {quote_id} not found")
        assert response.status_code == 200
        assert response.json().get("success") == True
        print("Successfully updated quote customer fields")


class TestInvoiceCRUD:
    """Test Invoice CRUD operations - PATCH /api/admin/invoices/{invoice_id}"""
    
    def test_get_invoices_list(self, api_client):
        """Get list of invoices"""
        response = api_client.get(f"{BASE_URL}/api/admin/invoices")
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        print(f"Found {len(data['invoices'])} invoices")
        if data['invoices']:
            pytest.test_invoice_id = data['invoices'][0]['invoice_id']
    
    def test_patch_invoice_status(self, api_client):
        """PATCH /api/admin/invoices/{invoice_id} - Change status"""
        invoice_id = getattr(pytest, 'test_invoice_id', None)
        if not invoice_id:
            pytest.skip("No invoices available for testing")
        
        response = api_client.patch(
            f"{BASE_URL}/api/admin/invoices/{invoice_id}",
            json={"status": "sent", "notes": "Updated via iteration 22 test"}
        )
        if response.status_code == 404:
            pytest.skip(f"Invoice {invoice_id} not found")
        assert response.status_code == 200, f"PATCH invoice failed: {response.text}"
        assert response.json().get("success") == True
        print(f"Successfully updated invoice status")
    
    def test_patch_invoice_payment_status(self, api_client):
        """PATCH invoice payment status"""
        invoice_id = getattr(pytest, 'test_invoice_id', None)
        if not invoice_id:
            pytest.skip("No invoices available")
        
        response = api_client.patch(
            f"{BASE_URL}/api/admin/invoices/{invoice_id}",
            json={"payment_status": "pending"}
        )
        if response.status_code == 404:
            pytest.skip(f"Invoice {invoice_id} not found")
        assert response.status_code == 200
        assert response.json().get("success") == True
        print("Successfully updated invoice payment status")
    
    def test_patch_invoice_not_found(self, api_client):
        """PATCH non-existent invoice returns 404"""
        response = api_client.patch(
            f"{BASE_URL}/api/admin/invoices/inv_nonexistent",
            json={"status": "sent"}
        )
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent invoice")


class TestBookingCreate:
    """Test Booking creation - POST /api/admin/bookings"""
    
    def test_create_booking_manual(self, api_client):
        """POST /api/admin/bookings - Create booking manually"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        payload = {
            "vorname": "TEST_Iter22",
            "nachname": "Booking",
            "email": f"test_booking_iter22_{datetime.now().strftime('%H%M%S')}@test.de",
            "telefon": "+49 171 5555555",
            "unternehmen": "Test Booking GmbH",
            "thema": "Iteration 22 Test Termin",
            "date": future_date,
            "time": "10:00"
        }
        response = api_client.post(f"{BASE_URL}/api/admin/bookings", json=payload)
        assert response.status_code == 200, f"Create booking failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "booking_id" in data
        pytest.test_booking_id = data["booking_id"]
        print(f"Successfully created booking: {data['booking_id']}")
    
    def test_create_booking_minimal(self, api_client):
        """Create booking with minimal required fields"""
        future_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        payload = {
            "vorname": "Minimal",
            "email": "minimal_test@test.de",
            "date": future_date,
            "time": "14:00"
        }
        response = api_client.post(f"{BASE_URL}/api/admin/bookings", json=payload)
        assert response.status_code == 200
        assert response.json().get("success") == True
        print("Successfully created minimal booking")
    
    def test_create_booking_missing_required(self, api_client):
        """Create booking without required fields returns 400"""
        payload = {
            "vorname": "Test",
            # Missing email, date, time
        }
        response = api_client.post(f"{BASE_URL}/api/admin/bookings", json=payload)
        assert response.status_code == 400
        print("Correctly returned 400 for missing required fields")
    
    def test_verify_booking_created(self, api_client):
        """Verify created booking exists in list"""
        booking_id = getattr(pytest, 'test_booking_id', None)
        if not booking_id:
            pytest.skip("No test booking created")
        
        response = api_client.get(f"{BASE_URL}/api/admin/bookings/{booking_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("booking_id") == booking_id
        assert data.get("source") == "admin_manual"
        print(f"Verified booking {booking_id} exists with source=admin_manual")


class TestExistingBookingOperations:
    """Test operations on existing bookings"""
    
    def test_get_bookings_list(self, api_client):
        """Get list of bookings"""
        response = api_client.get(f"{BASE_URL}/api/admin/bookings")
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        print(f"Found {len(data['bookings'])} bookings")
    
    def test_patch_booking(self, api_client):
        """PATCH existing booking"""
        booking_id = getattr(pytest, 'test_booking_id', None)
        if not booking_id:
            # Get first booking
            response = api_client.get(f"{BASE_URL}/api/admin/bookings?limit=1")
            bookings = response.json().get("bookings", [])
            if not bookings:
                pytest.skip("No bookings available")
            booking_id = bookings[0]["booking_id"]
        
        response = api_client.patch(
            f"{BASE_URL}/api/admin/bookings/{booking_id}",
            json={"status": "confirmed", "notes": "Updated via iteration 22"}
        )
        assert response.status_code == 200
        assert response.json().get("success") == True
        print(f"Successfully updated booking {booking_id}")


class TestCalendarData:
    """Test calendar data endpoint"""
    
    def test_get_calendar_data(self, api_client):
        """GET /api/admin/calendar-data"""
        current_month = datetime.now().strftime("%Y-%m")
        response = api_client.get(f"{BASE_URL}/api/admin/calendar-data?month={current_month}")
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "blocked_slots" in data
        print(f"Calendar data: {len(data['bookings'])} bookings, {len(data['blocked_slots'])} blocked slots")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
