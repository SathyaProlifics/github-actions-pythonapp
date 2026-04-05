import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"EC2 Server Dashboard" in response.data


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_get_tasks_empty(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.get_json()
    assert "tasks" in data


def test_add_task(client):
    response = client.post("/api/tasks", json={"task": "Test task"})
    assert response.status_code == 200
    data = response.get_json()
    assert "Test task" in data["tasks"]


def test_delete_task(client):
    client.post("/api/tasks", json={"task": "To be deleted"})
    response = client.delete("/api/tasks/0")
    assert response.status_code == 200


def test_add_empty_task(client):
    response = client.post("/api/tasks", json={"task": "   "})
    assert response.status_code == 200
