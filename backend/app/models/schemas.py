from typing import List, Literal, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class RiskUpdate(BaseModel):
    """
    Core data contract for VoxGuard.
    Every message streamed from the backend to the frontend MUST match this shape exactly.
    """
    chunk_id: str = Field(..., description="Unique identifier for the audio chunk (e.g., 'chunk_001')")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 formatted timestamp"
    )
    chunk_score: float = Field(..., ge=0.0, le=1.0, description="Raw impersonation risk score for this chunk (0.0 to 1.0)")
    rolling_risk_score: float = Field(..., ge=0.0, le=1.0, description="Smoothed rolling risk score across recent chunks")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score for this analysis (0.0 to 1.0)")
    flags: List[str] = Field(
        default_factory=list,
        description="Detection flags (e.g., ['synthetic_artifact', 'prosody_flatness', 'spectral_discontinuity'])"
    )
    alert_level: Literal["low", "medium", "high"] = Field(
        ...,
        description="Threat level based on risk thresholds: low (<0.4), medium (0.4-0.7), high (>0.7)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "chunk_id": "chunk_001",
                "timestamp": "2026-09-10T15:00:00.000000+00:00",
                "chunk_score": 0.12,
                "rolling_risk_score": 0.12,
                "confidence": 0.94,
                "flags": ["synthetic_artifact"],
                "alert_level": "low"
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"


class SimulationRequest(BaseModel):
    """Request payload to trigger a simulated call stream."""
    file_path: Optional[str] = Field(None, description="Path to a WAV file to stream. If omitted, uses default demo audio.")
    chunk_duration_sec: float = Field(3.0, ge=0.5, le=10.0, description="Duration of each audio chunk in seconds (default 3s)")
    delay_sec: float = Field(3.0, ge=0.01, le=10.0, description="Delay between yielding chunks to mimic live incoming audio")
    scenario: Literal["default", "clean", "suspicious", "gradual_escalation"] = Field(
        "gradual_escalation",
        description="Simulation scenario for chunk score trends"
    )


class SimulationResponse(BaseModel):
    """Response returned when simulation is started or stopped."""
    status: str
    message: str
    session_id: str
    total_chunks: Optional[int] = None
