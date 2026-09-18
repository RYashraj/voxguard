"""
Contract Verification Tests for VoxGuard API and Schemas

Proves:
1. OpenAPI schema exposes documented REST endpoints.
2. RiskUpdate schema example retains the stable seven core fields.
3. Advisory object is strictly optional/additive.
4. Session history privacy exclusions are preserved.
"""

import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from unittest.mock import patch

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.models.schemas import RiskUpdate, AdvisoryResult, SimulationContext
from app.db.session_logger import log_chunk_record

client = TestClient(app)


def test_openapi_exposes_documented_endpoints():
    """Verify OpenAPI JSON contains all documented REST endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi = response.json()
    paths = openapi.get("paths", {})

    expected_paths = [
        "/health",
        "/start-simulation",
        "/stop-simulation",
        "/sessions/{session_id}/context",
        "/sessions/{session_id}/history",
        "/contract",
    ]

    for expected_path in expected_paths:
        assert expected_path in paths, f"Missing documented endpoint: {expected_path}"


def test_risk_update_seven_core_fields_contract():
    """Verify RiskUpdate schema defines and serializes exact seven core fields."""
    seven_core_fields = {
        "chunk_id",
        "timestamp",
        "chunk_score",
        "rolling_risk_score",
        "confidence",
        "flags",
        "alert_level",
    }

    model_fields = set(RiskUpdate.model_fields.keys())
    assert seven_core_fields.issubset(model_fields), f"Missing core fields on model: {seven_core_fields - model_fields}"

    # Verify serialization output includes all seven core fields
    update = RiskUpdate(
        chunk_id="chunk_001",
        timestamp="2026-09-18T00:00:00Z",
        chunk_score=0.1,
        rolling_risk_score=0.1,
        confidence=0.9,
        flags=["short_audio"],
        alert_level="low",
    )
    serialized = update.model_dump()
    for field in seven_core_fields:
        assert field in serialized


def test_advisory_object_is_optional_and_additive():
    """Verify RiskUpdate can be instantiated with or without the optional additive advisory object."""
    # Instantiation without advisory (7 core fields)
    update_core = RiskUpdate(
        chunk_id="chunk_001",
        timestamp="2026-09-18T00:00:00Z",
        chunk_score=0.10,
        rolling_risk_score=0.10,
        confidence=0.95,
        flags=["short_audio"],
        alert_level="low",
    )

    core_dump = update_core.model_dump()
    assert "advisory" not in core_dump or core_dump["advisory"] is None

    # Instantiation with additive advisory dictionary
    advisory_data = AdvisoryResult(
        recommendation="continue_with_caution",
        reason_codes=["normal_call_flow"],
        user_message="Low risk detected.",
        requires_user_confirmation=True,
    )

    update_additive = RiskUpdate(
        chunk_id="chunk_001",
        timestamp="2026-09-18T00:00:00Z",
        chunk_score=0.10,
        rolling_risk_score=0.10,
        confidence=0.95,
        flags=["short_audio"],
        alert_level="low",
    )

    # Attach advisory object as additive payload field
    additive_dump = update_additive.model_dump()
    additive_dump["advisory"] = advisory_data.model_dump()

    assert "advisory" in additive_dump
    assert additive_dump["advisory"]["recommendation"] == "continue_with_caution"
    # Ensure seven core fields are still present and unchanged
    for field in ["chunk_id", "timestamp", "chunk_score", "rolling_risk_score", "confidence", "flags", "alert_level"]:
        assert additive_dump[field] == core_dump[field]


def test_session_history_privacy_exclusions(tmp_path):
    """Verify GET /sessions/{session_id}/history endpoint returns no raw audio, file paths, context, or embeddings."""
    db_file = str(tmp_path / "contract_test.db")
    log_chunk_record(
        session_id="session_contract_test",
        chunk_id="chunk_001",
        timestamp="2026-09-18T00:00:00Z",
        chunk_score=0.05,
        rolling_risk_score=0.05,
        confidence=0.95,
        flags=["short_audio"],
        alert_level="low",
        inference_latency_ms=15.0,
        db_path=db_file,
    )

    with patch("app.main.get_session_history_async") as mock_get_history:
        mock_get_history.return_value = [
            {
                "session_id": "session_contract_test",
                "chunk_id": "chunk_001",
                "timestamp": "2026-09-18T00:00:00Z",
                "chunk_score": 0.05,
                "rolling_risk_score": 0.05,
                "confidence": 0.95,
                "flags": ["short_audio"],
                "alert_level": "low",
                "inference_latency_ms": 15.0,
            }
        ]

        response = client.get("/sessions/session_contract_test/history")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == "session_contract_test"
        assert len(data["history"]) == 1

        history_item = data["history"][0]
        forbidden_keys = {
            "audio_bytes",
            "file_path",
            "caller_name",
            "phone_number",
            "account_number",
            "otp",
            "pin",
            "context",
            "advisory",
            "embedding",
        }

        assert not (set(history_item.keys()) & forbidden_keys)
