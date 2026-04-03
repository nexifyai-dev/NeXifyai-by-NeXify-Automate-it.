"""
NeXifyAI Backend API Tests - Iteration 17
Testing: Health, Product APIs, Booking, Legal pages, PDF tariff sheets
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-architecture-lab.preview.emergentagent.com')

class TestHealthAndBasics:
    """Health check and basic API tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        print(f"✓ Health check passed: {data['status']}, version {data['version']}")

    def test_company_endpoint(self):
        """Test /api/company returns company data"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "kvk" in data
        assert data["kvk"] == "90483944"
        assert data["vat_id"] == "NL865786276B01"
        print(f"✓ Company data: KvK={data['kvk']}, VAT={data['vat_id']}")


class TestProductAPIs:
    """Product information API tests"""
    
    def test_tariffs_endpoint(self):
        """Test /api/product/tariffs returns tariff data"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        assert response.status_code == 200
        data = response.json()
        assert "tariffs" in data
        tariffs = data["tariffs"]
        # Check starter tariff
        assert "starter" in tariffs
        starter = tariffs["starter"]
        assert starter["reference_monthly_eur"] == 499
        assert starter["calculation"]["total_contract_eur"] == 11976
        # Check growth tariff
        assert "growth" in tariffs
        growth = tariffs["growth"]
        assert growth["reference_monthly_eur"] == 1299
        print(f"✓ Tariffs: Starter={starter['reference_monthly_eur']} EUR, Growth={growth['reference_monthly_eur']} EUR")

    def test_product_descriptions(self):
        """Test /api/product/descriptions returns 12 products"""
        response = requests.get(f"{BASE_URL}/api/product/descriptions")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        products = data["products"]
        # Products is a dict with keys like 'starter', 'growth', etc.
        assert isinstance(products, dict)
        assert len(products) >= 12, f"Expected at least 12 products, got {len(products)}"
        # Check for key products
        assert "starter" in products
        assert "growth" in products
        assert "web_starter" in products
        assert "seo_starter" in products
        print(f"✓ Product descriptions: {len(products)} products returned")

    def test_product_faq(self):
        """Test /api/product/faq returns 18 FAQ items"""
        response = requests.get(f"{BASE_URL}/api/product/faq")
        assert response.status_code == 200
        data = response.json()
        assert "faq" in data
        faq = data["faq"]
        assert len(faq) >= 18, f"Expected at least 18 FAQ items, got {len(faq)}"
        # Check FAQ structure - uses 'q' and 'a' keys
        for item in faq[:3]:
            assert "q" in item, "FAQ item missing 'q' key"
            assert "a" in item, "FAQ item missing 'a' key"
        print(f"✓ FAQ: {len(faq)} items returned")


class TestPDFTariffSheet:
    """PDF tariff sheet download tests"""
    
    def test_tariff_sheet_all(self):
        """Test /api/product/tariff-sheet?category=all returns PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=all")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 1000  # PDF should have content
        print(f"✓ PDF tariff sheet (all): {len(response.content)} bytes")

    def test_tariff_sheet_seo(self):
        """Test /api/product/tariff-sheet?category=seo returns PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=seo")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ PDF tariff sheet (seo): {len(response.content)} bytes")

    def test_tariff_sheet_agents(self):
        """Test /api/product/tariff-sheet?category=agents returns PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=agents")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        print(f"✓ PDF tariff sheet (agents): {len(response.content)} bytes")


class TestBookingSlots:
    """Booking slot availability tests"""
    
    def test_booking_slots_future_date(self):
        """Test /api/booking/slots returns slots for future date"""
        response = requests.get(f"{BASE_URL}/api/booking/slots?date=2026-04-07")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "slots" in data
        assert data["date"] == "2026-04-07"
        # Should have available slots
        assert isinstance(data["slots"], list)
        print(f"✓ Booking slots for 2026-04-07: {len(data['slots'])} available")

    def test_booking_slots_another_date(self):
        """Test booking slots for another date"""
        response = requests.get(f"{BASE_URL}/api/booking/slots?date=2026-04-10")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"✓ Booking slots for 2026-04-10: {len(data['slots'])} available")


class TestFrontendPages:
    """Frontend page accessibility tests"""
    
    def test_homepage_loads(self):
        """Test homepage loads correctly"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert "NeXify" in response.text
        print("✓ Homepage loads correctly")

    def test_german_legal_impressum(self):
        """Test /de/impressum loads"""
        response = requests.get(f"{BASE_URL}/de/impressum")
        assert response.status_code == 200
        print("✓ /de/impressum loads")

    def test_german_legal_datenschutz(self):
        """Test /de/datenschutz loads"""
        response = requests.get(f"{BASE_URL}/de/datenschutz")
        assert response.status_code == 200
        print("✓ /de/datenschutz loads")

    def test_german_legal_agb(self):
        """Test /de/agb loads"""
        response = requests.get(f"{BASE_URL}/de/agb")
        assert response.status_code == 200
        print("✓ /de/agb loads")

    def test_integration_detail_salesforce(self):
        """Test /integrationen/salesforce loads"""
        response = requests.get(f"{BASE_URL}/integrationen/salesforce")
        assert response.status_code == 200
        print("✓ /integrationen/salesforce loads")


class TestUmlautCheck:
    """Check for ASCII umlaut remnants in API responses"""
    
    def test_no_ascii_umlauts_in_tariffs(self):
        """Verify no ASCII umlauts in tariff data"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        text = response.text
        ascii_umlauts = ["&auml;", "&ouml;", "&uuml;", "&Auml;", "&Ouml;", "&Uuml;", "&szlig;"]
        for umlaut in ascii_umlauts:
            assert umlaut not in text, f"Found ASCII umlaut {umlaut} in tariffs"
        print("✓ No ASCII umlauts in tariff data")

    def test_no_ascii_umlauts_in_faq(self):
        """Verify no ASCII umlauts in FAQ data"""
        response = requests.get(f"{BASE_URL}/api/product/faq")
        text = response.text
        ascii_umlauts = ["&auml;", "&ouml;", "&uuml;", "&Auml;", "&Ouml;", "&Uuml;", "&szlig;"]
        for umlaut in ascii_umlauts:
            assert umlaut not in text, f"Found ASCII umlaut {umlaut} in FAQ"
        print("✓ No ASCII umlauts in FAQ data")

    def test_no_ascii_umlauts_in_descriptions(self):
        """Verify no ASCII umlauts in product descriptions"""
        response = requests.get(f"{BASE_URL}/api/product/descriptions")
        text = response.text
        ascii_umlauts = ["&auml;", "&ouml;", "&uuml;", "&Auml;", "&Ouml;", "&Uuml;", "&szlig;"]
        for umlaut in ascii_umlauts:
            assert umlaut not in text, f"Found ASCII umlaut {umlaut} in descriptions"
        print("✓ No ASCII umlauts in product descriptions")


class TestAnalytics:
    """Analytics tracking endpoint tests"""
    
    def test_analytics_track(self):
        """Test /api/analytics/track accepts events"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/track",
            json={"event": "test_event", "properties": {"test": True}, "session_id": "test_session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✓ Analytics tracking works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
