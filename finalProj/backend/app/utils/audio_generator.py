import os
import wave
import struct
import math
from typing import Optional
from pathlib import Path


def generate_sample_wav(output_path: str, duration_sec: float = 15.0, sample_rate: int = 16000, frequency: float = 440.0) -> str:
    """
    Generates a clean synthetic PCM 16-bit mono WAV audio file for call simulation testing.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    num_samples = int(duration_sec * sample_rate)
    
    with wave.open(str(path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Mix harmonics to sound like a voice vowel tone
            sample_val = (
                0.5 * math.sin(2.0 * math.pi * frequency * t) +
                0.3 * math.sin(2.0 * math.pi * (frequency * 2) * t) +
                0.15 * math.sin(2.0 * math.pi * (frequency * 3) * t) +
                0.05 * math.sin(2.0 * math.pi * 120.0 * t)  # Low fundamental pitch
            )
            
            # Add subtle envelope
            envelope = min(1.0, t / 0.1) * min(1.0, (duration_sec - t) / 0.1)
            int_val = int(sample_val * envelope * 24000.0)
            int_val = max(-32767, min(32767, int_val))
            data = struct.pack('<h', int_val)
            wav_file.writeframes(data)
            
    return str(path)


def ensure_default_sample_audio(data_dir: Optional[str] = None) -> str:
    """
    Ensures that a default demo WAV file exists in the backend data directory.
    """
    if data_dir:
        base_dir = Path(data_dir)
    else:
        # Default to backend/data/sample_calls
        backend_root = Path(__file__).parent.parent.parent
        base_dir = backend_root / "data" / "sample_calls"

    base_dir.mkdir(parents=True, exist_ok=True)
    demo_wav_path = base_dir / "demo_call.wav"
    
    if not demo_wav_path.exists():
        generate_sample_wav(str(demo_wav_path), duration_sec=18.0, frequency=220.0)
        
    return str(demo_wav_path)
