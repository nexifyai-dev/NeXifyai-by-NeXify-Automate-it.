"""
NeXifyAI Iteration 17 Backend Tests
Focus: PDF tariff sheets for all categories, product descriptions API, responsive layout verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-architecture-lab.preview.emergentagent.com')

class TestPDFTariffSheets:
    """Test PDF tariff sheet generation for all categories"""
    
    def test_tariff_sheet_all_categories(self):
        """GET /api/product/tariff-sheet?category=all returns valid PDF > 10KB"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 10000, f"PDF too small: {len(response.content)} bytes, expected > 10KB"
        print(f"✓ All categories PDF: {len(response.content)} bytes")
    
    def test_tariff_sheet_seo(self):
        """GET /api/product/tariff-sheet?category=seo returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=seo")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        print(f"✓ SEO PDF: {len(response.content)} bytes")
    
    def test_tariff_sheet_apps(self):
        """GET /api/product/tariff-sheet?category=apps returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=apps")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        print(f"✓ Apps PDF: {len(response.content)} bytes")
    
    def test_tariff_sheet_addons(self):
        """GET /api/product/tariff-sheet?category=addons returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=addons")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        print(f"✓ Addons PDF: {len(response.content)} bytes")
    
    def test_tariff_sheet_bundles(self):
        """GET /api/product/tariff-sheet?category=bundles returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=bundles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        print(f"✓ Bundles PDF: {len(response.content)} bytes")
    
    def test_tariff_sheet_agents(self):
        """GET /api/product/tariff-sheet?category=agents returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=agents")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        print(f"✓ Agents PDF: {len(response.content)} bytes")
    
    def test_tariff_sheet_websites(self):
        """GET /api/product/tariff-sheet?category=websites returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/product/tariff-sheet?category=websites")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Expected PDF content-type"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
        print(f"✓ Websites PDF: {len(response.content)} bytes")


class TestProductDescriptions:
    """Test product descriptions API"""
    
    def test_product_descriptions_structure(self):
        """GET /api/product/descriptions returns JSON with products, services, bundles"""
        response = requests.get(f"{BASE_URL}/api/product/descriptions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check products (6+ expected: starter, growth, web_starter, web_professional, seo_starter, seo_growth)
        products = data.get('products', {})
        assert len(products) >= 6, f"Expected 6+ products, got {len(products)}"
        print(f"✓ Products count: {len(products)}")
        
        # Check services (10+ expected from SERVICE_CATALOG)
        services = data.get('services', {})
        assert len(services) >= 10, f"Expected 10+ services, got {len(services)}"
        print(f"✓ Services count: {len(services)}")
        
        # Check bundles (3 expected: digital_starter, growth_digital, enterprise_digital)
        bundles = data.get('bundles', {})
        assert len(bundles) >= 3, f"Expected 3 bundles, got {len(bundles)}"
        print(f"✓ Bundles count: {len(bundles)}")
    
    def test_product_descriptions_content(self):
        """Verify product descriptions have required fields"""
        response = requests.get(f"{BASE_URL}/api/product/descriptions")
        data = response.json()
        
        # Check starter product has required fields
        starter = data.get('products', {}).get('starter', {})
        assert 'what' in starter, "Starter missing 'what' field"
        assert 'for_whom' in starter, "Starter missing 'for_whom' field"
        assert 'included' in starter, "Starter missing 'included' field"
        print("✓ Starter product has required fields")
        
        # Check growth product
        growth = data.get('products', {}).get('growth', {})
        assert 'what' in growth, "Growth missing 'what' field"
        assert 'contract_terms' in growth, "Growth missing 'contract_terms' field"
        print("✓ Growth product has required fields")


class TestHealthAndBasicEndpoints:
    """Basic health and endpoint tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
        print("✓ Health endpoint OK")
    
    def test_company_endpoint(self):
        """GET /api/company returns company data"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert 'name' in data
        assert 'email' in data
        print("✓ Company endpoint OK")
    
    def test_tariffs_endpoint(self):
        """GET /api/product/tariffs returns tariff data"""
        response = requests.get(f"{BASE_URL}/api/product/tariffs")
        assert response.status_code == 200
        data = response.json()
        assert 'tariffs' in data
        assert 'starter' in data['tariffs']
        assert 'growth' in data['tariffs']
        print("✓ Tariffs endpoint OK")


class TestBundleCatalog:
    """Test bundle catalog alignment"""
    
    def test_bundle_prices(self):
        """Verify bundle prices match expected values"""
        response = requests.get(f"{BASE_URL}/api/product/descriptions")
        data = response.json()
        bundles = data.get('bundles', {})
        
        # digital_starter should be 3990
        ds = bundles.get('digital_starter', {})
        assert ds.get('bundle_price_eur') == 3990.0, f"digital_starter price mismatch: {ds.get('bundle_price_eur')}"
        print("✓ digital_starter price: 3990 EUR")
        
        # growth_digital should be 17490
        gd = bundles.get('growth_digital', {})
        assert gd.get('bundle_price_eur') == 17490.0, f"growth_digital price mismatch: {gd.get('bundle_price_eur')}"
        print("✓ growth_digital price: 17490 EUR")
        
        # enterprise_digital should be 39900
        ed = bundles.get('enterprise_digital', {})
        assert ed.get('bundle_price_eur') == 39900.0, f"enterprise_digital price mismatch: {ed.get('bundle_price_eur')}"
        print("✓ enterprise_digital price: 39900 EUR")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
