import io
import wave
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_dummy_wav_bytes(duration_sec: float = 3.0, sample_rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        num_samples = int(duration_sec * sample_rate)
        # Low frequency dummy audio
        raw_data = bytes(num_samples * 2)
        wav.writeframes(raw_data)
    return buffer.getvalue()

def test_analyze_audio_endpoint_wav():
    wav_bytes = create_dummy_wav_bytes(3.0)
    files = {"file": ("test_mic_record.wav", wav_bytes, "audio/wav")}
    response = client.post("/api/analyze-audio", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "classification" in data
    assert data["classification"] in ["human", "ai_clone"]
    assert "verdict" in data
    assert "spoof_score" in data
    assert "confidence" in data
    assert "alert_level" in data
    assert "explanation" in data

def test_analyze_audio_endpoint_empty_file():
    files = {"file": ("empty.wav", b"", "audio/wav")}
    response = client.post("/api/analyze-audio", files=files)
    assert response.status_code == 400

from unittest.mock import AsyncMock, patch

def test_analyze_audio_classification_human():
    wav_bytes = create_dummy_wav_bytes(2.5)
    mock_res = {"chunk_score": 0.05, "confidence": 0.92, "flags": ["short_audio"]}
    with patch("app.main.analyze_chunk_dispatch", new=AsyncMock(return_value=mock_res)):
        files = {"file": ("mic_recording.wav", wav_bytes, "audio/wav")}
        response = client.post("/api/analyze-audio", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "human"
        assert data["alert_level"] == "low"
        assert "Genuine Human Voice" in data["verdict"]

def test_analyze_audio_classification_ai_clone():
    wav_bytes = create_dummy_wav_bytes(2.5)
    mock_res = {"chunk_score": 0.88, "confidence": 0.98, "flags": ["synthetic_artifact", "short_audio"]}
    with patch("app.main.analyze_chunk_dispatch", new=AsyncMock(return_value=mock_res)):
        files = {"file": ("mic_recording.wav", wav_bytes, "audio/wav")}
        response = client.post("/api/analyze-audio", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "ai_clone"
        assert data["alert_level"] == "high"
        assert "AI Voice Clone" in data["verdict"]

def test_analyze_audio_classification_hyper_realistic_clone():
    wav_bytes = create_dummy_wav_bytes(2.5)
    mock_res = {"chunk_score": 0.32, "confidence": 0.85, "flags": ["short_audio", "prosody_flatness"]}
    with patch("app.main.analyze_chunk_dispatch", new=AsyncMock(return_value=mock_res)):
        files = {"file": ("clone_sample.wav", wav_bytes, "audio/wav")}
        response = client.post("/api/analyze-audio", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["classification"] == "ai_clone"
        assert data["alert_level"] == "medium"
        assert "Suspected AI Voice Clone" in data["verdict"]

