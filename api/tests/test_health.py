from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_env():
    response = client.get("/health")
    data = response.json()
    assert "env" in data
    assert "version" in data


def test_health_method_not_allowed():
    response = client.post("/health")
    assert response.status_code == 405