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
        
        # Precompute weights for O(1) lookup
        self._weights = {i: list(range(1, i + 1)) for i in range(1, window_size + 1)}
        self._weight_sums = {i: sum(self._weights[i]) for i in range(1, window_size + 1)}

    def update(
        self, 
        chunk_score: float, 
        prosody_score: Optional[float] = None,
        identity_drift: Optional[float] = None,
        flags: Optional[List[str]] = None
    ) -> float:
        """
        Updates the aggregator with new ML scores.
        Fuses AASIST (chunk_score), Prosody, and Identity into a unified threat score.
        Returns the computed rolling risk score.
        """
        # Feature Fusion Logic (SIH Strategy: Multi-layer threat detection)
        # 1. Base score is the Deepfake/AASIST score
        fused_score = float(chunk_score)

        # 2. If it's a human, but the identity doesn't match the CEO (mimic attack)
        if identity_drift is not None and identity_drift > 0.5:
            # High drift means it's an impersonator. Push risk up.
            fused_score = max(fused_score, identity_drift)
            if flags is not None and "impersonator_detected" not in flags:
                flags.append("impersonator_detected")

        # 3. If prosody is highly robotic, penalize slightly
        if prosody_score is not None and prosody_score > 0.7:
            fused_score = max(fused_score, chunk_score + 0.2)
            if flags is not None and "robotic_prosody" not in flags:
                flags.append("robotic_prosody")

        # Clamp fused_score to [0.0, 1.0]
        clamped_score = max(0.0, min(1.0, fused_score))
        self.scores.append(clamped_score)
        self.flag_history.append(flags or [])
        self.total_chunks_processed += 1

        n = len(self.scores)
        if n == 0:
            return 0.0
            
        weights = self._weights[n]
        total_weight = self._weight_sums[n]
        
        # Generator expression sum is fast for small n
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
        timestamp: Optional[str] = None,
        **kwargs
    ) -> RiskUpdate:
        """
        Helper method to process a new chunk score and generate a valid RiskUpdate Pydantic model.
        """
        prosody = kwargs.get("prosody_score")
        identity = kwargs.get("identity_drift")
        rolling_score = self.update(
            chunk_score, 
            prosody_score=prosody, 
            identity_drift=identity, 
            flags=flags
        )
        
        return RiskUpdate(
            chunk_id=chunk_id,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            chunk_score=round(chunk_score, 4),
            rolling_risk_score=rolling_score,
            confidence=round(confidence, 4),
            flags=flags or [],
            alert_level=self.get_alert_level(),
            **kwargs
        )
