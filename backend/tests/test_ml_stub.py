import pytest
from app.ml.stub import analyze_chunk_stub, MLStubSession


def test_analyze_chunk_stub_contract():
    """Verify ML stub returns all required fields within valid ranges."""
    dummy_audio = b"\x00" * 1000
    result = analyze_chunk_stub(dummy_audio, step=1, scenario="gradual_escalation")

    assert "chunk_score" in result
    assert "confidence" in result
    assert "flags" in result
    assert 0.0 <= result["chunk_score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["flags"], list)


def test_ml_stub_scenarios():
    """Verify different demo scenarios behave properly."""
    dummy_audio = b"\x00" * 1000

    # Clean scenario
    clean_res = analyze_chunk_stub(dummy_audio, step=5, scenario="clean")
    assert clean_res["chunk_score"] < 0.35
    assert len(clean_res["flags"]) == 0

    # Suspicious scenario
    susp_res = analyze_chunk_stub(dummy_audio, step=1, scenario="suspicious")
    assert susp_res["chunk_score"] > 0.70
    assert "synthetic_artifact" in susp_res["flags"]


def test_ml_stub_session_progression():
    """Verify MLStubSession automatically increments step counter and escalates risk."""
    session = MLStubSession(scenario="gradual_escalation")
    dummy_audio = b"\x00" * 1000

    res_step1 = session.analyze_chunk(dummy_audio)
    assert res_step1["chunk_score"] < 0.35

    res_step2 = session.analyze_chunk(dummy_audio)
    res_step3 = session.analyze_chunk(dummy_audio)
    res_step4 = session.analyze_chunk(dummy_audio)
    res_step5 = session.analyze_chunk(dummy_audio)
    res_step6 = session.analyze_chunk(dummy_audio)

    # Step 6 should be in high-risk zone
    assert res_step6["chunk_score"] >= 0.75
    assert "synthetic_artifact" in res_step6["flags"]
