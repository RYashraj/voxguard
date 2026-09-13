import random
import struct
import math
from typing import Dict, Any, Optional, List


class MLStubSession:
    """
    Simulates ML inference for audio chunks across a session.
    Generates realistic score trajectories matching evaluation day requirements.
    """
    def __init__(self, scenario: str = "gradual_escalation"):
        self.scenario = scenario
        self.call_count = 0

    def analyze_chunk(self, audio_bytes: bytes) -> Dict[str, Any]:
        self.call_count += 1
        return analyze_chunk_stub(audio_bytes, step=self.call_count, scenario=self.scenario)


def analyze_chunk_stub(
    audio_bytes: bytes,
    step: Optional[int] = None,
    scenario: str = "gradual_escalation"
) -> Dict[str, Any]:
    """
    Day 4 Requirement: ML Stub Inference Function
    Analyzes an audio chunk's raw bytes and returns:
    - chunk_score (float, 0.0 to 1.0)
    - confidence (float, 0.0 to 1.0)
    - flags (list of detected synthetic flags)
    """
    current_step = step if step is not None else 1
    
    # Calculate simple acoustic signal metrics from raw bytes if available (for realism)
    rms_energy = 0.0
    if len(audio_bytes) >= 44:  # WAV header is 44 bytes
        pcm_data = audio_bytes[44:]
        sample_count = len(pcm_data) // 2
        if sample_count > 0:
            try:
                samples = struct.unpack(f"<{min(sample_count, 1000)}h", pcm_data[:min(sample_count, 1000) * 2])
                sum_sq = sum(s * s for s in samples)
                rms_energy = math.sqrt(sum_sq / len(samples)) / 32768.0
            except Exception:
                pass

    # Score generation logic per scenario
    if scenario == "clean":
        # Safe human voice conversation (score remains comfortably < 0.35)
        base_score = 0.08 + (random.uniform(-0.03, 0.04))
        chunk_score = round(max(0.02, min(0.28, base_score)), 4)
        confidence = round(random.uniform(0.92, 0.98), 4)
        flags: List[str] = []

    elif scenario == "suspicious":
        # Immediate high-risk synthetic / deepfake voice (score > 0.75)
        base_score = 0.85 + (random.uniform(-0.05, 0.08))
        chunk_score = round(max(0.72, min(0.99, base_score)), 4)
        confidence = round(random.uniform(0.90, 0.97), 4)
        flags = ["synthetic_artifact", "prosody_flatness"]

    else:
        # "gradual_escalation": Simulates live call getting progressively riskier
        # Steps 1-2: Normal conversation (Green, score ~0.10 - 0.25)
        # Steps 3-4: Switch to AI voice / prosody anomalies (Yellow, score ~0.45 - 0.65)
        # Steps 5+: High-risk spoof / transaction fraud attempt (Red, score ~0.82 - 0.96)
        if current_step <= 2:
            base_score = 0.10 + 0.05 * current_step + random.uniform(-0.02, 0.03)
            chunk_score = round(max(0.04, min(0.30, base_score)), 4)
            confidence = round(random.uniform(0.93, 0.98), 4)
            flags = []
        elif current_step <= 4:
            base_score = 0.45 + 0.08 * (current_step - 2) + random.uniform(-0.03, 0.03)
            chunk_score = round(max(0.40, min(0.68, base_score)), 4)
            confidence = round(random.uniform(0.90, 0.96), 4)
            flags = ["prosody_flatness"]
        else:
            base_score = 0.80 + 0.05 * min(current_step - 4, 3) + random.uniform(-0.02, 0.04)
            chunk_score = round(max(0.75, min(0.98, base_score)), 4)
            confidence = round(random.uniform(0.94, 0.99), 4)
            flags = ["synthetic_artifact", "spectral_discontinuity", "prosody_flatness"]

    return {
        "chunk_score": chunk_score,
        "confidence": confidence,
        "flags": flags,
        "rms_energy": round(rms_energy, 4)
    }
