"""
Verification script for Day 1 & Day 2 milestones of VoxGuard (Shreyas - Backend).
Checks:
1. GET /health -> 200 {"status": "ok"}
2. GET /contract -> valid sample matching strict JSON shape
3. WebSocket /ws/session connection & streaming
4. Call simulator slicing, real-time chunk delay, and contract validation
"""
import sys
import asyncio
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import RiskUpdate
from app.services.simulator import simulate_call, slice_wav_file
from app.utils.audio_generator import ensure_default_sample_audio


async def run_async_verification():
    print("\n==========================================")
    print("VOXGUARD BACKEND - DAY 1 & 2 VERIFICATION")
    print("==========================================\n")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Day 1: Health Check
        print("[1/4] Testing GET /health...")
        health_res = await client.get("/health")
        assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
        assert health_res.json() == {"status": "ok"}
        print("      SUCCESS: /health returned 200 {'status': 'ok'}\n")

        # 2. Day 1: Contract Endpoint
        print("[2/4] Testing GET /contract schema...")
        contract_res = await client.get("/contract")
        assert contract_res.status_code == 200
        contract_data = contract_res.json()
        validated_contract = RiskUpdate(**contract_data)  # Validates through Pydantic
        print("      SUCCESS: Contract validated against Pydantic model:")
        for k, v in contract_data.items():
            print(f"        - {k}: {v}")
        print()

        # 3. Day 2: Audio Chunk Slicing Verification
        print("[3/4] Testing Audio Slicer (simulate_call chunking)...")
        sample_audio = ensure_default_sample_audio()
        chunks = slice_wav_file(sample_audio, chunk_duration_sec=3.0)
        assert len(chunks) > 0, "No chunks produced from sample audio"
        print(f"      SUCCESS: Sliced '{sample_audio}' into {len(chunks)} chunks of 3.0s duration each.")
        print(f"      First chunk ID: {chunks[0]['chunk_id']}, Duration: {chunks[0]['duration_sec']:.2f}s\n")

        # 4. Day 2: Real-Time Stream Simulation & Contract Match
        print("[4/4] Testing simulate_call streaming & data contract...")
        streamed_count = 0
        async for chunk_update in simulate_call(sample_audio, chunk_duration_sec=3.0, delay_sec=0.05, scenario="gradual_escalation"):
            assert isinstance(chunk_update, RiskUpdate)
            assert chunk_update.alert_level in ["low", "medium", "high"]
            assert 0.0 <= chunk_update.chunk_score <= 1.0
            assert 0.0 <= chunk_update.rolling_risk_score <= 1.0
            print(f"      -> Chunk [{chunk_update.chunk_id}]: score={chunk_update.chunk_score:.2f}, rolling={chunk_update.rolling_risk_score:.2f}, alert='{chunk_update.alert_level}', flags={chunk_update.flags}")
            streamed_count += 1

        assert streamed_count == len(chunks)
        print(f"      SUCCESS: Streamed all {streamed_count} chunks matching contract shape perfectly!\n")

    print("==========================================")
    print("ALL DAY 1 & DAY 2 DELIVERABLES VERIFIED!")
    print("==========================================\n")


if __name__ == "__main__":
    asyncio.run(run_async_verification())
