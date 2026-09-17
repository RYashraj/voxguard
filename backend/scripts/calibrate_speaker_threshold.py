"""
VoxGuard Speaker Identity Drift Threshold Calibration Script

Helper tool to measure cosine similarity and identity drift across explicitly consented
same-speaker and different-speaker audio files, suggesting a calibrated threshold range.

Prerequisites:
1. SpeechBrain package must be installed (`pip install speechbrain`).
2. Explicitly consented WAV files separated into same-speaker and different-speaker directories:
   python scripts/calibrate_speaker_threshold.py --reference <ref.wav> --same-dir <same_speaker_dir> --diff-dir <diff_speaker_dir>

DISCLAIMER:
Do not download model weights or process a real person's voice without explicit user direction and consent.
"""

import os
import sys
import argparse

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_calibration():
    print("=== VoxGuard Speaker Verification Threshold Calibration Tool ===\n")

    parser = argparse.ArgumentParser(description="Calibrate identity drift threshold using consented speaker audio samples.")
    parser.add_argument("--reference", help="Path to consented reference speaker WAV file", default=None)
    parser.add_argument("--same-dir", help="Directory containing consented same-speaker comparison WAV files", default=None)
    parser.add_argument("--diff-dir", help="Directory containing consented different-speaker comparison WAV files", default=None)

    args = parser.parse_args()

    # 1. Check SpeechBrain dependency
    try:
        import speechbrain
        print(f"[OK] SpeechBrain library detected (v{speechbrain.__version__}).")
    except ImportError:
        print("[PREREQUISITE NOTICE] SpeechBrain library is NOT installed.")
        print("To run threshold calibration, install speechbrain:")
        print("  pip install speechbrain")
        print("\nCalibration tool stopped safely.")
        sys.exit(0)

    # 2. Check arguments
    if not args.reference or not args.same_dir or not args.diff_dir:
        print("[PREREQUISITE NOTICE] Consented reference audio and comparison directories required.")
        print("Usage:")
        print("  python scripts/calibrate_speaker_threshold.py --reference <ref.wav> --same-dir <same_dir> --diff-dir <diff_dir>")
        print("\nCalibration tool stopped safely.")
        sys.exit(0)

    if not os.path.exists(args.reference):
        print(f"ERROR: Reference file not found: {args.reference}")
        sys.exit(1)

    if not os.path.exists(args.same_dir):
        print(f"ERROR: Same-speaker directory not found: {args.same_dir}")
        sys.exit(1)

    if not os.path.exists(args.diff_dir):
        print(f"ERROR: Different-speaker directory not found: {args.diff_dir}")
        sys.exit(1)

    from app.ml.speaker_verification import SessionIdentityTracker
    import numpy as np

    tracker = SessionIdentityTracker(session_id="calibration_session")
    
    with open(args.reference, "rb") as f:
        ref_bytes = f.read()

    enroll_res = tracker.enroll_reference(ref_bytes)
    if enroll_res.get("status") != "ok":
        print(f"ERROR: Enrollment failed: {enroll_res}")
        sys.exit(1)

    same_files = [os.path.join(args.same_dir, f) for f in os.listdir(args.same_dir) if f.lower().endswith(".wav")]
    diff_files = [os.path.join(args.diff_dir, f) for f in os.listdir(args.diff_dir) if f.lower().endswith(".wav")]

    print(f"\nProcessing {len(same_files)} same-speaker files and {len(diff_files)} different-speaker files...\n")

    same_drifts = []
    same_sims = []
    for fpath in same_files:
        with open(fpath, "rb") as f:
            res = tracker.verify_chunk(f.read())
        if res.get("status") == "ok":
            same_sims.append(res["speaker_similarity"])
            same_drifts.append(res["identity_drift"])

    diff_drifts = []
    diff_sims = []
    for fpath in diff_files:
        with open(fpath, "rb") as f:
            res = tracker.verify_chunk(f.read())
        if res.get("status") == "ok":
            diff_sims.append(res["speaker_similarity"])
            diff_drifts.append(res["identity_drift"])

    tracker.clear()

    # Output Summary Table
    print("=== CALIBRATION RESULTS SUMMARY TABLE ===")
    print(f"{'Category':<20} | {'Count':<5} | {'Sim Mean (Std)':<16} | {'Drift Mean (Std)':<16} | {'Drift Range [Min, Max]'}")
    print("-" * 80)

    if same_drifts:
        s_sim_mean, s_sim_std = np.mean(same_sims), np.std(same_sims)
        s_dr_mean, s_dr_std = np.mean(same_drifts), np.std(same_drifts)
        print(f"{'Same-Speaker':<20} | {len(same_drifts):<5} | {s_sim_mean:.4f} ({s_sim_std:.4f})  | {s_dr_mean:.4f} ({s_dr_std:.4f})  | [{min(same_drifts):.4f}, {max(same_drifts):.4f}]")
    else:
        print(f"{'Same-Speaker':<20} | 0     | N/A              | N/A              | N/A")

    if diff_drifts:
        d_sim_mean, d_sim_std = np.mean(diff_sims), np.std(diff_sims)
        d_dr_mean, d_dr_std = np.mean(diff_drifts), np.std(diff_drifts)
        print(f"{'Different-Speaker':<20} | {len(diff_drifts):<5} | {d_sim_mean:.4f} ({d_sim_std:.4f})  | {d_dr_mean:.4f} ({d_dr_std:.4f})  | [{min(diff_drifts):.4f}, {max(diff_drifts):.4f}]")
    else:
        print(f"{'Different-Speaker':<20} | 0     | N/A              | N/A              | N/A")

    print("-" * 80)

    # Suggest Threshold Range
    if same_drifts and diff_drifts:
        max_same_drift = max(same_drifts)
        min_diff_drift = min(diff_drifts)

        if min_diff_drift > max_same_drift:
            print(f"\n[SUGGESTED THRESHOLD RANGE]: {max_same_drift + 0.02:.4f} to {min_diff_drift - 0.02:.4f}")
            print(f"Optimal Midpoint Threshold: {(max_same_drift + min_diff_drift) / 2.0:.4f}")
        else:
            print(f"\n[WARNING]: Overlap detected between same-speaker max drift ({max_same_drift:.4f}) and different-speaker min drift ({min_diff_drift:.4f}).")
            print("Consider collecting longer voiced enrollment samples or filtering low-SNR audio.")
    
    print("\n=== Calibration Analysis Complete ===")


if __name__ == "__main__":
    run_calibration()
