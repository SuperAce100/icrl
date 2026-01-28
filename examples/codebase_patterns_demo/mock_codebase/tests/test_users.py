"""Tests for user endpoints.

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


class TestListUsers:
    """Tests for GET /api/v1/users."""
    
    async def test_list_users_success(self, client: AsyncClient):
        """Should return paginated list of users."""
        response = await client.get("/api/v1/users")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify APIResponse structure
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert isinstance(data["data"]["items"], list)
    
    async def test_list_users_pagination(self, client: AsyncClient):
        """Should respect skip and limit parameters."""
        response = await client.get("/api/v1/users?skip=0&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 1


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}."""
    
    async def test_get_user_success(self, client: AsyncClient):
        """Should return user when found."""
        response = await client.get("/api/v1/users/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert "email" in data["data"]
        assert "name" in data["data"]
    
    async def test_get_user_not_found(self, client: AsyncClient):
        """Should return 404 with proper error format."""
        response = await client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert "NOT_FOUND" in str(data)


class TestCreateUser:
    """Tests for POST /api/v1/users."""
    
    async def test_create_user_success(self, client: AsyncClient):
        """Should create user and return 201."""
        user_data = {
            "email": "newuser@acme.com",
            "name": "New User",
            "department": "Testing",
        }
        
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["email"] == user_data["email"]
        assert data["data"]["name"] == user_data["name"]
        assert "id" in data["data"]
    
    async def test_create_user_duplicate_email(self, client: AsyncClient):
        """Should return 409 for duplicate email."""
        user_data = {
            "email": "alice@acme.com",  # Already exists
            "name": "Another Alice",
        }
        
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
