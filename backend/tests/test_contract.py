import pytest
from pydantic import ValidationError
from app.models.schemas import RiskUpdate


def test_risk_update_valid_contract():
    """Verify valid RiskUpdate instances conform strictly to contract."""
    update = RiskUpdate(
        chunk_id="chunk_001",
        timestamp="2026-09-10T15:00:00Z",
        chunk_score=0.25,
        rolling_risk_score=0.20,
        confidence=0.95,
        flags=["synthetic_artifact"],
        alert_level="low"
    )
    data = update.model_dump()
    assert data["chunk_id"] == "chunk_001"
    assert data["chunk_score"] == 0.25
    assert data["rolling_risk_score"] == 0.20
    assert data["confidence"] == 0.95
    assert data["flags"] == ["synthetic_artifact"]
    assert data["alert_level"] == "low"


def test_risk_update_invalid_alert_level():
    """Verify invalid alert_level is rejected with ValidationError."""
    with pytest.raises(ValidationError):
        RiskUpdate(
            chunk_id="chunk_001",
            timestamp="2026-09-10T15:00:00Z",
            chunk_score=0.5,
            rolling_risk_score=0.5,
            confidence=0.9,
            flags=[],
            alert_level="critical"  # Invalid: only low, medium, high allowed
        )


def test_risk_update_score_bounds():
    """Verify scores outside 0.0 to 1.0 are rejected."""
    with pytest.raises(ValidationError):
        RiskUpdate(
            chunk_id="chunk_001",
            timestamp="2026-09-10T15:00:00Z",
            chunk_score=1.5,  # Invalid: must be <= 1.0
            rolling_risk_score=0.5,
            confidence=0.9,
            flags=[],
            alert_level="high"
        )
