"""
Offline Unit Tests for VoxGuard Speaker Verification Module (app.ml.speaker_verification)

Tests:
1. Mock speaker-model embeddings
2. Same-speaker embeddings produce high similarity and low identity drift
3. Different-speaker embeddings produce low similarity and high identity drift (identity_mismatch flag)
4. Missing/invalid reference produces safe status ('reference_unavailable')
5. Model unavailable produces safe status ('identity_unavailable')
6. Reference state is completely cleared after session stop / clear()
7. Verification on silent/invalid/short audio returns safe non-crash quality status
"""

import unittest
import numpy as np
from unittest.mock import MagicMock, patch

from app.ml.speaker_verification import (
    SessionIdentityTracker,
    SpeakerEmbeddingModel,
    IDENTITY_MISMATCH_DRIFT_THRESHOLD
)


class MockSpeakerModel:
    """Mock speaker embedding model for offline testing without network or model weights."""
    def __init__(self, vector_map=None, should_fail=False):
        self.vector_map = vector_map or {}
        self.should_fail = should_fail
        self.is_loaded = not should_fail

    def compute_embedding(self, audio_array, sample_rate=16000):
        if self.should_fail:
            return None
        
        audio_len = len(audio_array)
        if audio_len in self.vector_map:
            return self.vector_map[audio_len]
        
        # Return a deterministic 128-D normalized embedding vector based on mean energy
        val = float(np.mean(np.abs(audio_array))) + 0.1
        vec = np.ones(128, dtype=np.float32) * val
        return vec / np.linalg.norm(vec)


class TestSpeakerVerificationModule(unittest.TestCase):

    def test_same_speaker_low_identity_drift(self):
        """Verify same-speaker embeddings produce high similarity and low identity drift."""
        # Create identical 128D embedding vector for enrollment and verification
        speaker_a_vec = np.random.randn(128).astype(np.float32)
        speaker_a_vec /= np.linalg.norm(speaker_a_vec)

        mock_model = MockSpeakerModel(should_fail=False)
        mock_model.compute_embedding = MagicMock(return_value=speaker_a_vec)

        tracker = SessionIdentityTracker(session_id="test_same_speaker", custom_model=mock_model)
        
        # 1-second sine wave float audio
        ref_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        enroll_res = tracker.enroll_reference(ref_audio)
        self.assertEqual(enroll_res["status"], "ok")
        self.assertTrue(tracker.is_enrolled)

        # Verify chunk from same speaker
        chunk_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        eval_res = tracker.verify_chunk(chunk_audio)

        self.assertEqual(eval_res["status"], "ok")
        self.assertAlmostEqual(eval_res["speaker_similarity"], 1.0, places=3)
        self.assertAlmostEqual(eval_res["identity_drift"], 0.0, places=3)
        self.assertNotIn("identity_mismatch", eval_res["flags"])

    def test_different_speaker_high_identity_drift(self):
        """Verify different-speaker orthogonal embeddings produce low similarity and identity_mismatch flag."""
        # Orthogonal embedding vectors
        speaker_a_vec = np.zeros(128, dtype=np.float32)
        speaker_a_vec[0] = 1.0

        speaker_b_vec = np.zeros(128, dtype=np.float32)
        speaker_b_vec[1] = 1.0  # Orthogonal vector (cosine sim = 0.0, normalized sim = 0.5, drift = 0.5)

        mock_model = MockSpeakerModel()
        mock_model.compute_embedding = MagicMock(side_effect=[speaker_a_vec, speaker_b_vec])

        tracker = SessionIdentityTracker(session_id="test_diff_speaker", custom_model=mock_model)
        
        ref_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        enroll_res = tracker.enroll_reference(ref_audio)
        self.assertEqual(enroll_res["status"], "ok")

        chunk_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        eval_res = tracker.verify_chunk(chunk_audio)

        self.assertEqual(eval_res["status"], "ok")
        self.assertLess(eval_res["speaker_similarity"], 0.60)
        self.assertGreater(eval_res["identity_drift"], IDENTITY_MISMATCH_DRIFT_THRESHOLD)
        self.assertIn("identity_mismatch", eval_res["flags"])

    def test_missing_or_invalid_reference_status(self):
        """Verify verifying a chunk without an enrolled reference returns reference_unavailable."""
        tracker = SessionIdentityTracker(session_id="test_no_ref")
        self.assertFalse(tracker.is_enrolled)

        chunk_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        eval_res = tracker.verify_chunk(chunk_audio)

        self.assertEqual(eval_res["status"], "reference_unavailable")
        self.assertEqual(eval_res["identity_drift"], 0.0)
        self.assertIn("reference_unavailable", eval_res["flags"])

    def test_model_unavailable_safe_fallback(self):
        """Verify model failure returns identity_unavailable safely without crashing."""
        failing_model = MockSpeakerModel(should_fail=True)
        tracker = SessionIdentityTracker(session_id="test_model_fail", custom_model=failing_model)

        ref_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        enroll_res = tracker.enroll_reference(ref_audio)
        self.assertEqual(enroll_res["status"], "identity_unavailable")

    def test_reference_state_cleared_on_session_stop(self):
        """Verify clear() completely wipes enrolled reference embedding from memory."""
        vec = np.ones(128, dtype=np.float32) / np.sqrt(128)
        mock_model = MockSpeakerModel()
        mock_model.compute_embedding = MagicMock(return_value=vec)

        tracker = SessionIdentityTracker(session_id="test_clear", custom_model=mock_model)
        ref_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        tracker.enroll_reference(ref_audio)
        self.assertTrue(tracker.is_enrolled)
        self.assertIsNotNone(tracker.reference_embedding)

        # Clear session reference
        tracker.clear()

        self.assertFalse(tracker.is_enrolled)
        self.assertIsNone(tracker.reference_embedding)

        # Subsequent verification returns reference_unavailable
        chunk_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        eval_res = tracker.verify_chunk(chunk_audio)
        self.assertEqual(eval_res["status"], "reference_unavailable")

    def test_silent_or_short_audio_quality_handling(self):
        """Verify silent or short audio returns safe status without identity mismatch claims."""
        vec = np.ones(128, dtype=np.float32) / np.sqrt(128)
        mock_model = MockSpeakerModel()
        mock_model.compute_embedding = MagicMock(return_value=vec)

        tracker = SessionIdentityTracker(session_id="test_quality", custom_model=mock_model)
        ref_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        tracker.enroll_reference(ref_audio)

        # Silent chunk audio
        silent_audio = np.zeros(16000, dtype=np.float32)
        eval_silent = tracker.verify_chunk(silent_audio)
        self.assertEqual(eval_silent["status"], "silent_audio")
        self.assertEqual(eval_silent["identity_drift"], 0.0)

        # Short chunk audio (<0.5s = 4000 samples)
        short_audio = np.sin(np.linspace(0, 20, 4000)).astype(np.float32) * 0.5
        eval_short = tracker.verify_chunk(short_audio)
        self.assertEqual(eval_short["status"], "insufficient_speech")
        self.assertEqual(eval_short["identity_drift"], 0.0)

    def test_reference_path_validation_and_rejection(self):
        """Verify strict path validation for consented_reference_audio directory."""
        from app.ml.speaker_verification import validate_consented_reference_path

        # 1. Path traversal attempt
        ok, reason, _ = validate_consented_reference_path("../../backend/main.py")
        self.assertFalse(ok)
        self.assertIn("path_outside_allowed_directory", reason)

        # 2. Outside absolute path
        ok, reason, _ = validate_consented_reference_path("C:/Windows/System32/cmd.exe")
        self.assertFalse(ok)
        self.assertIn("path_outside_allowed_directory", reason)

        # 3. Non-WAV file extension inside allowed dir
        ok, reason, _ = validate_consented_reference_path("data/consented_reference_audio/.gitkeep")
        self.assertFalse(ok)
        self.assertEqual(reason, "invalid_file_extension_must_be_wav")

        # 4. Missing WAV file inside allowed dir
        ok, reason, _ = validate_consented_reference_path("data/consented_reference_audio/non_existent.wav")
        self.assertFalse(ok)
        self.assertEqual(reason, "reference_file_not_found")

    def test_similarity_and_drift_bounds_math(self):
        """Verify raw_cosine_similarity, speaker_similarity, and identity_drift bounds."""
        mock_model = MockSpeakerModel()
        
        # Test exact cosine sim 1.0 (same vector)
        vec1 = np.ones(128, dtype=np.float32) / np.sqrt(128)
        mock_model.compute_embedding = MagicMock(side_effect=[vec1, vec1])
        
        tracker = SessionIdentityTracker("test_bounds_1", custom_model=mock_model)
        ref_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        tracker.enroll_reference(ref_audio)
        
        chunk_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32) * 0.5
        res = tracker.verify_chunk(chunk_audio)
        
        self.assertEqual(res["raw_cosine_similarity"], 1.0)
        self.assertEqual(res["speaker_similarity"], 1.0)
        self.assertEqual(res["identity_drift"], 0.0)
        self.assertGreaterEqual(res["speaker_similarity"], 0.0)
        self.assertLessEqual(res["speaker_similarity"], 1.0)
        self.assertEqual(res["identity_drift"], round(1.0 - res["speaker_similarity"], 4))

        # Test opposite vector (-1.0 cosine sim)
        mock_model_opp = MockSpeakerModel()
        mock_model_opp.compute_embedding = MagicMock(side_effect=[vec1, -vec1])
        
        tracker_opp = SessionIdentityTracker("test_bounds_opp", custom_model=mock_model_opp)
        tracker_opp.enroll_reference(ref_audio)
        res_opp = tracker_opp.verify_chunk(chunk_audio)

        self.assertEqual(res_opp["raw_cosine_similarity"], -1.0)
        self.assertEqual(res_opp["speaker_similarity"], 0.0)
        self.assertEqual(res_opp["identity_drift"], 1.0)


if __name__ == "__main__":
    unittest.main()

