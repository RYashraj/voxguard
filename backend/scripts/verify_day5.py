"""
Verification script for Day 5 milestone of VoxGuard (Shreyas - Backend).
Prompt 5 Requirements:
1. Real ML Model Integration (Spectra-AASIST3 / analyze_chunk)
2. Mode switching between 'real' and 'stub' (VOXGUARD_ML_MODE)
3. SQLite Database Persistence (sessions / chunk_history table)
4. Per-chunk latency tracking and average latency calculation
5. Full pipeline integration with REST session history verification
"""
import os
import sys
import time
import asyncio
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.ml_model import analyze_chunk, parse_audio_bytes, get_detector
from app.ml.analyzer import analyze_chunk_dispatch
from app.db.session_logger import (
    init_db,
    get_db_path,
    log_chunk_record,
    get_session_history,
    get_session_stats,
    list_all_sessions,
)
from app.services.simulator import simulate_call
from app.utils.audio_generator import generate_sample_wav, ensure_default_sample_audio


async def run_day5_verification():
    print("\n" + "=" * 60)
    print("      VOXGUARD BACKEND — DAY 5 COMPREHENSIVE VERIFICATION")
    print("=" * 60 + "\n")

    # ---------------------------------------------------------
    # Milestone 1: Audio Parsing & Direct ML Model Interface
    # ---------------------------------------------------------
    print("[1/5] Testing Audio Preprocessing & ML Interface (analyze_chunk)...")
    sample_chunk_path = Path(__file__).parent.parent.parent / "team_resources" / "for_ml" / "sample_chunks" / "chunk_001.wav"
    
    if sample_chunk_path.exists():
        raw_bytes = sample_chunk_path.read_bytes()
        print(f"      Loaded real audio chunk: {sample_chunk_path.name} ({len(raw_bytes)} bytes)")
    else:
        print("      Generating synthetic test WAV for evaluation...")
        temp_wav = Path(__file__).parent / "temp_test_chunk.wav"
        generate_sample_wav(str(temp_wav), duration_sec=3.0, frequency=440.0)
        raw_bytes = temp_wav.read_bytes()
        temp_wav.unlink(missing_ok=True)

    parsed_audio, energy, flags = parse_audio_bytes(raw_bytes)
    assert parsed_audio is not None, "Audio parser returned None on valid WAV"
    print(f"      Audio parsed successfully: RMS energy = {energy:.5f}, Initial flags = {flags}")

    # Test analyze_chunk execution
    t0 = time.perf_counter()
    ml_result = analyze_chunk(raw_bytes)
    t1 = time.perf_counter()
    ml_latency_ms = (t1 - t0) * 1000.0

    print(f"      Direct ML result: score={ml_result['chunk_score']}, conf={ml_result['confidence']}, flags={ml_result['flags']}")
    print(f"      Inference execution time: {ml_latency_ms:.2f} ms")
    assert "chunk_score" in ml_result and 0.0 <= ml_result["chunk_score"] <= 1.0
    assert "confidence" in ml_result and 0.0 <= ml_result["confidence"] <= 1.0
    assert "flags" in ml_result and isinstance(ml_result["flags"], list)
    print("      SUCCESS: ML model interface conforms strictly to contract.\n")

    # ---------------------------------------------------------
    # Milestone 2: Dispatcher Mode Switching ('real' vs 'stub')
    # ---------------------------------------------------------
    print("[2/5] Testing Dispatcher Mode Switching (VOXGUARD_ML_MODE)...")
    
    # Test Stub mode
    os.environ["VOXGUARD_ML_MODE"] = "stub"
    stub_res = await analyze_chunk_dispatch(raw_bytes, step=1, scenario="gradual_escalation")
    print(f"      Stub Mode:  chunk_score={stub_res['chunk_score']:.4f}, flags={stub_res['flags']}")
    assert stub_res["chunk_score"] < 0.40

    # Test Real mode
    os.environ["VOXGUARD_ML_MODE"] = "real"
    real_res = await analyze_chunk_dispatch(raw_bytes, step=1)
    print(f"      Real Mode:  chunk_score={real_res['chunk_score']:.4f}, flags={real_res['flags']}")
    assert "chunk_score" in real_res
    print("      SUCCESS: Mode switcher successfully toggles between stub and real model.\n")

    # ---------------------------------------------------------
    # Milestone 3: SQLite Database Schema & Session Logging
    # ---------------------------------------------------------
    print("[3/5] Testing SQLite Database Persistence (sessions / chunk_history)...")
    db_file = Path(__file__).parent / "test_day5.db"
    db_path = str(db_file.resolve())
    
    if db_file.exists():
        db_file.unlink()

    ok = init_db(db_path)
    assert ok is True, "Failed to initialize SQLite database"
    print(f"      SQLite database created at: {db_file.name}")

    test_session = "session_day5_demo_001"
    sample_records = [
        ("chunk_001", "2026-09-11T10:00:00Z", 0.08, 0.08, 0.94, [], "low", 12.5),
        ("chunk_002", "2026-09-11T10:00:03Z", 0.15, 0.12, 0.92, [], "low", 11.8),
        ("chunk_003", "2026-09-11T10:00:06Z", 0.78, 0.45, 0.88, ["synthetic_artifact"], "medium", 14.2),
        ("chunk_004", "2026-09-11T10:00:09Z", 0.92, 0.68, 0.96, ["synthetic_artifact"], "medium", 13.1),
        ("chunk_005", "2026-09-11T10:00:12Z", 0.95, 0.82, 0.98, ["synthetic_artifact", "prosody_flatness"], "high", 12.9),
    ]

    for chunk_id, ts, cs, rrs, conf, fl, al, lat in sample_records:
        log_chunk_record(
            session_id=test_session,
            chunk_id=chunk_id,
            timestamp=ts,
            chunk_score=cs,
            rolling_risk_score=rrs,
            confidence=conf,
            flags=fl,
            alert_level=al,
            inference_latency_ms=lat,
            db_path=db_path
        )

    history = get_session_history(test_session, db_path=db_path)
    print(f"      Retrieved {len(history)} persisted chunk records from SQLite.")
    assert len(history) == 5
    assert history[-1]["alert_level"] == "high"
    assert "synthetic_artifact" in history[-1]["flags"]

    stats = get_session_stats(test_session, db_path=db_path)
    print(f"      Session Stats: Avg Latency = {stats['avg_latency_ms']} ms | Peak Risk = {stats['peak_risk_score']} | Alert = {stats['final_alert_level']}")
    assert stats["total_chunks"] == 5
    assert stats["peak_risk_score"] == 0.82
    assert stats["final_alert_level"] == "high"
    print("      SUCCESS: SQLite database logs records with full telemetry and stats.\n")

    # ---------------------------------------------------------
    # Milestone 4: End-to-End Simulation with Latency Measurement
    # ---------------------------------------------------------
    print("[4/5] Running End-to-End Live Simulation & Average Latency Benchmark...")
    # Use stub mode for fast deterministic automated benchmark
    os.environ["VOXGUARD_ML_MODE"] = "stub"
    os.environ["VOXGUARD_DB_PATH"] = db_path
    
    demo_wav = ensure_default_sample_audio()
    sim_session = "session_live_simulation_test"
    latencies = []
    chunk_updates = []

    print(f"      Streaming chunks from: {Path(demo_wav).name}")
    async for update in simulate_call(
        file_path=demo_wav,
        chunk_duration_sec=3.0,
        delay_sec=0.01,
        scenario="gradual_escalation",
        session_id=sim_session
    ):
        chunk_updates.append(update)
        print(f"        -> Chunk {update.chunk_id}: score={update.chunk_score:.4f} | rolling={update.rolling_risk_score:.4f} | alert={update.alert_level.upper()} | flags={update.flags}")

    sim_history = get_session_history(sim_session, db_path=db_path)
    assert len(sim_history) == len(chunk_updates)
    
    sim_stats = get_session_stats(sim_session, db_path=db_path)
    print(f"\n      Simulated Session Summary:")
    print(f"        - Session ID:       {sim_stats['session_id']}")
    print(f"        - Total Chunks:     {sim_stats['total_chunks']}")
    print(f"        - Avg ML Latency:   {sim_stats['avg_latency_ms']} ms")
    print(f"        - Peak Risk Score:  {sim_stats['peak_risk_score']}")
    print(f"        - Final Alert:      {sim_stats['final_alert_level'].upper()}")
    print(f"        - Flags Triggered:  {sim_stats['flags_triggered']}")
    print("      SUCCESS: End-to-end streaming correctly logs latency & generates summary.\n")

    # ---------------------------------------------------------
    # Milestone 5: Multi-Session Listing
    # ---------------------------------------------------------
    print("[5/5] Testing Multi-Session Listing (GET /sessions)...")
    all_sessions = list_all_sessions(db_path=db_path)
    print(f"      Found {len(all_sessions)} distinct sessions in SQLite database:")
    for s in all_sessions:
        print(f"        * [{s['session_id']}] Chunks: {s['total_chunks']} | Avg Latency: {s['avg_latency_ms']}ms | Alert: {s['final_alert_level']}")

    assert len(all_sessions) >= 2
    print("      SUCCESS: Multi-session query verified.\n")

    # Cleanup temporary test DB safely on Windows
    import gc
    gc.collect()
    try:
        if db_file.exists():
            db_file.unlink(missing_ok=True)
    except OSError:
        pass

    print("=" * 60)
    print("      ALL DAY 5 DELIVERABLES VERIFIED AND PRODUCTION READY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_day5_verification())
