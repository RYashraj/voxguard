import pytest
from app.core.aggregator import RollingRiskAggregator
from app.models.schemas import RiskUpdate


def test_aggregator_initial_state():
    """Verify aggregator initializes cleanly with 0.0 score and low alert."""
    agg = RollingRiskAggregator(window_size=5)
    assert agg.get_rolling_score() == 0.0
    assert agg.get_alert_level() == "low"
    assert agg.total_chunks_processed == 0


def test_score_rising_smoothly_across_increasing_scores():
    """
    Day 3 Prompt requirement:
    Include unit tests showing the score rising smoothly across a sequence of increasingly high chunk scores.
    """
    agg = RollingRiskAggregator(window_size=5)
    
    # Increasing chunk scores simulating call getting riskier
    chunk_scores = [0.10, 0.20, 0.40, 0.60, 0.80, 0.90, 0.95]
    rolling_scores = []
    alert_levels = []

    for score in chunk_scores:
        rolling = agg.update(score)
        rolling_scores.append(rolling)
        alert_levels.append(agg.get_alert_level())

    # Verify monotonic smooth rise
    for i in range(len(rolling_scores) - 1):
        assert rolling_scores[i] < rolling_scores[i + 1], f"Score at index {i} did not rise smoothly"

    # Verify alert levels transitioned properly from low -> medium -> high
    assert alert_levels[0] == "low"     # score ~0.10
    assert alert_levels[1] == "low"     # (1*0.10 + 2*0.20)/3 = 0.1667 < 0.4
    assert "medium" in alert_levels     # enters medium around chunks 3-4
    assert alert_levels[-1] == "high"   # enters high (> 0.7) for sustained 0.90+ scores


def test_weighted_average_calculation():
    """Verify exact weighted rolling average math."""
    agg = RollingRiskAggregator(window_size=5)

    # 1 item: weight [1]
    agg.update(0.20)
    assert pytest.approx(agg.get_rolling_score(), 0.0001) == 0.20

    # 2 items: weights [1, 2], sum=3 -> (1*0.2 + 2*0.5)/3 = 1.2/3 = 0.40
    agg.update(0.50)
    assert pytest.approx(agg.get_rolling_score(), 0.0001) == 0.40

    # Reset and test 5 items: [0.1, 0.1, 0.1, 0.1, 0.1]
    agg.reset()
    for _ in range(5):
        agg.update(0.10)
    assert pytest.approx(agg.get_rolling_score(), 0.0001) == 0.10


def test_noise_smoothing_single_spike():
    """
    Verify single random chunk spike does NOT trigger false high alert.
    (Demonstrates why rolling aggregation is critical for audio stream detection).
    """
    agg = RollingRiskAggregator(window_size=5)

    # 4 clean chunks
    agg.update(0.10)
    agg.update(0.10)
    agg.update(0.10)
    agg.update(0.10)

    # 1 brief anomalous spike (e.g. mic bump or transient artifact)
    agg.update(0.85)

    # Weights [1, 2, 3, 4, 5], sum=15
    # (1*0.1 + 2*0.1 + 3*0.1 + 4*0.1 + 5*0.85)/15 = (1.0 + 4.25)/15 = 5.25/15 = 0.35
    assert agg.get_rolling_score() < 0.40
    assert agg.get_alert_level() == "low"  # Successfully filtered transient noise!


def test_threshold_boundaries():
    """Verify exact alert level threshold transitions."""
    agg = RollingRiskAggregator(window_size=5, low_threshold=0.40, high_threshold=0.70)

    # Score below 0.40 -> low
    agg.update(0.39)
    assert agg.get_alert_level() == "low"

    # Score at 0.40 -> medium
    agg.reset()
    agg.update(0.40)
    assert agg.get_alert_level() == "medium"

    # Score at 0.70 -> medium
    agg.reset()
    agg.update(0.70)
    assert agg.get_alert_level() == "medium"

    # Score > 0.70 -> high
    agg.reset()
    agg.update(0.71)
    assert agg.get_alert_level() == "high"


def test_create_risk_update_helper():
    """Verify create_risk_update produces contract-compliant RiskUpdate instances."""
    agg = RollingRiskAggregator(window_size=5)
    update = agg.create_risk_update(
        chunk_id="chunk_042",
        chunk_score=0.88,
        confidence=0.96,
        flags=["synthetic_artifact"]
    )
    assert isinstance(update, RiskUpdate)
    assert update.chunk_id == "chunk_042"
    assert update.chunk_score == 0.88
    assert update.rolling_risk_score == 0.88
    assert update.alert_level == "high"
    assert update.flags == ["synthetic_artifact"]
