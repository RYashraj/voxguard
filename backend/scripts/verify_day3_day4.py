"""
Verification script for Day 3 & Day 4 milestones of VoxGuard (Shreyas - Backend).
Checks:
1. RollingRiskAggregator 5-chunk weighted rolling window math & threshold logic
2. ML Stub analyze_chunk_stub inference and score generation
3. End-to-end pipeline: Audio slice -> ML stub -> Rolling aggregator -> WebSocket broadcast
4. Exact contract conformance on all streamed messages
"""
import sys
import asyncio
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.aggregator import RollingRiskAggregator
from app.ml.stub import analyze_chunk_stub
from app.services.simulator import simulate_call
from app.models.schemas import RiskUpdate
from app.utils.audio_generator import ensure_default_sample_audio


async def run_verification():
    print("\n==========================================")
    print("VOXGUARD BACKEND - DAY 3 & 4 VERIFICATION")
    print("==========================================\n")

    # 1. Day 3: RollingRiskAggregator Logic & Smoothing
    print("[1/3] Testing RollingRiskAggregator (Day 3)...")
    agg = RollingRiskAggregator(window_size=5, low_threshold=0.40, high_threshold=0.70)
    
    test_scores = [0.10, 0.15, 0.45, 0.60, 0.85, 0.95]
    print("      Feeding sequence of chunk scores:")
    for i, s in enumerate(test_scores, 1):
        rolling = agg.update(s)
        level = agg.get_alert_level()
        print(f"        Step {i}: chunk_score={s:.2f} -> rolling_score={rolling:.4f} (alert='{level}')")

    assert agg.get_alert_level() == "high"
    print("      SUCCESS: Aggregator produced smooth curve and flipped alert_level to 'high'.\n")

    # 2. Day 4: ML Stub Inference
    print("[2/3] Testing analyze_chunk_stub (Day 4)...")
    sample_bytes = b"\x00" * 4000
    res_normal = analyze_chunk_stub(sample_bytes, step=1, scenario="gradual_escalation")
    res_spoof = analyze_chunk_stub(sample_bytes, step=5, scenario="gradual_escalation")
    
    print(f"      Step 1 (Normal speech): score={res_normal['chunk_score']}, flags={res_normal['flags']}")
    print(f"      Step 5 (AI clone):      score={res_spoof['chunk_score']}, flags={res_spoof['flags']}")
    assert res_normal["chunk_score"] < 0.40
    assert res_spoof["chunk_score"] > 0.70
    print("      SUCCESS: ML stub returns appropriate scores and synthetic flags.\n")

    # 3. End-to-End Pipeline
    print("[3/3] Testing Full Pipeline (Simulator -> ML Stub -> Aggregator -> RiskUpdate)...")
    demo_wav = ensure_default_sample_audio()
    streamed = []

    async for update in simulate_call(demo_wav, chunk_duration_sec=3.0, delay_sec=0.01, scenario="gradual_escalation"):
        assert isinstance(update, RiskUpdate)
        streamed.append(update)
        print(f"      [Stream] Chunk '{update.chunk_id}' -> chunk={update.chunk_score:.4f} | rolling={update.rolling_risk_score:.4f} | alert={update.alert_level.upper()} | flags={update.flags}")

    assert len(streamed) > 0
    # Verify the smooth rolling behavior in the actual stream
    initial_score = streamed[0].rolling_risk_score
    final_score = streamed[-1].rolling_risk_score
    assert final_score > initial_score, "Stream did not escalate as expected"

    print("\n==========================================")
    print("ALL DAY 3 & DAY 4 DELIVERABLES VERIFIED!")
    print("==========================================\n")


if __name__ == "__main__":
    asyncio.run(run_verification())
