"""API Service Unit Tests"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app, items_db


@pytest.fixture(autouse=True)
def clear_db():
    """Clear in-memory database before each test"""
    items_db.clear()
    yield
    items_db.clear()


@pytest_asyncio.fixture
async def client():
    """Async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint returns healthy status"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "api"


@pytest.mark.asyncio
async def test_get_items_empty(client):
    """Test getting items when database is empty"""
    response = await client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_item(client):
    """Test creating a new item"""
    item_data = {"name": "Test Item", "description": "A test item"}
    response = await client.post("/items", json=item_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test item"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_and_get_items(client):
    """Test creating items and retrieving them"""
    await client.post("/items", json={"name": "Item 1"})
    await client.post("/items", json={"name": "Item 2"})
    
    response = await client.get("/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "api_requests_total" in response.text
