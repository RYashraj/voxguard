from typing import List, Literal, Optional, Deque
from collections import deque
from datetime import datetime, timezone

from app.models.schemas import RiskUpdate


class RollingRiskAggregator:
    """
    Day 3 Requirement: RollingRiskAggregator
    - Maintains a weighted rolling average over the last N chunks (default 5, recent chunks weighted higher).
    - Exposes update(score: float), get_rolling_score() -> float, get_alert_level() -> "low" | "medium" | "high".
    - Smooths out per-chunk noise while allowing rapid escalation if multiple consecutive risky chunks occur.
    """
    def __init__(self, window_size: int = 5, low_threshold: float = 0.4, high_threshold: float = 0.7):
        self.window_size = window_size
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.scores: Deque[float] = deque(maxlen=window_size)
        self.flag_history: Deque[List[str]] = deque(maxlen=window_size)
        self.current_rolling_score: float = 0.0
        self.current_alert_level: Literal["low", "medium", "high"] = "low"
        self.total_chunks_processed: int = 0

    def update(self, chunk_score: float, flags: Optional[List[str]] = None) -> float:
        """
        Updates the aggregator with a new chunk_score.
        Appends to rolling window, computes weighted rolling average, and updates alert level.
        Returns the computed rolling risk score.
        """
        # Clamp chunk_score to [0.0, 1.0]
        clamped_score = max(0.0, min(1.0, float(chunk_score)))
        self.scores.append(clamped_score)
        self.flag_history.append(flags or [])
        self.total_chunks_processed += 1

        # Calculate linearly weighted average over available window items
        # Weights: for k items, weights are 1, 2, ..., k (recent chunks weighted highest)
        n = len(self.scores)
        weights = list(range(1, n + 1))  # e.g., for 5 items: [1, 2, 3, 4, 5], sum=15
        total_weight = sum(weights)
        
        weighted_sum = sum(w * s for w, s in zip(weights, self.scores))
        self.current_rolling_score = round(weighted_sum / total_weight, 4)

        # Update alert level based on strict thresholds
        if self.current_rolling_score < self.low_threshold:
            self.current_alert_level = "low"
        elif self.current_rolling_score <= self.high_threshold:
            self.current_alert_level = "medium"
        else:
            self.current_alert_level = "high"

        return self.current_rolling_score

    def get_rolling_score(self) -> float:
        """Returns the current smoothed rolling risk score (0.0 to 1.0)."""
        return self.current_rolling_score

    def get_alert_level(self) -> Literal["low", "medium", "high"]:
        """
        Returns the current threat alert level:
        - "low" for score < 0.4
        - "medium" for 0.4 <= score <= 0.7
        - "high" for score > 0.7
        """
        return self.current_alert_level

    def get_active_flags(self) -> List[str]:
        """Returns unique flags observed in the recent rolling window."""
        seen = set()
        active = []
        for flag_list in self.flag_history:
            for flag in flag_list:
                if flag not in seen:
                    seen.add(flag)
                    active.append(flag)
        return active

    def reset(self):
        """Resets the aggregator state for a new session/call."""
        self.scores.clear()
        self.flag_history.clear()
        self.current_rolling_score = 0.0
        self.current_alert_level = "low"
        self.total_chunks_processed = 0

    def create_risk_update(
        self,
        chunk_id: str,
        chunk_score: float,
        confidence: float = 0.95,
        flags: Optional[List[str]] = None,
        timestamp: Optional[str] = None
    ) -> RiskUpdate:
        """
        Helper method to process a new chunk score and generate a valid RiskUpdate Pydantic model.
        """
        rolling_score = self.update(chunk_score, flags=flags)
        
        return RiskUpdate(
            chunk_id=chunk_id,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            chunk_score=round(chunk_score, 4),
            rolling_risk_score=rolling_score,
            confidence=round(confidence, 4),
            flags=flags or [],
            alert_level=self.get_alert_level()
        )
