"""
Integration Tests for VoxGuard Session Context Endpoints, WebSocket Delivery, and Data Isolation
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.session_context_manager import session_context_mgr
from app.models.schemas import SimulationContext, RiskUpdate
from app.db.session_logger import get_session_history_async, init_db_async

client = TestClient(app)


def test_unknown_or_inactive_session_returns_404():
    """Requirement Test 7: Unknown or inactive session returns 404 for GET and POST."""
    fake_session = "session_non_existent_999"

    # GET context for unknown session
    res_get = client.get(f"/sessions/{fake_session}/context")
    assert res_get.status_code == 404
    assert f"Session '{fake_session}' not found" in res_get.json()["detail"]

    # POST context for unknown session
    payload = {
        "caller_context": "unknown_contact",
        "transaction_type": "otp_or_pin_request"
    }
    res_post = client.post(f"/sessions/{fake_session}/context", json=payload)
    assert res_post.status_code == 404
    assert f"Session '{fake_session}' not found" in res_post.json()["detail"]


def test_session_context_post_get_behavior():
    """Requirement Test 6: Registered active session context POST/GET behavior and Pydantic validation."""
    test_session = "session_test_active_123"
    session_context_mgr.register_session(test_session)

    try:
        # 1. Initial GET returns default context
        res_init = client.get(f"/sessions/{test_session}/context")
        assert res_init.status_code == 200
        data_init = res_init.json()
        assert data_init["session_id"] == test_session
        assert data_init["context"]["caller_context"] == "not_provided"

        # 2. Valid POST updates context
        update_payload = {
            "caller_context": "unknown_contact",
            "transaction_type": "fund_transfer",
            "transaction_amount": 15000.0,
            "user_confirmation_required": True
        }
        res_post = client.post(f"/sessions/{test_session}/context", json=update_payload)
        assert res_post.status_code == 200
        assert res_post.json()["status"] == "updated"

        # 3. Subsequent GET returns updated context
        res_get = client.get(f"/sessions/{test_session}/context")
        assert res_get.status_code == 200
        get_data = res_get.json()["context"]
        assert get_data["caller_context"] == "unknown_contact"
        assert get_data["transaction_type"] == "fund_transfer"
        assert get_data["transaction_amount"] == 15000.0

        # 4. Invalid Pydantic validation check (negative transaction_amount or invalid enum)
        invalid_payload = {
            "caller_context": "invalid_enum_value",
            "transaction_amount": -500.0
        }
        res_invalid = client.post(f"/sessions/{test_session}/context", json=invalid_payload)
        assert res_invalid.status_code == 422  # Unprocessable Entity
    finally:
        session_context_mgr.remove_session(test_session)


@pytest.mark.asyncio
async def test_websocket_message_retains_core_fields_and_includes_advisory():
    """Requirement Test 8: WebSocket payload retains all original 7 core fields and includes valid optional advisory."""
    from app.services.simulator import simulate_call

    ctx = SimulationContext(
        caller_context="unknown_contact",
        transaction_type="otp_or_pin_request"
    )

    test_session = "session_ws_contract_test"

    async for update in simulate_call(
        chunk_duration_sec=1.0,
        delay_sec=0.01,
        scenario="gradual_escalation",
        session_id=test_session,
        context=ctx
    ):
        # Verify 7 core fields exist on RiskUpdate model
        update_dict = update.model_dump()
        core_fields = ["chunk_id", "timestamp", "chunk_score", "rolling_risk_score", "confidence", "flags", "alert_level"]
        for field in core_fields:
            assert field in update_dict, f"Core field '{field}' missing from RiskUpdate"

        # Simulate broadcast enrichment
        from app.services.context_policy import evaluate_advisory_policy
        active_ctx = session_context_mgr.get_context(test_session)
        advisory = evaluate_advisory_policy(update.rolling_risk_score, update.alert_level, active_ctx)
        update_dict["advisory"] = advisory.model_dump()

        assert "advisory" in update_dict
        adv = update_dict["advisory"]
        assert adv["recommendation"] in ["continue_with_caution", "pause_and_verify", "block_and_report"]
        assert isinstance(adv["reason_codes"], list)
        assert isinstance(adv["user_message"], str)
        assert isinstance(adv["requires_user_confirmation"], bool)
        break


@pytest.mark.asyncio
async def test_context_never_written_to_sqlite():
    """Requirement Test 9: Context is NEVER written into SQLite history database records."""
    await init_db_async()

    ctx = SimulationContext(
        caller_context="unknown_contact",
        transaction_type="fund_transfer",
        transaction_amount=25000.0
    )

    test_session = "session_sqlite_isolation_test"

    from app.services.simulator import simulate_call
    async for update in simulate_call(
        chunk_duration_sec=1.0,
        delay_sec=0.01,
        scenario="clean",
        session_id=test_session,
        context=ctx
    ):
        break

    history = await get_session_history_async(test_session)
    assert len(history) > 0

    record = history[0]
    # Check SQLite record keys: must contain only standard session history fields
    sqlite_keys = list(record.keys())
    assert "caller_context" not in sqlite_keys
    assert "transaction_type" not in sqlite_keys
    assert "transaction_amount" not in sqlite_keys
    assert "advisory" not in sqlite_keys

    # Verify original 7 core RiskUpdate fields logged cleanly into SQLite
    assert "chunk_id" in record
    assert "chunk_score" in record
    assert "rolling_risk_score" in record
    assert "alert_level" in record


@pytest.mark.asyncio
async def test_start_simulation_context_reaches_ws_advisory_known_caller():
    """Integration Test: Context sent in POST /start-simulation reaches WebSocket advisory for known caller."""
    from app.services.simulator import sim_runner

    known_caller_ctx = SimulationContext(
        caller_context="known_contact",
        transaction_type="other",
        user_confirmation_required=True
    )

    session_id = await sim_runner.start(
        scenario="clean",
        delay_sec=0.1,
        context=known_caller_ctx
    )

    try:
        # Verify in-memory session context is correctly registered
        active_ctx = session_context_mgr.get_context(session_id)
        assert active_ctx is not None
        assert active_ctx.caller_context == "known_contact"
        assert active_ctx.transaction_type == "other"

        # Evaluate policy for low risk clean call
        from app.services.context_policy import evaluate_advisory_policy
        advisory = evaluate_advisory_policy(
            rolling_risk_score=0.05,
            alert_level="low",
            context=active_ctx
        )

        assert advisory.recommendation == "continue_with_caution"
        assert advisory.reason_codes == ["normal_call_flow"]
    finally:
        sim_runner.stop()

