"""
VoxGuard Speaker Verification & Identity Drift Smoke Test

Prerequisites:
1. SpeechBrain package must be installed (`pip install speechbrain`).
2. Two explicitly consented local WAV files must be provided as CLI arguments:
   - Argument 1: Path to consented reference speaker WAV file
   - Argument 2: Path to comparison speaker WAV file (same speaker or different speaker)

DISCLAIMER:
Do not download model weights or process a real person's voice without explicit user direction and consent.
"""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_smoke_test():
    print("=== VoxGuard Speaker Verification Smoke Test ===\n")

    # 1. Check SpeechBrain dependency
    try:
        import speechbrain
        print(f"[OK] SpeechBrain library detected (v{speechbrain.__version__}).")
    except ImportError:
        print("[PREREQUISITE NOTICE] SpeechBrain library is NOT installed.")
        print("To run this live speaker verification smoke test, install speechbrain:")
        print("  pip install speechbrain")
        print("\nSmoke test stopped safely (no missing dependencies forced).")
        sys.exit(0)

    # 2. Check CLI arguments for consented audio files
    if len(sys.argv) < 3:
        print("[PREREQUISITE NOTICE] Two consented local WAV files are required.")
        print("Usage:")
        print("  python scripts/smoke_test_speaker_verification.py <consented_reference.wav> <comparison.wav>")
        print("\nSmoke test stopped safely.")
        sys.exit(0)

    ref_path = sys.argv[1]
    comp_path = sys.argv[2]

    if not os.path.exists(ref_path):
        print(f"ERROR: Consented reference WAV file not found at: {ref_path}")
        sys.exit(1)

    if not os.path.exists(comp_path):
        print(f"ERROR: Comparison WAV file not found at: {comp_path}")
        sys.exit(1)

    from app.ml.speaker_verification import SessionIdentityTracker

    print(f"Consented Reference Audio: {ref_path}")
    print(f"Comparison Audio:          {comp_path}\n")

    tracker = SessionIdentityTracker(session_id="smoke_test_session")

    # Enroll reference
    print("1. Enrolling reference voice...")
    with open(ref_path, "rb") as f:
        ref_bytes = f.read()

    enroll_res = tracker.enroll_reference(ref_bytes)
    print(f"   Enrollment Result: {enroll_res}")

    if enroll_res.get("status") != "ok":
        print("ERROR: Reference enrollment failed. Exiting.")
        sys.exit(1)

    # Verify comparison audio
    print("2. Verifying comparison audio...")
    with open(comp_path, "rb") as f:
        comp_bytes = f.read()

    verify_res = tracker.verify_chunk(comp_bytes)
    print(f"\n--- Identity Verification Result ---")
    print(f"  Status:             {verify_res['status']}")
    print(f"  Speaker Similarity: {verify_res['speaker_similarity']:.4f}")
    print(f"  Identity Drift:     {verify_res['identity_drift']:.4f}")
    print(f"  Confidence:         {verify_res['confidence']:.4f}")
    print(f"  Flags:              {verify_res['flags']}")

    # Wipe in-memory embedding
    tracker.clear()
    print("\n[OK] In-memory reference embedding wiped successfully.")
    print("=== Speaker Verification Smoke Test Completed ===")


if __name__ == "__main__":
    run_smoke_test()
