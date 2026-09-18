"""
VoxGuard Prosody & Behavioural Analysis Layer

Calculates explainable acoustic prosody features:
- Fundamental frequency (F0/pitch) mean, variance, and standard deviation
- Voiced speech ratio
- Pause count and pause-duration ratio
- Speech rate proxy (voiced-burst / energy-segment rate)
- Quality status and safe failure handling

NOTE ON THRESHOLDS:
The anomaly detection thresholds defined in this module are initial baseline heuristics.
They are NOT clinically or scientifically calibrated across diverse speakers, languages, or telephony codecs.
Prosody features serve as supporting signals only and DO NOT constitute proof of AI synthetic cloning.
"""

import io
import math
import wave
import logging
from typing import Dict, Any, Union, List, Optional

logger = logging.getLogger("VoxGuard.Prosody")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import scipy.signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


# INITIAL UNCALIBRATED HEURISTIC THRESHOLDS
# WARNING: These thresholds are uncalibrated baseline heuristics.
LOW_F0_STD_THRESHOLD_HZ = 8.0        # Pitch std dev < 8 Hz suggests unusually flat pitch
HIGH_PAUSE_RATIO_THRESHOLD = 0.40    # Pause duration > 40% of chunk duration
LOW_VOICED_RATIO_THRESHOLD = 0.20    # Voiced speech < 20% of active frames
MIN_VOICED_FRAMES_REQUIRED = 5       # Minimum voiced frames required for F0 stats
DEFAULT_SAMPLE_RATE = 16000


def _parse_wav_bytes_to_float(audio_bytes: bytes) -> tuple[Optional[Any], float, List[str]]:
    """Helper to convert raw WAV bytes to float32 audio array normalized to [-1.0, 1.0]."""
    if not audio_bytes or len(audio_bytes) < 44:
        return None, 0.0, ["invalid_audio"]

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            sr = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            n_frames = wav.getnframes()

            if n_frames == 0 or sample_width != 2:
                return None, 0.0, ["invalid_audio"]

            frames = wav.readframes(n_frames)

        if not HAS_NUMPY:
            return None, 0.0, ["prosody_unavailable"]

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        if sr != DEFAULT_SAMPLE_RATE:
            try:
                import torch
                import torchaudio
                waveform = torch.tensor(audio).unsqueeze(0)
                waveform = torchaudio.functional.resample(waveform, sr, DEFAULT_SAMPLE_RATE)
                audio = waveform.squeeze(0).numpy()
            except Exception:
                old_idx = np.linspace(0, len(audio) - 1, num=len(audio))
                new_len = int(len(audio) * DEFAULT_SAMPLE_RATE / sr)
                new_idx = np.linspace(0, len(audio) - 1, num=new_len)
                audio = np.interp(new_idx, old_idx, audio).astype(np.float32)

        rms_energy = float(np.sqrt(np.mean(audio ** 2)))
        flags = []
        if rms_energy < 0.001:
            flags.append("silent_audio")

        return audio, rms_energy, flags

    except Exception as e:
        logger.debug(f"WAV parse error in prosody: {e}")
        return None, 0.0, ["invalid_audio"]


def extract_prosody_features(
    audio_input: Union[bytes, Any, List[float]],
    sample_rate: int = DEFAULT_SAMPLE_RATE
) -> Dict[str, Any]:
    """
    Extracts acoustic prosody features from either raw WAV bytes or a pre-normalized float waveform.
    
    Accepts:
    - raw WAV bytes; or
    - an already-normalized 16 kHz mono waveform (numpy array or list of floats)
    
    Returns a dictionary containing:
    - status: "ok" | "silent_audio" | "invalid_audio" | "insufficient_voiced_speech" | "short_audio" | "prosody_unavailable"
    - pitch_mean_hz: float or None
    - pitch_std_hz: float or None
    - pitch_variance: float or None
    - voiced_ratio: float (0.0 to 1.0)
    - pause_count: int
    - pause_duration_ratio: float (0.0 to 1.0)
    - speech_rate_proxy: float (voiced-burst / energy-segment rate per second)
    - jitter: None (labeled unreliable on short 3-second streaming chunks)
    - shimmer: None (labeled unreliable on short 3-second streaming chunks)
    - duration_sec: float
    - rms_energy: float
    """
    default_response = {
        "status": "invalid_audio",
        "pitch_mean_hz": None,
        "pitch_std_hz": None,
        "pitch_variance": None,
        "voiced_ratio": 0.0,
        "pause_count": 0,
        "pause_duration_ratio": 0.0,
        "speech_rate_proxy": 0.0,
        "jitter": None,
        "shimmer": None,
        "duration_sec": 0.0,
        "rms_energy": 0.0,
        "quality_notes": []
    }

    if not HAS_NUMPY:
        default_response["status"] = "prosody_unavailable"
        default_response["quality_notes"].append("numpy_unavailable")
        return default_response

    try:
        # Handle dual input types (bytes vs pre-parsed waveform array)
        if isinstance(audio_input, bytes):
            audio, rms_energy, flags = _parse_wav_bytes_to_float(audio_input)
            if "invalid_audio" in flags:
                default_response["status"] = "invalid_audio"
                return default_response
            if "silent_audio" in flags:
                default_response["status"] = "silent_audio"
                default_response["rms_energy"] = rms_energy
                return default_response
            sr = DEFAULT_SAMPLE_RATE
        elif isinstance(audio_input, (np.ndarray, list)):
            audio = np.asarray(audio_input, dtype=np.float32)
            sr = sample_rate
            if len(audio) == 0:
                default_response["status"] = "invalid_audio"
                return default_response
            rms_energy = float(np.sqrt(np.mean(audio ** 2)))
            if rms_energy < 0.001:
                default_response["status"] = "silent_audio"
                default_response["rms_energy"] = rms_energy
                default_response["duration_sec"] = round(len(audio) / sr, 3)
                return default_response
        else:
            default_response["status"] = "invalid_audio"
            return default_response

        duration_sec = float(len(audio) / sr)
        if duration_sec < 0.2:
            default_response["status"] = "short_audio"
            default_response["duration_sec"] = round(duration_sec, 3)
            default_response["rms_energy"] = round(rms_energy, 4)
            return default_response

        # Frame parameters for prosody analysis
        frame_len = int(0.030 * sr)  # 30 ms frame
        hop_len = int(0.010 * sr)    # 10 ms hop
        n_frames = max(1, (len(audio) - frame_len) // hop_len + 1)

        # 1. Pitch / F0 Extraction (using librosa.pyin if available, otherwise autocorrelation)
        f0_list = []
        is_voiced_list = []

        if HAS_LIBROSA:
            try:
                f0, voiced_flag, _ = librosa.pyin(
                    audio,
                    fmin=65,
                    fmax=400,
                    sr=sr,
                    frame_length=frame_len,
                    hop_length=hop_len
                )
                if f0 is not None:
                    for p, v in zip(f0, voiced_flag):
                        if v and not np.isnan(p) and p > 0:
                            f0_list.append(float(p))
                            is_voiced_list.append(True)
                        else:
                            is_voiced_list.append(False)
            except Exception as librosa_err:
                logger.debug(f"librosa pyin extraction fallback: {librosa_err}")
                f0_list = []
                is_voiced_list = []

        if not f0_list and HAS_NUMPY:
            # Autocorrelation-based F0 pitch extraction fallback
            min_lag = int(sr / 400)  # 400 Hz max pitch
            max_lag = int(sr / 65)   # 65 Hz min pitch

            for i in range(n_frames):
                start = i * hop_len
                end = start + frame_len
                if end > len(audio):
                    break
                frame = audio[start:end]
                frame_rms = float(np.sqrt(np.mean(frame ** 2)))
                if frame_rms < 0.01:
                    is_voiced_list.append(False)
                    continue

                # Normalized autocorrelation
                corr = np.correlate(frame, frame, mode='full')
                corr = corr[len(frame)-1:]
                if corr[0] <= 0:
                    is_voiced_list.append(False)
                    continue

                norm_corr = corr / corr[0]
                if max_lag >= len(norm_corr):
                    is_voiced_list.append(False)
                    continue

                search_window = norm_corr[min_lag:max_lag]
                if len(search_window) == 0:
                    is_voiced_list.append(False)
                    continue

                peak_idx = int(np.argmax(search_window)) + min_lag
                peak_val = float(norm_corr[peak_idx])

                if peak_val > 0.45:  # Voicing threshold
                    f0_val = float(sr / peak_idx)
                    f0_list.append(f0_val)
                    is_voiced_list.append(True)
                else:
                    is_voiced_list.append(False)

        total_analyzed_frames = len(is_voiced_list) if is_voiced_list else n_frames
        voiced_frames_count = len(f0_list)
        voiced_ratio = float(voiced_frames_count / max(1, total_analyzed_frames))

        # 2. Pitch statistics
        if voiced_frames_count >= MIN_VOICED_FRAMES_REQUIRED:
            f0_arr = np.array(f0_list, dtype=np.float32)
            pitch_mean_hz = float(np.mean(f0_arr))
            pitch_std_hz = float(np.std(f0_arr))
            pitch_variance = float(np.var(f0_arr))
            status = "ok"
        else:
            pitch_mean_hz = None
            pitch_std_hz = None
            pitch_variance = None
            status = "insufficient_voiced_speech"

        # 3. Pause detection and pause-duration ratio
        pause_frame_threshold = int(0.200 / (hop_len / sr))
        current_unvoiced = 0
        pause_count = 0
        total_pause_frames = 0

        for voiced in is_voiced_list:
            if not voiced:
                current_unvoiced += 1
            else:
                if current_unvoiced >= pause_frame_threshold:
                    pause_count += 1
                    total_pause_frames += current_unvoiced
                current_unvoiced = 0

        if current_unvoiced >= pause_frame_threshold:
            pause_count += 1
            total_pause_frames += current_unvoiced

        pause_duration_ratio = float(total_pause_frames / max(1, total_analyzed_frames))

        # 4. Speech rate proxy (voiced-burst / energy-segment rate per second)
        voiced_bursts = 0
        prev_voiced = False
        for v in is_voiced_list:
            if v and not prev_voiced:
                voiced_bursts += 1
            prev_voiced = v

        voiced_burst_rate_hz = float(voiced_bursts / max(0.1, duration_sec))

        return {
            "status": status,
            "pitch_mean_hz": round(pitch_mean_hz, 2) if pitch_mean_hz is not None else None,
            "pitch_std_hz": round(pitch_std_hz, 2) if pitch_std_hz is not None else None,
            "pitch_variance": round(pitch_variance, 2) if pitch_variance is not None else None,
            "voiced_ratio": round(voiced_ratio, 4),
            "pause_count": pause_count,
            "pause_duration_ratio": round(pause_duration_ratio, 4),
            "speech_rate_proxy": round(voiced_burst_rate_hz, 2),  # Voiced-burst rate per sec
            "jitter": None,   # Cycle-level jitter unreliable on 3s frame-based chunks
            "shimmer": None,  # Cycle-level shimmer unreliable on 3s frame-based chunks
            "duration_sec": round(duration_sec, 3),
            "rms_energy": round(rms_energy, 4),
            "quality_notes": [] if status == "ok" else [status]
        }

    except Exception as e:
        logger.error(f"Error in extract_prosody_features: {e}", exc_info=True)
        default_response["status"] = "prosody_unavailable"
        default_response["quality_notes"].append("prosody_extraction_error")
        return default_response


def assess_prosody(features: dict) -> dict:
    """
    Evaluates prosody features against initial uncalibrated heuristic thresholds.
    
    Returns:
    - prosody_score: float (0.0 to 1.0 supporting anomaly metric)
    - confidence: float
    - flags: list of user/UI-facing flags (e.g. ['prosody_flatness', 'high_pause_ratio'])
    - reason_codes: list of precise internal reason codes (e.g. ['low_f0_variability'])
    """
    status = features.get("status", "ok")

    if status in ("silent_audio", "invalid_audio", "short_audio", "insufficient_voiced_speech", "prosody_unavailable"):
        return {
            "prosody_score": 0.0,
            "confidence": 0.0,
            "flags": [status],
            "reason_codes": [status]
        }

    flags = []
    reason_codes = []

    pitch_std = features.get("pitch_std_hz")
    voiced_ratio = features.get("voiced_ratio", 0.0)
    pause_ratio = features.get("pause_duration_ratio", 0.0)

    # 1. Pitch variability assessment
    if pitch_std is not None and pitch_std < LOW_F0_STD_THRESHOLD_HZ:
        reason_codes.append("low_f0_variability")
        flags.append("prosody_flatness")  # User-facing flag for UI compatibility

    # 2. Pause ratio assessment
    if pause_ratio > HIGH_PAUSE_RATIO_THRESHOLD:
        reason_codes.append("high_pause_ratio")
        flags.append("high_pause_ratio")

    # 3. Voiced ratio assessment
    if voiced_ratio < LOW_VOICED_RATIO_THRESHOLD:
        reason_codes.append("low_voiced_ratio")
        flags.append("low_voiced_ratio")

    # Calculate supporting prosody anomaly score
    if "low_f0_variability" in reason_codes:
        f0_deficit = (LOW_F0_STD_THRESHOLD_HZ - (pitch_std or 0.0)) / LOW_F0_STD_THRESHOLD_HZ
        prosody_score = round(min(0.95, 0.60 + 0.35 * f0_deficit), 4)
        confidence = 0.85
    elif reason_codes:
        prosody_score = 0.50
        confidence = 0.75
    else:
        prosody_score = 0.05
        confidence = 0.90

    return {
        "prosody_score": prosody_score,
        "confidence": confidence,
        "flags": sorted(list(set(flags))),
        "reason_codes": sorted(list(set(reason_codes)))
    }
