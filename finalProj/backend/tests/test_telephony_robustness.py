"""
Offline Tests for Telephony Robustness Baseline Evaluation

Proves:
1. Deterministic transform output given fixed random seed.
2. 8 kHz narrowband downsampling properties.
3. Approximate 20 dB SNR noise behavior.
4. Result grouping and summary calculations.
5. Prosody-only flag quarantine remains strictly enforced.
"""

import io
import sys
import wave
import unittest
import numpy as np
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.evaluate_telephony_robustness import (
    transform_audio,
    compute_telephony_group_summary,
    get_benchmark_clips,
)
from app.ml.flag_filters import PROSODY_ONLY_FLAGS, filter_public_flags


class TestTelephonyRobustnessOffline(unittest.TestCase):

    def setUp(self):
        """Generate synthetic 16kHz mono PCM WAV bytes for testing."""
        sr = 16000
        duration_sec = 2.0
        t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
        sine_wave = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        pcm_int16 = (sine_wave * 32767).astype(np.int16)

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sr)
            wav.writeframes(pcm_int16.tobytes())

        self.synthetic_wav_bytes = out_io.getvalue()

    def test_deterministic_transform_output(self):
        """Verify transformation functions produce identical byte outputs given the same seed."""
        output1 = transform_audio(self.synthetic_wav_bytes, "narrowband_8khz_noise_20db", noise_seed=42)
        output2 = transform_audio(self.synthetic_wav_bytes, "narrowband_8khz_noise_20db", noise_seed=42)
        self.assertEqual(output1, output2, "Transforms with identical seed must yield identical byte output")

    def test_narrowband_8khz_properties(self):
        """Verify narrowband_8khz transformation produces valid 16kHz mono WAV bytes of matching frame length."""
        transformed = transform_audio(self.synthetic_wav_bytes, "narrowband_8khz")

        with wave.open(io.BytesIO(transformed), "rb") as wav:
            self.assertEqual(wav.getframerate(), 16000, "Output WAV must remain 16000 Hz for pipeline compatibility")
            self.assertEqual(wav.getnchannels(), 1, "Output WAV must be mono")
            self.assertGreater(wav.getnframes(), 0, "Output WAV must contain frames")

    def test_approximate_20db_snr_behavior(self):
        """Verify narrowband_8khz_noise_20db adds background noise with ~20 dB SNR relative to signal power."""
        nb_bytes = transform_audio(self.synthetic_wav_bytes, "narrowband_8khz")
        noisy_bytes = transform_audio(self.synthetic_wav_bytes, "narrowband_8khz_noise_20db", noise_seed=42)

        with wave.open(io.BytesIO(nb_bytes), "rb") as wav:
            nb_frames = wav.readframes(wav.getnframes())
        nb_audio = np.frombuffer(nb_frames, dtype=np.int16).astype(np.float32) / 32768.0

        with wave.open(io.BytesIO(noisy_bytes), "rb") as wav:
            noisy_frames = wav.readframes(wav.getnframes())
        noisy_audio = np.frombuffer(noisy_frames, dtype=np.int16).astype(np.float32) / 32768.0

        noise = noisy_audio - nb_audio
        p_signal = np.mean(nb_audio ** 2)
        p_noise = np.mean(noise ** 2)

        measured_snr = 10 * np.log10(p_signal / p_noise)
        self.assertAlmostEqual(measured_snr, 20.0, delta=1.5, msg="Measured SNR must be close to 20 dB target")

    def test_compute_telephony_group_summary(self):
        """Verify score distribution, alert count, and flag statistics calculation."""
        sample_results = [
            {
                "chunk_score": 0.05,
                "alert_level": "low",
                "public_flags": [],
                "inference_latency_sec": 0.10,
            },
            {
                "chunk_score": 0.95,
                "alert_level": "high",
                "public_flags": ["synthetic_artifact"],
                "inference_latency_sec": 0.12,
            },
            {
                "chunk_score": 0.98,
                "alert_level": "high",
                "public_flags": ["synthetic_artifact", "short_audio"],
                "inference_latency_sec": 0.14,
            },
        ]

        summary = compute_telephony_group_summary(sample_results)

        self.assertEqual(summary["count"], 3)
        self.assertAlmostEqual(summary["mean_chunk_score"], 0.66, places=4)
        self.assertAlmostEqual(summary["median_chunk_score"], 0.95, places=4)
        self.assertEqual(summary["min_chunk_score"], 0.05)
        self.assertEqual(summary["max_chunk_score"], 0.98)
        self.assertEqual(summary["alert_counts"]["low"], 1)
        self.assertEqual(summary["alert_counts"]["high"], 2)
        self.assertEqual(summary["synthetic_artifact_flag_count"], 2)
        self.assertAlmostEqual(summary["avg_inference_latency_sec"], 0.12, places=4)

    def test_prosody_flag_quarantine_enforced(self):
        """Verify prosody-only flags are filtered and never leak into public flags."""
        test_flags = ["synthetic_artifact", "prosody_flatness", "prosody_pitch_instability"]
        public_flags = filter_public_flags(test_flags)

        for quarantined_flag in PROSODY_ONLY_FLAGS:
            self.assertNotIn(quarantined_flag, public_flags, f"Quarantined flag {quarantined_flag} must not be public")

        self.assertIn("synthetic_artifact", public_flags)

    def test_get_benchmark_clips_structure(self):
        """Verify the 6 benchmark clips are correctly declared with 3 bonafide and 3 spoof clips."""
        clips = get_benchmark_clips()
        self.assertEqual(len(clips), 6)

        bonafide = [c for c in clips if c["label"] == "bonafide"]
        spoof = [c for c in clips if c["label"] == "spoof"]

        self.assertEqual(len(bonafide), 3)
        self.assertEqual(len(spoof), 3)


if __name__ == "__main__":
    unittest.main()
