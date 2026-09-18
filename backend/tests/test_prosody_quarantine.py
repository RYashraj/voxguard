"""
Regression Tests for VoxGuard Prosody Signal Quarantine

Verifies that unvalidated prosody-only heuristic labels are strictly quarantined
from public RiskUpdate outputs, WebSocket streams, and SQLite session history records.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.flag_filters import filter_public_flags, PROSODY_ONLY_FLAGS
from app.ml.analyzer import analyze_chunk_dispatch
from app.models.schemas import SimulationContext
from app.db.session_logger import get_session_history_async, init_db_async


def test_prosody_only_labels_filtered_from_public_output():
    """Requirement Test 2: All listed prosody-only labels are filtered from public output."""
    raw_flags = [
        "synthetic_artifact",
        "short_audio",
        "low_pitch_variation",
        "low_f0_variability",
        "prosody_flatness",
        "high_pause_ratio",
        "low_voiced_ratio",
        "insufficient_speech",
        "insufficient_voiced_speech",
        "prosody_unavailable",
        "prosody_anomaly",
        "model_unavailable",
    ]

    filtered = filter_public_flags(raw_flags)

    # Prosody flags must be stripped
    for prosody_flag in PROSODY_ONLY_FLAGS:
        assert prosody_flag not in filtered

    # Operational & acoustic flags must remain intact
    assert "synthetic_artifact" in filtered
    assert "short_audio" in filtered
    assert "model_unavailable" in filtered


def test_operational_and_error_flags_remain_intact():
    """Requirement Test 3: synthetic_artifact, short_audio, silent_audio, invalid_audio, model_unavailable, inference_error remain intact."""
    operational_flags = [
        "synthetic_artifact",
        "short_audio",
        "silent_audio",
        "invalid_audio",
        "model_unavailable",
        "inference_error",
    ]

    filtered = filter_public_flags(operational_flags)
    assert set(filtered) == set(operational_flags)


@pytest.mark.asyncio
async def test_low_risk_sample_does_not_expose_prosody_flatness_in_public_flags():
    """Requirement Test 1: Low-risk sample that internally produces prosody_flatness does not expose it in public WebSocket flags."""
    from app.ml.ml_model import SpectraAASISTDetector
    import numpy as np

    detector = SpectraAASISTDetector.__new__(SpectraAASISTDetector)
    detector.is_loaded = True
    detector._inference_lock = MagicMock()
    detector.model = MagicMock()

    # Mock low-risk bona-fide score
    mock_output = MagicMock()
    import torch
    mock_output.logits = torch.tensor([[-5.0, 5.0]])  # Low spoof prob ~0.006 (index 0 = spoof)
    detector.model.return_value = mock_output

    audio_samples = np.zeros(64600, dtype=np.float32)

    # Patch prosody module to return internal prosody_flatness flag
    with patch("app.ml.ml_model.extract_prosody_features", return_value={"status": "ok", "pitch_std_hz": 2.0}), \
         patch("app.ml.ml_model.assess_prosody", return_value={"flags": ["prosody_flatness"], "reason_codes": ["low_f0_variability"]}):
        res = detector.predict_parsed(audio_samples, rms_energy=0.1, flags=["short_audio"])

        assert res["chunk_score"] < 0.10
        assert "prosody_flatness" not in res["flags"]
        assert "short_audio" in res["flags"]


@pytest.mark.asyncio
async def test_sqlite_history_contains_filtered_flags_only():
    """Requirement Test 4: SQLite history records contain filtered flags only."""
    await init_db_async()

    test_session = "session_quarantine_sqlite_test"
    ctx = SimulationContext(
        caller_context="known_contact",
        transaction_type="other"
    )

    from app.services.simulator import simulate_call
    async for update in simulate_call(
        chunk_duration_sec=1.0,
        delay_sec=0.01,
        scenario="suspicious",
        session_id=test_session,
        context=ctx
    ):
        break

    history = await get_session_history_async(test_session)
    assert len(history) > 0

    for record in history:
        logged_flags = record["flags"]
        assert isinstance(logged_flags, list)
        for prosody_flag in PROSODY_ONLY_FLAGS:
            assert prosody_flag not in logged_flags
