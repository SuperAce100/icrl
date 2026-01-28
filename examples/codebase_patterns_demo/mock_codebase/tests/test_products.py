"""Tests for product endpoints.

Test patterns for ACME API:
1. Use httpx.AsyncClient for async testing
2. Test both success and error cases
3. Verify response structure matches APIResponse
4. Check that proper exceptions are raised
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestListProducts:
    """Tests for GET /api/v1/products."""
    
    async def test_list_products_success(self, client: AsyncClient):
        """Should return paginated list of products."""
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify APIResponse structure
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert isinstance(data["data"]["items"], list)
    
    async def test_list_products_pagination(self, client: AsyncClient):
        """Should respect skip and limit parameters."""
        response = await client.get("/api/v1/products?skip=0&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 1
    
    async def test_list_products_filter_by_category(self, client: AsyncClient):
        """Should filter products by category."""
        response = await client.get("/api/v1/products?category=Widgets")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned products should be in the Widgets category
        for product in data["data"]["items"]:
            assert product["category"] == "Widgets"


class TestGetProduct:
    """Tests for GET /api/v1/products/{product_id}."""
    
    async def test_get_product_success(self, client: AsyncClient):
        """Should return product when found."""
        response = await client.get("/api/v1/products/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert "name" in data["data"]
        assert "sku" in data["data"]
        assert "price" in data["data"]
    
    async def test_get_product_not_found(self, client: AsyncClient):
        """Should return 404 with proper error format."""
        response = await client.get("/api/v1/products/99999")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert "NOT_FOUND" in str(data)


class TestCreateProduct:
    """Tests for POST /api/v1/products."""
    
    async def test_create_product_success(self, client: AsyncClient):
        """Should create product and return 201."""
        product_data = {
            "name": "New Widget",
            "description": "A brand new widget",
            "sku": "WGT-NEW-001",
            "price": "39.99",
            "category": "Widgets",
            "stock_quantity": 50,
        }
        
        response = await client.post("/api/v1/products", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["name"] == product_data["name"]
        assert data["data"]["sku"] == product_data["sku"]
        assert "id" in data["data"]
    
    async def test_create_product_duplicate_sku(self, client: AsyncClient):
        """Should return 409 for duplicate SKU."""
        product_data = {
            "name": "Another Widget",
            "sku": "WGT-STD-001",  # Already exists
            "price": "29.99",
        }
        
        response = await client.post("/api/v1/products", json=product_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False


class TestUpdateStock:
    """Tests for POST /api/v1/products/{product_id}/stock."""
    
    async def test_update_stock_add(self, client: AsyncClient):
        """Should add stock successfully."""
        response = await client.post("/api/v1/products/1/stock?quantity_change=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "stock_quantity" in data["data"]
    
    async def test_update_stock_insufficient(self, client: AsyncClient):
        """Should return 400 when removing more stock than available."""
        response = await client.post("/api/v1/products/1/stock?quantity_change=-99999")
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["success"] is False
        assert "VALIDATION_ERROR" in str(data)
