"""Worker Service Unit Tests"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app, tasks_db


@pytest.fixture(autouse=True)
def clear_db():
    """Clear in-memory database before each test"""
    tasks_db.clear()
    yield
    tasks_db.clear()


@pytest.fixture
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
    assert response.json()["service"] == "worker"


@pytest.mark.asyncio
async def test_get_status_empty(client):
    """Test status when no tasks exist"""
    response = await client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["pending"] == 0
    assert data["completed"] == 0


@pytest.mark.asyncio
async def test_create_task(client):
    """Test creating a new task"""
    task_data = {"name": "Test Task", "payload": {"key": "value"}}
    response = await client.post("/tasks", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Task"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_tasks(client):
    """Test getting all tasks"""
    await client.post("/tasks", json={"name": "Task 1"})
    await client.post("/tasks", json={"name": "Task 2"})
    
    response = await client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "worker_requests_total" in response.text
