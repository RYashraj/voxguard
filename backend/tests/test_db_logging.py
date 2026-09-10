import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.db.session_logger import (
    get_db_path,
    init_db,
    log_chunk_record,
    get_session_history,
)
from app.services.simulator import simulate_call
from app.utils.audio_generator import generate_sample_wav

client = TestClient(app)


class TestDBLogging(unittest.TestCase):

    def test_db_path_resolution(self):
        """Verify default VOXGUARD_DB_PATH resolves to source-file relative backend/data/voxguard.db."""
        with patch.dict(os.environ, {}, clear=True):
            if "VOXGUARD_DB_PATH" in os.environ:
                del os.environ["VOXGUARD_DB_PATH"]
            path = get_db_path()
            self.assertTrue(path.endswith("voxguard.db"))
            self.assertIn("data", path)

    def test_simulated_session_persists_records(self):
        """Verify a simulated session produces persisted records sharing one session_id and latency."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db = os.path.join(tmp_dir, "test_voxguard.db")
            wav_path = os.path.join(tmp_dir, "test_call.wav")
            generate_sample_wav(wav_path, duration_sec=6.0, frequency=300.0)

            with patch.dict(os.environ, {"VOXGUARD_DB_PATH": test_db, "VOXGUARD_ML_MODE": "stub"}):
                init_db(test_db)
                session_id = "session_test_12345"

                import asyncio
                async def _run():
                    updates = []
                    async for update in simulate_call(
                        wav_path, chunk_duration_sec=3.0, delay_sec=0.01, session_id=session_id
                    ):
                        updates.append(update)
                    return updates

                updates = asyncio.run(_run())
                self.assertEqual(len(updates), 2)

                # Fetch persisted history
                history = get_session_history(session_id, db_path=test_db)
                self.assertEqual(len(history), 2)

                # Verify all records share session_id
                for record in history:
                    self.assertEqual(record["session_id"], session_id)
                    self.assertTrue(record["chunk_id"].startswith("chunk_"))
                    self.assertGreaterEqual(record["chunk_score"], 0.0)
                    self.assertLessEqual(record["chunk_score"], 1.0)
                    self.assertGreaterEqual(record["rolling_risk_score"], 0.0)
                    self.assertLessEqual(record["rolling_risk_score"], 1.0)
                    self.assertIsInstance(record["flags"], list)
                    self.assertIn(record["alert_level"], ["low", "medium", "high"])
                    self.assertGreaterEqual(record["inference_latency_ms"], 0.0)

    def test_get_session_history_deterministic_order(self):
        """Verify get_session_history orders records deterministically by timestamp ASC, id ASC."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db = os.path.join(tmp_dir, "test_voxguard.db")
            init_db(test_db)
            sid = "session_order_test"

            log_chunk_record(sid, "chunk_001", "2026-09-10T15:00:00Z", 0.1, 0.1, 0.9, [], "low", 5.2, db_path=test_db)
            log_chunk_record(sid, "chunk_002", "2026-09-10T15:00:03Z", 0.3, 0.2, 0.9, [], "low", 4.8, db_path=test_db)
            log_chunk_record(sid, "chunk_003", "2026-09-10T15:00:06Z", 0.8, 0.5, 0.9, ["synthetic_artifact"], "medium", 6.1, db_path=test_db)

            history = get_session_history(sid, db_path=test_db)
            self.assertEqual(len(history), 3)
            self.assertEqual(history[0]["chunk_id"], "chunk_001")
            self.assertEqual(history[1]["chunk_id"], "chunk_002")
            self.assertEqual(history[2]["chunk_id"], "chunk_003")

    def test_session_history_endpoint_200_and_404(self):
        """Verify GET /sessions/{session_id}/history returns 200 for known session and 404 for unknown session."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db = os.path.join(tmp_dir, "test_voxguard.db")
            init_db(test_db)
            sid = "session_api_test"

            log_chunk_record(sid, "chunk_001", "2026-09-10T15:00:00Z", 0.12, 0.12, 0.95, ["test_flag"], "low", 3.5, db_path=test_db)

            with patch.dict(os.environ, {"VOXGUARD_DB_PATH": test_db}):
                # Test 200 OK
                resp_200 = client.get(f"/sessions/{sid}/history")
                self.assertEqual(resp_200.status_code, 200)
                data = resp_200.json()
                self.assertEqual(data["session_id"], sid)
                self.assertEqual(data["total_chunks"], 1)
                self.assertEqual(data["history"][0]["chunk_id"], "chunk_001")

                # Test 404 Not Found
                resp_404 = client.get("/sessions/unknown_nonexistent_session/history")
                self.assertEqual(resp_404.status_code, 404)
                self.assertIn("detail", resp_404.json())

    def test_db_write_failure_does_not_stop_streaming(self):
        """
        Requirement 5 & Constraint 7:
        Simulate DB write failure (mock log_chunk_record returning False or raising Exception).
        Verify simulator still emits every expected RiskUpdate item without crashing.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = os.path.join(tmp_dir, "test_call.wav")
            generate_sample_wav(wav_path, duration_sec=6.0, frequency=300.0)

            # Test 1: Mock returning False
            with patch("app.services.simulator.log_chunk_record_async", return_value=False):
                import asyncio
                async def _run():
                    updates = []
                    async for update in simulate_call(wav_path, chunk_duration_sec=3.0, delay_sec=0.01):
                        updates.append(update)
                    return updates

                updates = asyncio.run(_run())
                self.assertEqual(len(updates), 2)

            # Test 2: Mock raising controlled SQLite Exception
            with patch("app.services.simulator.log_chunk_record_async", side_effect=sqlite3.OperationalError("Simulated DB Disk Full")):
                import asyncio
                async def _run_err():
                    updates = []
                    async for update in simulate_call(wav_path, chunk_duration_sec=3.0, delay_sec=0.01):
                        updates.append(update)
                    return updates

                updates_err = asyncio.run(_run_err())
                self.assertEqual(len(updates_err), 2)


if __name__ == "__main__":
    unittest.main()
