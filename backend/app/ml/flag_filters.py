"""Utility functions for filtering flags emitted by the ML layer prior to public output."""

from typing import List

# Prosody-only heuristic labels that must not appear in public runtime output
PROSODY_ONLY_FLAGS = {
    "low_pitch_variation",
    "prosody_flatness",
    "high_pause_ratio",
    "low_voiced_ratio",
    "insufficient_speech",
    "insufficient_voiced_speech",
    "prosody_unavailable",
    "prosody_anomaly",
    "low_f0_variability",
}


def filter_public_flags(flags: List[str]) -> List[str]:
    """
    Filters out internal research/unvalidated prosody heuristic flags from public RiskUpdate flags.
    
    Reliable operational/acoustic flags (such as synthetic_artifact, short_audio,
    silent_audio, invalid_audio, model_unavailable, inference_error) are preserved.
    """
    if not flags:
        return []
    return [flag for flag in flags if flag not in PROSODY_ONLY_FLAGS]
