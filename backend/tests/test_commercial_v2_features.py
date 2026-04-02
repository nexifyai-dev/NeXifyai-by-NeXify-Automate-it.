"""
NeXifyAI Commercial Engine v2.0 - NEW Features Tests (Iteration 14)
Tests for: Services, Bundles, Compliance, ISO Gap Analysis, Security Headers, Extended FAQ
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-architecture-lab.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "p.courbois@icloud.com"
ADMIN_PASSWORD = "NxAi#Secure2026!"


class TestServicesAndBundles:
    """Test GET /api/product/services — returns 7 services and 3 bundles"""
    
    def test_services_endpoint_returns_200(self):
        """GET /api/product/services — returns 200"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Services endpoint returns 200")
    
    def test_services_returns_7_services(self):
        """GET /api/product/services — returns 7 services"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200
        
        data = response.json()
        assert "services" in data, "Response should contain 'services' key"
        services = data["services"]
        
        assert len(services) == 7, f"Expected 7 services, got {len(services)}"
        
        # Verify expected service keys
        expected_keys = ["web_starter", "web_professional", "web_enterprise", "app_mvp", "app_professional", "ai_addon_chatbot", "ai_addon_automation"]
        for key in expected_keys:
            assert key in services, f"Missing service: {key}"
        
        print(f"✓ Services returns 7 services: {list(services.keys())}")
    
    def test_services_returns_3_bundles(self):
        """GET /api/product/services — returns 3 bundles"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200
        
        data = response.json()
        assert "bundles" in data, "Response should contain 'bundles' key"
        bundles = data["bundles"]
        
        assert len(bundles) == 3, f"Expected 3 bundles, got {len(bundles)}"
        
        # Verify expected bundle keys
        expected_keys = ["digital_starter", "growth_digital", "enterprise_digital"]
        for key in expected_keys:
            assert key in bundles, f"Missing bundle: {key}"
        
        print(f"✓ Services returns 3 bundles: {list(bundles.keys())}")
    
    def test_website_services_pricing(self):
        """Verify website services have correct pricing"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200
        
        services = response.json()["services"]
        
        # Website Starter: 2990 EUR
        assert services["web_starter"]["price_eur"] == 2990.0, f"web_starter price mismatch: {services['web_starter']['price_eur']}"
        assert services["web_starter"]["category"] == "website"
        
        # Website Professional: 7490 EUR
        assert services["web_professional"]["price_eur"] == 7490.0, f"web_professional price mismatch"
        
        # Website Enterprise: 14900 EUR
        assert services["web_enterprise"]["price_eur"] == 14900.0, f"web_enterprise price mismatch"
        
        print("✓ Website services pricing correct: 2990, 7490, 14900 EUR")
    
    def test_app_services_pricing(self):
        """Verify app services have correct pricing"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200
        
        services = response.json()["services"]
        
        # App MVP: 9900 EUR
        assert services["app_mvp"]["price_eur"] == 9900.0, f"app_mvp price mismatch"
        assert services["app_mvp"]["category"] == "app"
        
        # App Professional: 24900 EUR
        assert services["app_professional"]["price_eur"] == 24900.0, f"app_professional price mismatch"
        
        print("✓ App services pricing correct: 9900, 24900 EUR")
    
    def test_ai_addon_pricing(self):
        """Verify AI add-on services have correct monthly pricing"""
        response = requests.get(f"{BASE_URL}/api/product/services")
        assert response.status_code == 200
        
        services = response.json()["services"]
        
        # KI-Chatbot: 249 EUR/Mo
        assert services["ai_addon_chatbot"]["price_monthly_eur"] == 249.0, f"ai_addon_chatbot price mismatch"
        assert services["ai_addon_chatbot"]["category"] == "ai_addon"
        assert services["ai_addon_chatbot"]["billing_mode"] == "monthly"
        
        # KI-Automation: 499 EUR/Mo
        assert services["ai_addon_automation"]["price_monthly_eur"] == 499.0, f"ai_addon_automation price mismatch"
        
        print("✓ AI add-on pricing correct: 249, 499 EUR/Mo")


class TestComplianceEndpoint:
    """Test GET /api/product/compliance — returns compliance status and ISO gap analysis"""
    
    def test_compliance_endpoint_returns_200(self):
        """GET /api/product/compliance — returns 200"""
        response = requests.get(f"{BASE_URL}/api/product/compliance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Compliance endpoint returns 200")
    
    def test_compliance_returns_status(self):
        """GET /api/product/compliance — returns compliance status"""
        response = requests.get(f"{BASE_URL}/api/product/compliance")
        assert response.status_code == 200
        
        data = response.json()
        assert "compliance" in data, "Response should contain 'compliance' key"
        compliance = data["compliance"]
        
        # Verify expected compliance items
        expected_items = ["gdpr", "eu_ai_act", "uavg", "iso_27001", "iso_27701", "pci_dss", "ssl_tls", "eu_hosting"]
        for item in expected_items:
            assert item in compliance, f"Missing compliance item: {item}"
            assert "status" in compliance[item], f"Missing status for {item}"
            assert "label" in compliance[item], f"Missing label for {item}"
        
        print(f"✓ Compliance returns {len(compliance)} items: {list(compliance.keys())}")
    
    def test_compliance_returns_iso_gap_analysis(self):
        """GET /api/product/compliance — returns ISO gap analysis"""
        response = requests.get(f"{BASE_URL}/api/product/compliance")
        assert response.status_code == 200
        
        data = response.json()
        assert "iso_gap_analysis" in data, "Response should contain 'iso_gap_analysis' key"
        iso_gap = data["iso_gap_analysis"]
        
        # Verify ISO 27001 and 27701 gap analysis
        assert "iso_27001" in iso_gap, "Missing ISO 27001 gap analysis"
        assert "iso_27701" in iso_gap, "Missing ISO 27701 gap analysis"
        
        # Verify structure
        for iso_key in ["iso_27001", "iso_27701"]:
            assert "name" in iso_gap[iso_key], f"Missing name for {iso_key}"
            assert "summary" in iso_gap[iso_key], f"Missing summary for {iso_key}"
            assert "controls" in iso_gap[iso_key], f"Missing controls for {iso_key}"
            
            summary = iso_gap[iso_key]["summary"]
            assert "fulfilled" in summary, f"Missing fulfilled count for {iso_key}"
            assert "partial" in summary, f"Missing partial count for {iso_key}"
            assert "total" in summary, f"Missing total count for {iso_key}"
        
        print(f"✓ ISO gap analysis present for: {list(iso_gap.keys())}")
    
    def test_compliance_returns_company_info(self):
        """GET /api/product/compliance — returns company info"""
        response = requests.get(f"{BASE_URL}/api/product/compliance")
        assert response.status_code == 200
        
        data = response.json()
        assert "company" in data, "Response should contain 'company' key"
        company = data["company"]
        
        assert "name" in company, "Missing company name"
        assert "kvk" in company, "Missing KvK number"
        assert "vat_id" in company, "Missing VAT ID"
        assert "hosting" in company, "Missing hosting info"
        
        print(f"✓ Company info present: {company.get('name')}, hosting: {company.get('hosting')}")


class TestExtendedFAQ:
    """Test GET /api/product/faq — returns 17+ FAQ entries"""
    
    def test_faq_returns_17_plus_entries(self):
        """GET /api/product/faq — returns 17+ FAQ entries"""
        response = requests.get(f"{BASE_URL}/api/product/faq")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "faq" in data, "Response should contain 'faq' key"
        faq = data["faq"]
        
        assert len(faq) >= 17, f"Expected 17+ FAQ entries, got {len(faq)}"
        print(f"✓ FAQ returns {len(faq)} entries (17+ expected)")
    
    def test_faq_contains_services_info(self):
        """Verify FAQ contains questions about services (websites, apps, bundles)"""
        response = requests.get(f"{BASE_URL}/api/product/faq")
        assert response.status_code == 200
        
        faq = response.json()["faq"]
        all_text = " ".join([item["q"] + " " + item["a"] for item in faq])
        
        # Check for services-related content
        assert "Website" in all_text or "website" in all_text, "FAQ should mention websites"
        assert "App" in all_text or "app" in all_text, "FAQ should mention apps"
        assert "Bundle" in all_text or "bundle" in all_text, "FAQ should mention bundles"
        
        print("✓ FAQ contains services info (websites, apps, bundles)")


class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_x_content_type_options_header(self):
        """Response headers include X-Content-Type-Options"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        assert "X-Content-Type-Options" in response.headers, "Missing X-Content-Type-Options header"
        assert response.headers["X-Content-Type-Options"] == "nosniff", f"Expected 'nosniff', got {response.headers['X-Content-Type-Options']}"
        
        print("✓ X-Content-Type-Options: nosniff")
    
    def test_x_frame_options_header(self):
        """Response headers include X-Frame-Options"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        assert "X-Frame-Options" in response.headers, "Missing X-Frame-Options header"
        assert response.headers["X-Frame-Options"] == "DENY", f"Expected 'DENY', got {response.headers['X-Frame-Options']}"
        
        print("✓ X-Frame-Options: DENY")
    
    def test_referrer_policy_header(self):
        """Response headers include Referrer-Policy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        assert "Referrer-Policy" in response.headers, "Missing Referrer-Policy header"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin", f"Expected 'strict-origin-when-cross-origin', got {response.headers['Referrer-Policy']}"
        
        print("✓ Referrer-Policy: strict-origin-when-cross-origin")
    
    def test_x_xss_protection_header(self):
        """Response headers include X-XSS-Protection"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        assert "X-XSS-Protection" in response.headers, "Missing X-XSS-Protection header"
        assert response.headers["X-XSS-Protection"] == "1; mode=block", f"Expected '1; mode=block', got {response.headers['X-XSS-Protection']}"
        
        print("✓ X-XSS-Protection: 1; mode=block")
    
    def test_permissions_policy_header(self):
        """Response headers include Permissions-Policy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        assert "Permissions-Policy" in response.headers, "Missing Permissions-Policy header"
        
        print(f"✓ Permissions-Policy: {response.headers['Permissions-Policy']}")
    
    def test_cache_control_header(self):
        """Response headers include Cache-Control"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        assert "Cache-Control" in response.headers, "Missing Cache-Control header"
        
        print(f"✓ Cache-Control: {response.headers['Cache-Control']}")


@pytest.fixture
def auth_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


class TestQuoteCreationWithTiers:
    """Test quote creation for both tiers (verify still works)"""
    
    def test_create_quote_starter_tier(self, auth_token):
        """POST /api/admin/quotes — create quote for starter tier"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        payload = {
            "tier": "starter",
            "customer_name": "TEST_Iter14_Starter",
            "customer_email": "test_iter14_starter@example.com",
            "customer_company": "Iteration 14 Test GmbH"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        assert response.status_code == 200, f"Create quote failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "quote" in data, "Response should contain 'quote'"
        quote = data["quote"]
        
        assert quote.get("tier") == "starter"
        assert quote.get("status") == "draft"
        
        print(f"✓ Starter quote created: {quote.get('quote_number')}")
    
    def test_create_quote_growth_tier(self, auth_token):
        """POST /api/admin/quotes — create quote for growth tier"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        payload = {
            "tier": "growth",
            "customer_name": "TEST_Iter14_Growth",
            "customer_email": "test_iter14_growth@example.com",
            "customer_company": "Iteration 14 Growth Test AG"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/quotes", json=payload, headers=headers)
        assert response.status_code == 200, f"Create quote failed: {response.status_code} - {response.text}"
        
        data = response.json()
        quote = data["quote"]
        
        assert quote.get("tier") == "growth"
        
        print(f"✓ Growth quote created: {quote.get('quote_number')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
