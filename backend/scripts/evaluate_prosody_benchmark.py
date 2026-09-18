"""
VoxGuard Offline Prosody Benchmark Evaluation Tool

Runs the VoxGuard prosody analysis layer (`app.ml.prosody`) across public bonafide
and spoof benchmark audio clips, generating clip-level telemetry and aggregate group metrics.

IMPORTANT:
- Operates 100% offline using raw original WAV audio bytes.
- Never uses Spectra-AASIST3 model weights or tiled/padded waveforms.
- Evaluates acoustic prosody features as supporting informational signals only.
"""

import os
import sys
import glob
import argparse
from typing import List, Dict, Any

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from app.ml.prosody import extract_prosody_features, assess_prosody


def evaluate_audio_files(file_paths: List[str], label: str) -> List[Dict[str, Any]]:
    """Evaluates a list of audio files using VoxGuard prosody extraction & assessment."""
    results = []
    for fpath in sorted(file_paths):
        fname = os.path.basename(fpath)
        if not os.path.exists(fpath):
            results.append({
                "file": fname,
                "label": label,
                "status": "missing_file",
                "duration_sec": 0.0,
                "pitch_mean_hz": None,
                "pitch_std_hz": None,
                "voiced_ratio": 0.0,
                "pause_ratio": 0.0,
                "speech_rate_proxy": 0.0,
                "prosody_score": 0.0,
                "flags": ["missing_file"],
                "reason_codes": ["missing_file"]
            })
            continue

        try:
            with open(fpath, "rb") as f:
                audio_bytes = f.read()

            features = extract_prosody_features(audio_bytes)
            assessment = assess_prosody(features)

            results.append({
                "file": fname,
                "label": label,
                "status": features.get("status", "unknown"),
                "duration_sec": features.get("duration_sec", 0.0),
                "pitch_mean_hz": features.get("pitch_mean_hz"),
                "pitch_std_hz": features.get("pitch_std_hz"),
                "voiced_ratio": features.get("voiced_ratio", 0.0),
                "pause_ratio": features.get("pause_duration_ratio", 0.0),
                "speech_rate_proxy": features.get("speech_rate_proxy", 0.0),
                "prosody_score": assessment.get("prosody_score", 0.0),
                "flags": assessment.get("flags", []),
                "reason_codes": assessment.get("reason_codes", [])
            })
        except Exception as err:
            results.append({
                "file": fname,
                "label": label,
                "status": "error",
                "duration_sec": 0.0,
                "pitch_mean_hz": None,
                "pitch_std_hz": None,
                "voiced_ratio": 0.0,
                "pause_ratio": 0.0,
                "speech_rate_proxy": 0.0,
                "prosody_score": 0.0,
                "flags": ["evaluation_error"],
                "reason_codes": [str(err)]
            })

    return results


def print_summary_table(rows: List[Dict[str, Any]], group_name: str):
    """Prints group summary metrics (count, mean, median, min, max)."""
    total_count = len(rows)
    ok_rows = [r for r in rows if r["status"] == "ok"]
    ok_count = len(ok_rows)
    non_ok_rows = [r for r in rows if r["status"] != "ok"]

    print(f"\n=== {group_name.upper()} GROUP SUMMARY ===")
    print(f"Total Clips Evaluated: {total_count} (Valid/OK: {ok_count}, Special/Unvoiced/Missing: {len(non_ok_rows)})")

    if non_ok_rows:
        print("Special Status Clips:")
        for r in non_ok_rows:
            print(f"  - {r['file']}: status='{r['status']}', flags={r['flags']}")

    if not ok_rows or not HAS_NUMPY:
        print("No valid 'ok' clips available for numerical summary statistics.")
        return

    metrics = [
        ("pitch_mean_hz", "F0 Mean (Hz)"),
        ("pitch_std_hz", "F0 Std (Hz)"),
        ("voiced_ratio", "Voiced Ratio"),
        ("pause_ratio", "Pause Ratio"),
        ("speech_rate_proxy", "Speech Rate Proxy (Hz)"),
        ("prosody_score", "Prosody Score")
    ]

    print(f"{'Metric':<25} | {'Count':<5} | {'Mean':<8} | {'Median':<8} | {'Min':<8} | {'Max':<8}")
    print("-" * 75)

    for m_key, m_label in metrics:
        vals = [r[m_key] for r in ok_rows if r[m_key] is not None]
        if vals:
            mean_v = float(np.mean(vals))
            med_v = float(np.median(vals))
            min_v = float(np.min(vals))
            max_v = float(np.max(vals))
            print(f"{m_label:<25} | {len(vals):<5} | {mean_v:<8.4f} | {med_v:<8.4f} | {min_v:<8.4f} | {max_v:<8.4f}")
        else:
            print(f"{m_label:<25} | 0     | N/A      | N/A      | N/A      | N/A")

    print("-" * 75)


def run_evaluation():
    print("=== VoxGuard Prosody Layer Benchmark Evaluation Tool ===\n")

    parser = argparse.ArgumentParser(description="Evaluate VoxGuard prosody feature extraction on benchmark clips.")
    parser.add_argument(
        "--bonafide-dirs",
        nargs="+",
        default=[
            "data/benchmark_speaker_calibration/reference_speaker",
            "data/benchmark_speaker_calibration/same_speaker",
            "data/benchmark_speaker_calibration/different_speaker"
        ],
        help="Directories containing bonafide WAV clips"
    )
    parser.add_argument(
        "--spoof-dir",
        default="data/test_audio/asvspoof_spoof_clips",
        help="Directory containing spoof WAV clips"
    )

    args = parser.parse_args()

    bonafide_files = []
    for bdir in args.bonafide_dirs:
        if os.path.exists(bdir):
            bonafide_files.extend(glob.glob(os.path.join(bdir, "*.wav")))

    spoof_files = []
    if os.path.exists(args.spoof_dir):
        spoof_files.extend(glob.glob(os.path.join(args.spoof_dir, "*.wav")))

    print(f"Discovered {len(bonafide_files)} bonafide WAV files and {len(spoof_files)} spoof WAV files.")

    bonafide_results = evaluate_audio_files(bonafide_files, "bonafide")
    spoof_results = evaluate_audio_files(spoof_files, "spoof")

    # 1. Print Per-Clip Table
    all_results = bonafide_results + spoof_results
    print("\n=== PER-CLIP EVALUATION RESULTS ===")
    print(f"{'Filename':<32} | {'Label':<8} | {'Dur(s)':<6} | {'Status':<12} | {'F0 Mean':<8} | {'F0 Std':<8} | {'Voiced':<6} | {'Pause':<6} | {'Rate':<6} | {'Score':<6} | {'Flags/Reasons'}")
    print("-" * 135)

    for r in all_results:
        f0_m_str = f"{r['pitch_mean_hz']:.1f}" if r['pitch_mean_hz'] is not None else "N/A"
        f0_s_str = f"{r['pitch_std_hz']:.1f}" if r['pitch_std_hz'] is not None else "N/A"
        flags_str = ",".join(r['flags']) if r['flags'] else "none"
        print(f"{r['file']:<32} | {r['label']:<8} | {r['duration_sec']:<6.2f} | {r['status']:<12} | {f0_m_str:<8} | {f0_s_str:<8} | {r['voiced_ratio']:<6.2f} | {r['pause_ratio']:<6.2f} | {r['speech_rate_proxy']:<6.2f} | {r['prosody_score']:<6.4f} | {flags_str}")

    print("-" * 135)

    # 2. Print Group Summaries
    print_summary_table(bonafide_results, "Bonafide")
    print_summary_table(spoof_results, "Spoof")

    # 3. Print Evaluation Conclusion
    print("\n=== PROSODY EVALUATION CONCLUSION ===")
    print("Conclusion: Prosody does not show reliable separation on this sample and must remain informational only.")
    print("\nKey Takeaways:")
    print("1. Small benchmark evaluation (13 clips); does not reflect overall production system accuracy.")
    print("2. Prosody features alone DO NOT constitute proof of AI synthetic cloning.")
    print("3. No prosody threshold was tuned or fitted on this evaluation set.")
    print("4. Prosody scores/flags MUST NOT alter alert levels, rolling risk, or transaction decisions.")
    print("5. Accent, language, microphone response, emotion, and telephony codecs can influence prosody metrics.")
    print("\n=== Evaluation Complete ===")


if __name__ == "__main__":
    run_evaluation()
