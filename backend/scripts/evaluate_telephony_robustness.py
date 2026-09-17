"""
VoxGuard Telephony Robustness Baseline Evaluation Script

Evaluates VoxGuard's current real Spectra-AASIST3 ML model on a balanced subset of 6 public benchmark clips
(3 genuine Indic language speech samples, 3 ASVspoof synthetic spoof samples) under 3 simulated telephony call-quality profiles:
1. original (unmodified 16kHz PCM WAV)
2. narrowband_8khz (resampled to 8kHz and returned to pipeline format)
3. narrowband_8khz_noise_20db (narrowband 8kHz audio with deterministic 20 dB SNR Gaussian background noise)

Measures detector behavior under simulated band-limiting and noise without altering model weights, thresholds,
or post-processing logic.
"""

import io
import os
import sys
import time
import wave
import json
import math
import statistics
import numpy as np
from pathlib import Path
from scipy.signal import resample_poly
from typing import Dict, Any, List, Tuple

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.ml_model import analyze_chunk
from app.ml.flag_filters import PROSODY_ONLY_FLAGS


def transform_audio(audio_bytes: bytes, profile: str, noise_seed: int = 42) -> bytes:
    """
    Applies deterministic simulated telephony-like transformations to 16kHz mono PCM WAV bytes.
    Profiles:
    - 'original': unmodified audio bytes.
    - 'narrowband_8khz': resamples to 8kHz, then back to 16kHz (simulating narrowband band-limiting).
    - 'narrowband_8khz_noise_20db': narrowband 8kHz audio with deterministic Gaussian noise at 20 dB SNR.

    Returns re-encoded 16kHz 16-bit mono PCM WAV bytes.
    """
    if profile == "original":
        return audio_bytes

    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        sr = wav.getframerate()
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        n_frames = wav.getnframes()
        frames = wav.readframes(n_frames)

    if sample_width != 2 or n_frames == 0:
        return audio_bytes

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    # 1. Downsample to 8kHz, then upsample back to 16kHz to simulate telephone channel band-limiting
    if sr == 16000:
        audio_8k = resample_poly(audio, 1, 2)
        audio_nb = resample_poly(audio_8k, 2, 1)
    else:
        audio_8k = resample_poly(audio, 8000, sr)
        audio_nb = resample_poly(audio_8k, 16000, 8000)

    expected_len = int(len(audio) * 16000 / sr) if sr != 16000 else len(audio)
    if len(audio_nb) > expected_len:
        audio_nb = audio_nb[:expected_len]
    elif len(audio_nb) < expected_len:
        audio_nb = np.pad(audio_nb, (0, expected_len - len(audio_nb)))

    if profile == "narrowband_8khz":
        final_audio = audio_nb
    elif profile == "narrowband_8khz_noise_20db":
        # Add deterministic additive white Gaussian noise at target 20 dB SNR
        p_signal = float(np.mean(audio_nb ** 2))
        if p_signal > 1e-9:
            p_noise = p_signal / (10.0 ** (20.0 / 10.0))  # 20 dB SNR
            sigma = float(np.sqrt(p_noise))
            rng = np.random.RandomState(noise_seed)
            noise = rng.normal(0.0, sigma, len(audio_nb)).astype(np.float32)
            final_audio = audio_nb + noise
        else:
            final_audio = audio_nb
    else:
        raise ValueError(f"Unknown transformation profile: {profile}")

    final_audio = np.clip(final_audio, -1.0, 1.0)
    pcm_int16 = (final_audio * 32767.0).astype(np.int16)

    out_io = io.BytesIO()
    with wave.open(out_io, "wb") as out_wav:
        out_wav.setnchannels(1)
        out_wav.setsampwidth(2)
        out_wav.setframerate(16000)
        out_wav.writeframes(pcm_int16.tobytes())

    return out_io.getvalue()


def compute_telephony_group_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes group level metrics, alert level distribution, and flag statistics for evaluation results."""
    if not results:
        return {}

    scores = [r["chunk_score"] for r in results]
    latencies = [r["inference_latency_sec"] for r in results]
    alerts = [r["alert_level"] for r in results]

    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    median_score = (
        (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2.0
        if n % 2 == 0
        else sorted_scores[n // 2]
    )

    synthetic_artifact_count = sum(
        1 for r in results if "synthetic_artifact" in r["public_flags"]
    )

    return {
        "count": n,
        "mean_chunk_score": round(statistics.mean(scores), 4),
        "median_chunk_score": round(median_score, 4),
        "min_chunk_score": round(min(scores), 4),
        "max_chunk_score": round(max(scores), 4),
        "alert_counts": {
            "low": alerts.count("low"),
            "medium": alerts.count("medium"),
            "high": alerts.count("high"),
        },
        "high_risk_count": alerts.count("high"),
        "synthetic_artifact_flag_count": synthetic_artifact_count,
        "avg_inference_latency_sec": round(statistics.mean(latencies), 4),
    }


def get_benchmark_clips() -> List[Dict[str, Any]]:
    """Returns the balanced subset of 6 benchmark audio clips."""
    return [
        {
            "clip_id": "hi_in_spk1_female_1608",
            "label": "bonafide",
            "language_or_system": "Hindi (Google FLEURS)",
            "relative_path": "data/benchmark_indic_language/hi_in_spk1_female_1608.wav",
        },
        {
            "clip_id": "ta_in_spk1_female_1623",
            "label": "bonafide",
            "language_or_system": "Tamil (Google FLEURS)",
            "relative_path": "data/benchmark_indic_language/ta_in_spk1_female_1623.wav",
        },
        {
            "clip_id": "te_in_spk1_female_1519",
            "label": "bonafide",
            "language_or_system": "Telugu (Google FLEURS)",
            "relative_path": "data/benchmark_indic_language/te_in_spk1_female_1519.wav",
        },
        {
            "clip_id": "LA_E_5932896",
            "label": "spoof",
            "language_or_system": "ASVspoof 2019 LA",
            "relative_path": "data/test_audio/asvspoof_spoof_clips/LA_E_5932896.wav",
        },
        {
            "clip_id": "LA_E_8877452",
            "label": "spoof",
            "language_or_system": "ASVspoof 2019 LA",
            "relative_path": "data/test_audio/asvspoof_spoof_clips/LA_E_8877452.wav",
        },
        {
            "clip_id": "LA_E_6977360",
            "label": "spoof",
            "language_or_system": "ASVspoof 2019 LA",
            "relative_path": "data/test_audio/asvspoof_spoof_clips/LA_E_6977360.wav",
        },
    ]


def run_telephony_evaluation() -> Dict[str, Any]:
    """Runs real ML model evaluation across 6 clips and 3 profiles."""
    clips = get_benchmark_clips()
    profiles = ["original", "narrowband_8khz", "narrowband_8khz_noise_20db"]

    detailed_results = []

    for clip in clips:
        full_path = backend_dir / clip["relative_path"]
        if not full_path.exists():
            raise FileNotFoundError(f"Audio clip file not found: {full_path}")

        with open(full_path, "rb") as f:
            raw_bytes = f.read()

        duration_sec = 0.0
        with wave.open(str(full_path), "rb") as wav:
            duration_sec = round(wav.getnframes() / float(wav.getframerate()), 2)

        for profile in profiles:
            transformed_bytes = transform_audio(raw_bytes, profile=profile, noise_seed=42)

            t0 = time.time()
            res = analyze_chunk(transformed_bytes)
            latency_sec = round(time.time() - t0, 3)

            chunk_score = res["chunk_score"]
            confidence = res["confidence"]
            public_flags = res["flags"]

            # Quarantined prosody flag check
            violating_flags = set(public_flags) & set(PROSODY_ONLY_FLAGS)
            if violating_flags:
                raise ValueError(
                    f"Quarantine violation detected on {clip['clip_id']} ({profile}): "
                    f"quarantined flags found in public output: {violating_flags}"
                )

            # Determine alert level based on chunk_score thresholds
            if chunk_score > 0.70:
                alert_level = "high"
            elif chunk_score >= 0.40:
                alert_level = "medium"
            else:
                alert_level = "low"

            record = {
                "clip_id": clip["clip_id"],
                "label": clip["label"],
                "source": clip["language_or_system"],
                "profile": profile,
                "input_duration_sec": duration_sec,
                "chunk_score": chunk_score,
                "confidence": confidence,
                "public_flags": public_flags,
                "alert_level": alert_level,
                "inference_latency_sec": latency_sec,
            }
            detailed_results.append(record)

    # Compute group summaries
    genuine_results = [r for r in detailed_results if r["label"] == "bonafide"]
    spoof_results = [r for r in detailed_results if r["label"] == "spoof"]

    summary_genuine = compute_telephony_group_summary(genuine_results)
    summary_spoof = compute_telephony_group_summary(spoof_results)

    # Profile-level summaries
    by_profile = {}
    for prof in profiles:
        prof_gen = [r for r in genuine_results if r["profile"] == prof]
        prof_spf = [r for r in spoof_results if r["profile"] == prof]
        by_profile[prof] = {
            "genuine": compute_telephony_group_summary(prof_gen),
            "spoof": compute_telephony_group_summary(prof_spf),
        }

    return {
        "detailed_results": detailed_results,
        "genuine_summary": summary_genuine,
        "spoof_summary": summary_spoof,
        "profile_summaries": by_profile,
    }


if __name__ == "__main__":
    print("=" * 80)
    print(" VoxGuard Telephony Robustness Baseline Evaluation")
    print("=" * 80)

    try:
        report = run_telephony_evaluation()
        print("\n--- PER-CLIP / PER-PROFILE RESULTS ---")
        print(
            f"{'Clip ID':<23} | {'Label':<8} | {'Profile':<26} | {'Score':<6} | {'Alert':<6} | {'Conf':<5} | {'Flags'}"
        )
        print("-" * 105)
        for r in report["detailed_results"]:
            print(
                f"{r['clip_id']:<23} | {r['label']:<8} | {r['profile']:<26} | {r['chunk_score']:<6.4f} | {r['alert_level']:<6} | {r['confidence']:<5.2f} | {r['public_flags']}"
            )

        print("\n--- GENUINE SPEECH SUMMARY ---")
        print(json.dumps(report["genuine_summary"], indent=2))

        print("\n--- SPOOF SPEECH SUMMARY ---")
        print(json.dumps(report["spoof_summary"], indent=2))

        print("\n--- SUMMARY BY PROFILE ---")
        print(json.dumps(report["profile_summaries"], indent=2))

        print("\nEvaluation completed successfully.")
    except Exception as err:
        print(f"\nEvaluation failed with error: {err}")
        sys.exit(1)
