import os
import asyncio
import tempfile
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from app.ml.analyzer import analyze_chunk_dispatch
from app.services.simulator import simulate_call
from app.utils.audio_generator import generate_sample_wav


class TestMLBackendIntegration(unittest.TestCase):

    def test_invalid_ml_mode_raises_error(self):
        """Verify invalid VOXGUARD_ML_MODE values raise ValueError and do not silently fall back to stub."""
        with patch.dict(os.environ, {"VOXGUARD_ML_MODE": "invalid_mode"}):
            with self.assertRaises(ValueError) as ctx:
                asyncio.run(analyze_chunk_dispatch(b"dummy_bytes"))
            self.assertIn("Invalid VOXGUARD_ML_MODE: 'invalid_mode'", str(ctx.exception))

    def test_stub_ml_mode_routing(self):
        """Verify VOXGUARD_ML_MODE=stub routes to analyze_chunk_stub."""
        with patch.dict(os.environ, {"VOXGUARD_ML_MODE": "stub"}):
            res = asyncio.run(analyze_chunk_dispatch(b"dummy_bytes", step=1, scenario="clean"))
            self.assertIn("chunk_score", res)
            self.assertIn("confidence", res)
            self.assertIn("flags", res)

    def test_real_ml_mode_dispatch_offline(self):
        """
        Verify VOXGUARD_ML_MODE=real calls analyze_chunk_real without model loading.
        Patches analyze_chunk in ml_model.
        """
        with patch.dict(os.environ, {"VOXGUARD_ML_MODE": "real"}):
            mock_result = {"chunk_score": 0.85, "confidence": 0.95, "flags": ["synthetic_artifact"]}
            with patch("app.ml.analyzer.analyze_chunk_real", return_value=mock_result) as mock_real:
                res = asyncio.run(analyze_chunk_dispatch(b"dummy_bytes"))
                self.assertEqual(res, mock_result)
                mock_real.assert_called_once_with(b"dummy_bytes")

    def test_simulator_calls_analyzer_once_per_chunk(self):
        """
        Exact lookup point patching requirement:
        Patch analyze_chunk_dispatch inside app.services.simulator.
        Assert each chunk calls the analyzer exactly once, and output reaches RiskUpdate.
        Assert real ML loader is never called during backend tests.
        """
        mock_analyzer = AsyncMock(return_value={
            "chunk_score": 0.82,
            "confidence": 0.96,
            "flags": ["synthetic_artifact"]
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = f"{tmp_dir}/test_call.wav"
            generate_sample_wav(wav_path, duration_sec=6.0, frequency=300.0)

            with patch("app.services.simulator.analyze_chunk_dispatch", mock_analyzer):
                async def _run():
                    updates = []
                    async for update in simulate_call(wav_path, chunk_duration_sec=3.0, delay_sec=0.01):
                        updates.append(update)
                    return updates

                updates = asyncio.run(_run())

                self.assertEqual(len(updates), 2)
                self.assertEqual(mock_analyzer.call_count, 2)

                for update in updates:
                    self.assertEqual(update.chunk_score, 0.82)
                    self.assertEqual(update.confidence, 0.96)
                    self.assertIn("synthetic_artifact", update.flags)
                    self.assertIn(update.alert_level, ["low", "medium", "high"])

    def test_model_unavailable_and_error_flags_reach_client(self):
        """Verify model_unavailable and silent_audio flags pass through to RiskUpdate unchanged."""
        mock_unavailable = AsyncMock(return_value={
            "chunk_score": 0.5,
            "confidence": 0.0,
            "flags": ["model_unavailable", "silent_audio"]
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = f"{tmp_dir}/test_call.wav"
            generate_sample_wav(wav_path, duration_sec=6.0, frequency=300.0)

            with patch("app.services.simulator.analyze_chunk_dispatch", mock_unavailable):
                async def _run():
                    updates = []
                    async for update in simulate_call(wav_path, chunk_duration_sec=3.0, delay_sec=0.01):
                        updates.append(update)
                    return updates

                updates = asyncio.run(_run())

                self.assertEqual(len(updates), 2)
                for update in updates:
                    self.assertEqual(update.chunk_score, 0.5)
                    self.assertEqual(update.confidence, 0.0)
                    self.assertIn("model_unavailable", update.flags)
                    self.assertIn("silent_audio", update.flags)

    def test_inference_error_flag_reaches_client(self):
        """
        Prompt 3.5 Assertion:
        Simulate an analyzer response containing ["inference_error"] and verify that exact flag reaches RiskUpdate.flags.
        """
        mock_error = AsyncMock(return_value={
            "chunk_score": 0.5,
            "confidence": 0.0,
            "flags": ["inference_error"]
        })

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav_path = f"{tmp_dir}/test_call.wav"
            generate_sample_wav(wav_path, duration_sec=6.0, frequency=300.0)

            with patch("app.services.simulator.analyze_chunk_dispatch", mock_error):
                async def _run():
                    updates = []
                    async for update in simulate_call(wav_path, chunk_duration_sec=3.0, delay_sec=0.01):
                        updates.append(update)
                    return updates

                updates = asyncio.run(_run())

                self.assertEqual(len(updates), 2)
                for update in updates:
                    self.assertEqual(update.chunk_score, 0.5)
                    self.assertEqual(update.confidence, 0.0)
                    self.assertIn("inference_error", update.flags)


if __name__ == "__main__":
    unittest.main()
