"""
Day 6 Sprint Integration Tests for VoxGuard.
Validates:
1. Multi-client WebSocket broadcasting (multiple concurrent viewers)
2. Integration stability across 3 distinct call scenarios (clean, suspicious, gradual_escalation)
3. Zero-restart consecutive simulation runs
4. SQLite session persistence and history retrieval
"""
import os
import asyncio
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session_logger import init_db, get_session_history, get_session_stats
from app.services.websocket_manager import ws_manager
from app.services.simulator import simulate_call
from app.utils.audio_generator import generate_sample_wav

client = TestClient(app)


class TestSprintIntegration:

    def test_multi_client_websocket_broadcast(self):
        """
        Verify multiple WebSocket clients (e.g. Judge Screen + Analyst Dashboard)
        connected simultaneously receive the exact same streamed updates.
        """
        with client.websocket_connect("/ws/session") as ws1:
            with client.websocket_connect("/ws/session") as ws2:
                # Both receive handshake
                greeting1 = ws1.receive_json()
                greeting2 = ws2.receive_json()
                assert greeting1["event"] == "connected"
                assert greeting2["event"] == "connected"

                # Broadcast a test risk update
                test_payload = {
                    "chunk_id": "chunk_sprint_001",
                    "timestamp": "2026-09-12T20:00:00Z",
                    "chunk_score": 0.85,
                    "rolling_risk_score": 0.72,
                    "confidence": 0.96,
                    "flags": ["synthetic_artifact"],
                    "alert_level": "high"
                }

                asyncio.run(ws_manager.broadcast(test_payload))

                # Both clients receive the exact payload
                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()

                assert msg1 == test_payload
                assert msg2 == test_payload

    def test_stability_across_three_sample_scenarios(self):
        """
        Verifies end-to-end simulation stability across 3 distinct call scenarios:
        1. 'clean' -> All chunks stay LOW alert
        2. 'suspicious' -> Rapidly flags HIGH risk with synthetic flags
        3. 'gradual_escalation' -> Smooth escalation from LOW to HIGH alert
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            test_wav = os.path.join(tmp_dir, "test_call.wav")
            generate_sample_wav(test_wav, duration_sec=6.0, frequency=400.0)

            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("VOXGUARD_ML_MODE", "stub")

                # 1. Clean Scenario
                clean_updates = []
                async def run_clean():
                    async for u in simulate_call(test_wav, chunk_duration_sec=3.0, delay_sec=0.001, scenario="clean"):
                        clean_updates.append(u)
                asyncio.run(run_clean())

                assert len(clean_updates) == 2
                for u in clean_updates:
                    assert u.chunk_score < 0.40
                    assert u.alert_level == "low"

                # 2. Suspicious Scenario
                suspicious_updates = []
                async def run_suspicious():
                    async for u in simulate_call(test_wav, chunk_duration_sec=3.0, delay_sec=0.001, scenario="suspicious"):
                        suspicious_updates.append(u)
                asyncio.run(run_suspicious())

                assert len(suspicious_updates) == 2
                assert suspicious_updates[-1].chunk_score > 0.70
                assert suspicious_updates[-1].alert_level in ["medium", "high"]
                assert "synthetic_artifact" in suspicious_updates[-1].flags

                # 3. Gradual Escalation Scenario
                escalation_updates = []
                async def run_escalation():
                    async for u in simulate_call(test_wav, chunk_duration_sec=3.0, delay_sec=0.001, scenario="gradual_escalation"):
                        escalation_updates.append(u)
                asyncio.run(run_escalation())

                assert len(escalation_updates) == 2
                assert escalation_updates[1].rolling_risk_score >= escalation_updates[0].rolling_risk_score

    def test_zero_restart_consecutive_simulations(self):
        """
        Verifies that multiple consecutive simulation sessions can be started and stopped
        back-to-back without restarting the server or leaking tasks.
        """
        for i in range(3):
            # Start
            start_resp = client.post("/start-simulation", json={
                "chunk_duration_sec": 3.0,
                "delay_sec": 0.05,
                "scenario": "clean"
            })
            assert start_resp.status_code == 200
            session_id = start_resp.json()["session_id"]
            assert session_id.startswith("session_")

            # Stop
            stop_resp = client.post("/stop-simulation")
            assert stop_resp.status_code == 200
            assert stop_resp.json()["status"] == "stopped"

    def test_sqlite_session_audit_history_and_listing(self):
        """
        Verifies that sessions are correctly persisted and queryable via both
        GET /sessions and GET /sessions/{session_id}/history.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            test_db = os.path.join(tmp_dir, "sprint_test.db")
            test_wav = os.path.join(tmp_dir, "test_call.wav")
            generate_sample_wav(test_wav, duration_sec=6.0, frequency=400.0)

            with pytest.MonkeyPatch.context() as mp:
                mp.setenv("VOXGUARD_DB_PATH", test_db)
                mp.setenv("VOXGUARD_ML_MODE", "stub")

                init_db(test_db)
                sid = "session_sprint_test_99"

                async def run_stream():
                    async for _ in simulate_call(
                        test_wav, chunk_duration_sec=3.0, delay_sec=0.001,
                        scenario="gradual_escalation", session_id=sid
                    ):
                        pass
                asyncio.run(run_stream())

                # Check REST endpoint
                resp = client.get(f"/sessions/{sid}/history")
                assert resp.status_code == 200
                data = resp.json()
                assert data["session_id"] == sid
                assert data["total_chunks"] == 2
                assert "stats" in data
                assert data["stats"]["avg_latency_ms"] >= 0.0

                # Check /sessions list endpoint
                list_resp = client.get("/sessions")
                assert list_resp.status_code == 200
                sessions = list_resp.json()["sessions"]
                session_ids = [s["session_id"] for s in sessions]
                assert sid in session_ids
