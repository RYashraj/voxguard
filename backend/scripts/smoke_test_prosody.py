"""
VoxGuard Direct Prosody Analysis Smoke Test

Runs prosody feature extraction and anomaly assessment on project audio files.
"""

import os
import sys
import wave

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.prosody import extract_prosody_features, assess_prosody
from app.services.simulator import slice_wav_file
from app.utils.audio_generator import ensure_default_sample_audio


def run_smoke_test():
    audio_path = os.path.join("data", "sample_calls", "demo_call.wav")
    if not os.path.exists(audio_path):
        audio_path = ensure_default_sample_audio()

    print(f"=== VoxGuard Prosody Analysis Smoke Test ===")
    print(f"Target audio file: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found at {audio_path}")
        sys.exit(1)

    chunks = slice_wav_file(audio_path, chunk_duration_sec=3.0)
    print(f"Sliced audio into {len(chunks)} chunks of ~3.0s each.\n")

    for i, chunk in enumerate(chunks):
        audio_bytes = chunk["audio_bytes"]
        chunk_id = chunk["chunk_id"]

        features = extract_prosody_features(audio_bytes)
        evaluation = assess_prosody(features)

        print(f"--- Chunk {i+1} ({chunk_id}, duration={chunk['duration_sec']:.2f}s) ---")
        print(f"  Status:               {features['status']}")
        print(f"  RMS Energy:           {features['rms_energy']:.4f}")
        print(f"  Pitch Mean (F0):      {features['pitch_mean_hz']} Hz")
        print(f"  Pitch Std (F0):       {features['pitch_std_hz']} Hz")
        print(f"  Voiced Ratio:         {features['voiced_ratio']:.4f}")
        print(f"  Pause Count:          {features['pause_count']}")
        print(f"  Pause Duration Ratio: {features['pause_duration_ratio']:.4f}")
        print(f"  Speech Rate Proxy:    {features['speech_rate_proxy']} voiced-bursts/sec")
        print(f"  Prosody Score:        {evaluation['prosody_score']:.4f}")
        print(f"  Confidence:           {evaluation['confidence']:.4f}")
        print(f"  Flags:                {evaluation['flags']}")
        print(f"  Reason Codes:         {evaluation['reason_codes']}\n")

    print("=== Prosody Smoke Test Completed Successfully ===")


if __name__ == "__main__":
    run_smoke_test()
