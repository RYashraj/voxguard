"""
Offline Model Benchmarking Utility for Hetvi & Nandini (ML Team).
Tests your analyze_chunk() function against all pre-sliced sample chunks,
validates return schema, and measures per-chunk inference latency.
"""
import sys
import time
from pathlib import Path

# Add ML directory and Backend directory to path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent.parent / "backend"

sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(backend_dir))

# Try importing from backend app first, or local sample template
try:
    from app.ml.ml_model import analyze_chunk
    print("Loaded ML model from: backend/app/ml/ml_model.py")
except ImportError:
    from sample_inference_template import analyze_chunk
    print("Loaded template from: sample_inference_template.py")


def run_benchmark():
    chunks_dir = current_dir / "sample_chunks"
    wav_files = sorted(list(chunks_dir.glob("*.wav")))

    if not wav_files:
        print(f"Error: No .wav files found in {chunks_dir}")
        return

    print("\n" + "=" * 65)
    print("       VOXGUARD ML MODEL OFFLINE BENCHMARK & TESTER")
    print("=" * 65 + "\n")
    print(f"Testing {len(wav_files)} audio chunks against analyze_chunk()...\n")

    latencies = []
    results = []

    for idx, wav_file in enumerate(wav_files, 1):
        raw_bytes = wav_file.read_bytes()
        file_size_kb = len(raw_bytes) / 1024.0

        t0 = time.perf_counter()
        result = analyze_chunk(raw_bytes)
        t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)
        results.append((wav_file.name, result, latency_ms))

        # Schema Validation
        assert isinstance(result, dict), f"Result must be a dict, got {type(result)}"
        assert "chunk_score" in result, "Missing 'chunk_score' key in output dict"
        assert "confidence" in result, "Missing 'confidence' key in output dict"
        assert "flags" in result, "Missing 'flags' key in output dict"
        assert 0.0 <= result["chunk_score"] <= 1.0, f"chunk_score {result['chunk_score']} out of [0.0, 1.0]"
        assert 0.0 <= result["confidence"] <= 1.0, f"confidence {result['confidence']} out of [0.0, 1.0]"
        assert isinstance(result["flags"], list), f"flags must be a list, got {type(result['flags'])}"

        score_bar = "#" * int(result["chunk_score"] * 20)
        print(f"[{idx}/{len(wav_files)}] {wav_file.name} ({file_size_kb:.1f} KB):")
        print(f"      Score:      {result['chunk_score']:.4f}  [{score_bar:<20}]")
        print(f"      Confidence: {result['confidence']:.4f}")
        print(f"      Flags:      {result['flags']}")
        print(f"      Latency:    {latency_ms:.2f} ms\n")

    # Summary Statistics
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    print("-" * 65)
    print("                      BENCHMARK SUMMARY")
    print("-" * 65)
    print(f"  * Total Chunks Processed:  {len(wav_files)}")
    print(f"  * Average Inference Time:  {avg_latency:.2f} ms")
    print(f"  * Min Latency (Warm):      {min_latency:.2f} ms")
    print(f"  * Max Latency (Cold Start):{max_latency:.2f} ms")
    print(f"  * Target Requirement:      < 1000.00 ms per 3-sec chunk")
    if avg_latency < 1000.0:
        print("  * Performance Status:      PASS (Meets Real-Time Streaming Goal)")
    else:
        print("  * Performance Status:      WARNING (Consider GPU or ONNX export)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_benchmark()
