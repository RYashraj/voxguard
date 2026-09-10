import os
import asyncio
import logging
from typing import Dict, Any

from app.ml.ml_model import analyze_chunk as analyze_chunk_real
from app.ml.stub import analyze_chunk_stub

logger = logging.getLogger("voxguard.ml_analyzer")


async def analyze_chunk_dispatch(
    audio_bytes: bytes,
    step: int = 1,
    scenario: str = "gradual_escalation"
) -> Dict[str, Any]:
    """
    Backend ML analyzer dispatcher.
    Routes audio chunk analysis based on VOXGUARD_ML_MODE env var:
    - 'real' (default): Runs real ML model inference off the main event loop thread via asyncio.to_thread.
    - 'stub': Runs simulated stub scenario for development/testing.
    - Any other value: Raises a ValueError configuration error.
    """
    raw_mode = os.getenv("VOXGUARD_ML_MODE", "real").lower().strip()

    if raw_mode not in ("real", "stub"):
        raise ValueError(
            f"Invalid VOXGUARD_ML_MODE: '{raw_mode}'. Allowed values are 'real' or 'stub'."
        )

    if raw_mode == "stub":
        logger.debug(f"VOXGUARD_ML_MODE=stub: running analyze_chunk_stub (step={step}, scenario={scenario})")
        return analyze_chunk_stub(audio_bytes=audio_bytes, step=step, scenario=scenario)

    # Real ML mode (default)
    # Execute synchronous ML inference safely off the main event loop thread
    return await asyncio.to_thread(analyze_chunk_real, audio_bytes)
