"""
Offline tests for VoxGuard Prosody Analysis Module (app.ml.prosody)

Tests:
1. Silent / empty / corrupt audio handling
2. Varying-frequency tone signal extraction (mathematical extraction check)
3. Flat tone / low-pitch-variation signal detection (low_f0_variability / prosody_flatness)
4. Pause-heavy audio detection (high_pause_ratio)
5. Output schema & safe failure behavior
6. Integration safeguards:
   - Prosody extraction exception does not stop real ML inference
   - Threshold-generated prosody_flatness flag removed from ml_model.py
   - RiskUpdate schema 7-field contract remains unchanged
"""

import io
import math
import wave
import struct
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from app.ml.prosody import (
    extract_prosody_features,
    assess_prosody,
    LOW_F0_STD_THRESHOLD_HZ,
    HIGH_PAUSE_RATIO_THRESHOLD,
    LOW_VOICED_RATIO_THRESHOLD
)
from app.ml.ml_model import SpectraAASISTDetector
from app.models.schemas import RiskUpdate


def _generate_wav_bytes(
    duration_sec: float = 3.0,
    sample_rate: int = 16000,
    frequency_func=lambda t: 200.0,
    amplitude: float = 0.5,
    pause_segments: list = None
) -> bytes:
    """Helper to generate in-memory PCM WAV bytes with customizable pitch modulation and pauses."""
    n_samples = int(sample_rate * duration_sec)
    buffer = io.BytesIO()
    
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        samples = []
        phase = 0.0
        dt = 1.0 / sample_rate
        
        for i in range(n_samples):
            t = i * dt
            
            # Check pause segments (list of (start_sec, end_sec))
            in_pause = False
            if pause_segments:
                for p_start, p_end in pause_segments:
                    if p_start <= t <= p_end:
                        in_pause = True
                        break
            
            if in_pause:
                sample_val = 0
            else:
                freq = frequency_func(t)
                phase += 2.0 * math.pi * freq * dt
                sample_val = int(32767.0 * amplitude * math.sin(phase))
                
            sample_val = max(-32768, min(32767, sample_val))
            samples.append(sample_val)
            
        raw_pcm = struct.pack(f"<{n_samples}h", *samples)
        wav.writeframes(raw_pcm)
        
    return buffer.getvalue()


class TestProsodyAnalysisModule(unittest.TestCase):

    def test_corrupt_empty_silent_audio_handling(self):
        """Verify explicit quality status for invalid/empty/silent WAV input."""
        # Empty bytes
        res_empty = extract_prosody_features(b"")
        self.assertEqual(res_empty["status"], "invalid_audio")
        self.assertIsNone(res_empty["pitch_mean_hz"])

        # Corrupt header
        res_corrupt = extract_prosody_features(b"RIFF_invalid_header_bytes_too_short")
        self.assertEqual(res_corrupt["status"], "invalid_audio")

        # Silent audio WAV
        silent_wav = _generate_wav_bytes(duration_sec=3.0, amplitude=0.0)
        res_silent = extract_prosody_features(silent_wav)
        self.assertEqual(res_silent["status"], "silent_audio")

        # Assess silent audio
        eval_silent = assess_prosody(res_silent)
        self.assertIn("silent_audio", eval_silent["flags"])
        self.assertEqual(eval_silent["prosody_score"], 0.0)

    def test_varying_frequency_tone_signal(self):
        """
        Verify pitch and voiced features extraction on a frequency-modulated test signal.
        Note: Used for mathematical extraction verification, not classified as human speech.
        """
        # Frequency sweeps from 150 Hz to 250 Hz over 3 seconds
        varying_wav = _generate_wav_bytes(
            duration_sec=3.0,
            frequency_func=lambda t: 150.0 + 33.3 * t,
            amplitude=0.5
        )
        res = extract_prosody_features(varying_wav)

        self.assertEqual(res["status"], "ok")
        self.assertIsNotNone(res["pitch_mean_hz"])
        self.assertIsNotNone(res["pitch_std_hz"])
        self.assertGreater(res["pitch_std_hz"], LOW_F0_STD_THRESHOLD_HZ)
        self.assertGreater(res["voiced_ratio"], 0.70)
        self.assertIn("speech_rate_proxy", res)

        eval_res = assess_prosody(res)
        self.assertNotIn("low_f0_variability", eval_res["reason_codes"])
        self.assertNotIn("prosody_flatness", eval_res["flags"])

    def test_flat_tone_low_pitch_variation(self):
        """Verify flat tone signal triggers low_f0_variability reason code and prosody_flatness flag."""
        # Constant 200 Hz tone (zero pitch std dev)
        flat_wav = _generate_wav_bytes(
            duration_sec=3.0,
            frequency_func=lambda t: 200.0,
            amplitude=0.5
        )
        res = extract_prosody_features(flat_wav)

        self.assertEqual(res["status"], "ok")
        self.assertIsNotNone(res["pitch_std_hz"])
        self.assertLess(res["pitch_std_hz"], LOW_F0_STD_THRESHOLD_HZ)

        eval_res = assess_prosody(res)
        self.assertIn("low_f0_variability", eval_res["reason_codes"])
        self.assertIn("prosody_flatness", eval_res["flags"])
        self.assertGreater(eval_res["prosody_score"], 0.50)

    def test_pause_heavy_audio_detection(self):
        """Verify audio with long pauses triggers high_pause_ratio reason code and flag."""
        # Tone for 0.5s, silence for 2.0s, tone for 0.5s (>60% pause ratio)
        pause_wav = _generate_wav_bytes(
            duration_sec=3.0,
            frequency_func=lambda t: 220.0,
            amplitude=0.5,
            pause_segments=[(0.5, 2.5)]
        )
        res = extract_prosody_features(pause_wav)

        self.assertGreater(res["pause_duration_ratio"], HIGH_PAUSE_RATIO_THRESHOLD)

        eval_res = assess_prosody(res)
        self.assertIn("high_pause_ratio", eval_res["reason_codes"])
        self.assertIn("high_pause_ratio", eval_res["flags"])

    def test_dual_input_support(self):
        """Verify extract_prosody_features supports both raw WAV bytes and float arrays."""
        # 1. Raw bytes
        wav_bytes = _generate_wav_bytes(duration_sec=1.0, frequency_func=lambda t: 200.0)
        res_bytes = extract_prosody_features(wav_bytes)
        self.assertIn(res_bytes["status"], ["ok", "insufficient_voiced_speech"])

        # 2. Float array (pre-normalized)
        t = np.linspace(0, 1.0, 16000, endpoint=False, dtype=np.float32)
        float_audio = (0.5 * np.sin(2 * np.pi * 200.0 * t)).astype(np.float32)
        res_array = extract_prosody_features(float_audio, sample_rate=16000)
        self.assertIn(res_array["status"], ["ok", "insufficient_voiced_speech"])

    def test_prosody_exception_does_not_stop_real_ml_inference(self):
        """Safeguard 7: Exception in prosody module must not crash Spectra ML inference."""
        detector = SpectraAASISTDetector.__new__(SpectraAASISTDetector)
        detector.is_loaded = True
        detector._inference_lock = MagicMock()
        detector.model = MagicMock()
        
        # Mock model output logits
        mock_output = MagicMock()
        import torch
        mock_output.logits = torch.tensor([[5.0, -5.0]])  # High spoof prob ~0.99
        detector.model.return_value = mock_output

        audio_samples = np.zeros(64600, dtype=np.float32)

        # Patch prosody extraction to throw an unexpected exception
        with patch("app.ml.ml_model.extract_prosody_features", side_effect=RuntimeError("Prosody crash simulation")):
            res = detector.predict_parsed(audio_samples, rms_energy=0.1, flags=[])

            # Inference succeeds with Spectra score
            self.assertGreater(res["chunk_score"], 0.90)
            self.assertNotIn("prosody_unavailable", res["flags"])
            self.assertIn("synthetic_artifact", res["flags"])

    def test_threshold_generated_prosody_flatness_removed_from_ml_model(self):
        """Safeguard 7: Spectra chunk_score threshold > 0.40 alone must NOT append prosody_flatness."""
        detector = SpectraAASISTDetector.__new__(SpectraAASISTDetector)
        detector.is_loaded = True
        detector._inference_lock = MagicMock()
        detector.model = MagicMock()

        # Mock model output logits corresponding to chunk_score ~0.55 (>0.40 but <0.70)
        import torch
        mock_output = MagicMock()
        mock_output.logits = torch.tensor([[0.2, 0.0]])  # spoof_prob ~ 0.55
        detector.model.return_value = mock_output

        audio_samples = np.zeros(64600, dtype=np.float32)

        # Patch prosody module to return normal prosody (no flags)
        with patch("app.ml.ml_model.extract_prosody_features", return_value={"status": "ok", "pitch_std_hz": 25.0}), \
             patch("app.ml.ml_model.assess_prosody", return_value={"flags": [], "reason_codes": []}):
            res = detector.predict_parsed(audio_samples, rms_energy=0.1, flags=[])

            self.assertGreater(res["chunk_score"], 0.50)
            self.assertLess(res["chunk_score"], 0.70)
            # Must NOT contain prosody_flatness just because score > 0.40!
            self.assertNotIn("prosody_flatness", res["flags"])

    def test_risk_update_7_field_contract_unmodified(self):
        """Safeguard 7: Ensure RiskUpdate schema contract remains 7 fields exactly."""
        update = RiskUpdate(
            chunk_id="chunk_001",
            chunk_score=0.45,
            rolling_risk_score=0.30,
            confidence=0.92,
            flags=["prosody_flatness"],
            alert_level="low"
        )
        data = update.model_dump()
        expected_fields = {"chunk_id", "timestamp", "chunk_score", "rolling_risk_score", "confidence", "flags", "alert_level"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_short_chunk_prosody_untiled_vs_spectra_padded(self):

        """
        Regression test: Verify short audio chunks preserve original duration for prosody
        while providing tiled/padded waveform to Spectra-AASIST3.
        """
        from app.ml.ml_model import parse_audio_bytes, REQUIRED_SAMPLES

        # 1.5s short chunk (24,000 samples) with 0.5s tone, 0.5s pause, 0.5s tone
        short_wav = _generate_wav_bytes(
            duration_sec=1.5,
            frequency_func=lambda t: 220.0,
            amplitude=0.5,
            pause_segments=[(0.5, 1.0)]
        )

        original_audio, spectra_audio, rms_energy, flags = parse_audio_bytes(short_wav)

        # Assert two separate waveforms preserved
        self.assertEqual(len(original_audio), 24000)
        self.assertEqual(len(spectra_audio), REQUIRED_SAMPLES)
        self.assertIn("short_audio", flags)

        # Verify prosody features extracted from untiled original_audio
        p_features_orig = extract_prosody_features(original_audio, sample_rate=16000)
        self.assertEqual(p_features_orig["duration_sec"], 1.5)
        # Pause duration ratio is ~0.33 (0.5s pause out of 1.5s)
        self.assertAlmostEqual(p_features_orig["pause_duration_ratio"], 0.33, delta=0.08)

        # Contrast with tiled spectra_audio (demonstrating why prosody must NOT use tiled audio)
        p_features_tiled = extract_prosody_features(spectra_audio, sample_rate=16000)
        self.assertGreater(p_features_tiled["duration_sec"], 4.0)

        # Verify predict_parsed receives original_audio for prosody and spectra_audio for model
        detector = SpectraAASISTDetector.__new__(SpectraAASISTDetector)
        detector.is_loaded = True
        detector._inference_lock = MagicMock()
        detector.model = MagicMock()
        
        import torch
        mock_output = MagicMock()
        mock_output.logits = torch.tensor([[0.1, 0.5]])
        detector.model.return_value = mock_output

        with patch("app.ml.ml_model.extract_prosody_features", wraps=extract_prosody_features) as mock_p_extract:
            res = detector.predict_parsed(
                audio=original_audio,
                rms_energy=rms_energy,
                flags=flags,
                spectra_audio=spectra_audio
            )
            # Verify extract_prosody_features was called with untiled original_audio (len 24000)
            mock_p_extract.assert_called_once()
            called_audio = mock_p_extract.call_args[0][0]
            self.assertEqual(len(called_audio), 24000)
            self.assertIn("short_audio", res["flags"])


if __name__ == "__main__":
    unittest.main()

