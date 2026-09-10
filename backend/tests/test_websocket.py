import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_websocket_connection():
    """Verify WebSocket endpoint /ws/session accepts connections and sends greeting."""
    with client.websocket_connect("/ws/session") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "connected"
        assert "message" in data


def test_start_and_stop_simulation_endpoint():
    """Verify /start-simulation and /stop-simulation endpoints."""
    # Start simulation with very small delay for testing
    start_resp = client.post("/start-simulation", json={
        "chunk_duration_sec": 3.0,
        "delay_sec": 0.1,
        "scenario": "clean"
    })
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["status"] == "started"
    assert "session_id" in start_data

    # Stop simulation
    stop_resp = client.post("/stop-simulation")
    assert stop_resp.status_code == 200
    stop_data = stop_resp.json()
    assert stop_data["status"] == "stopped"
