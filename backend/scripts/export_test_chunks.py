"""
Utility script for Hetvi & Nandini (ML Team).
Slices a full WAV recording into 3.0-second chunk WAV files
matching the exact audio format sent by the backend in real-time.
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.simulator import slice_wav_file
from app.utils.audio_generator import ensure_default_sample_audio


def export_chunks_for_ml(input_wav_path: str = None, output_dir: str = "data/ml_test_chunks", chunk_sec: float = 3.0):
    if not input_wav_path:
        input_wav_path = ensure_default_sample_audio()

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Slicing audio '{input_wav_path}' into {chunk_sec}s chunks...")
    chunks = slice_wav_file(input_wav_path, chunk_duration_sec=chunk_sec)

    saved_files = []
    for chunk in chunks:
        chunk_file = out_path / f"{chunk['chunk_id']}.wav"
        with open(chunk_file, "wb") as f:
            f.write(chunk["audio_bytes"])
        saved_files.append(str(chunk_file))
        print(f"  -> Exported: {chunk_file} ({chunk['duration_sec']:.2f}s, {len(chunk['audio_bytes'])} bytes)")

    print(f"\nSuccessfully generated {len(saved_files)} test chunks in '{output_dir}/'!")
    return saved_files


if __name__ == "__main__":
    wav_arg = sys.argv[1] if len(sys.argv) > 1 else None
    export_chunks_for_ml(wav_arg)
