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


def test_contacts_endpoint():
    """Verify /api/v1/contacts and /contacts return enrolled contacts list."""
    response = client.get("/api/v1/contacts")
    assert response.status_code == 200
    data = response.json()
    assert "total_contacts" in data
    assert data["total_contacts"] >= 5
    assert len(data["contacts"]) >= 5
    
    first_contact = data["contacts"][0]
    assert "id" in first_contact
    assert "name" in first_contact
    assert "role" in first_contact
    assert "phone_number" in first_contact


def test_api_v1_session_start_and_stop_with_context():
    """Verify POST /api/v1/session/start with caller_id and transaction_context."""
    start_resp = client.post("/api/v1/session/start", json={
        "caller_id": "contact_001",
        "caller_name": "Rajesh Sharma",
        "transaction_context": "fund_transfer",
        "scenario": "clean",
        "delay_sec": 0.1
    })
    assert start_resp.status_code == 200
    data = start_resp.json()
    assert data["status"] == "started"
    assert data["caller_id"] == "contact_001"
    assert data["transaction_context"] == "fund_transfer"
    assert "session_id" in data

    stop_resp = client.post("/api/v1/session/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "stopped"

