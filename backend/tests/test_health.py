import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify Day 1 Outcome: /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_contract_example_endpoint():
    """Verify example contract endpoint matches agreed specification."""
    response = client.get("/contract")
    assert response.status_code == 200
    data = response.json()
    assert "chunk_id" in data
    assert "timestamp" in data
    assert "chunk_score" in data
    assert "rolling_risk_score" in data
    assert "confidence" in data
    assert "flags" in data
    assert "alert_level" in data
    assert data["alert_level"] in ["low", "medium", "high"]
