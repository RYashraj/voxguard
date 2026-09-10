import pytest
import os
from app.utils.audio_generator import generate_sample_wav
from app.services.simulator import slice_wav_file, simulate_call


@pytest.fixture
def temp_wav_file(tmp_path):
    wav_path = tmp_path / "test_call.wav"
    generate_sample_wav(str(wav_path), duration_sec=6.0, frequency=300.0)
    return str(wav_path)


def test_slice_wav_file(temp_wav_file):
    """Verify slicing a 6-second WAV file into 3-second chunks produces 2 chunks."""
    chunks = slice_wav_file(temp_wav_file, chunk_duration_sec=3.0)
    assert len(chunks) == 2
    assert chunks[0]["chunk_id"] == "chunk_001"
    assert chunks[1]["chunk_id"] == "chunk_002"
    assert chunks[0]["duration_sec"] >= 2.9
    assert len(chunks[0]["audio_bytes"]) > 0


@pytest.mark.asyncio
async def test_simulate_call_stream(temp_wav_file):
    """Verify simulate_call yields RiskUpdate instances matching the contract."""
    collected_updates = []
    async for update in simulate_call(temp_wav_file, chunk_duration_sec=3.0, delay_sec=0.01, scenario="gradual_escalation"):
        collected_updates.append(update)

    assert len(collected_updates) == 2
    for item in collected_updates:
        assert item.chunk_id.startswith("chunk_")
        assert 0.0 <= item.chunk_score <= 1.0
        assert 0.0 <= item.rolling_risk_score <= 1.0
        assert item.alert_level in ["low", "medium", "high"]
