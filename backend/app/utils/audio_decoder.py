import io
import wave
import logging
from typing import Tuple, Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger("voxguard.audio_decoder")

TARGET_SAMPLE_RATE = 16000


def decode_audio_bytes(audio_bytes: bytes, filename: Optional[str] = None) -> Tuple[np.ndarray, int, bytes]:
    """
    Decodes audio bytes of any format (WAV, WebM, MP3, M4A, OGG, FLAC) into:
    - 16kHz mono float32 numpy array
    - sample rate (16000)
    - standard 16-bit mono PCM WAV bytes ready for model inference
    """
    if not audio_bytes or len(audio_bytes) < 16:
        raise ValueError("Audio file is empty or corrupted.")

    audio_data: Optional[np.ndarray] = None
    sr: int = TARGET_SAMPLE_RATE

    # 1. Try wave module first if it's standard WAV
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            n_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            frames = wav_file.readframes(n_frames)
            
            if sampwidth == 2:
                raw_int16 = np.frombuffer(frames, dtype=np.int16)
                if n_channels > 1:
                    raw_int16 = raw_int16.reshape(-1, n_channels).mean(axis=1)
                audio_data = raw_int16.astype(np.float32) / 32768.0
                sr = framerate
    except Exception:
        audio_data = None

    # 2. Try PyAV (handles WebM, Opus, AAC/M4A, MP3, OGG seamlessly)
    if audio_data is None:
        try:
            import av
            container = av.open(io.BytesIO(audio_bytes))
            resampler = av.AudioResampler(format="s16", layout="mono", rate=TARGET_SAMPLE_RATE)
            samples = []
            for frame in container.decode(audio=0):
                for resampled_frame in resampler.resample(frame):
                    samples.append(resampled_frame.to_ndarray())
            container.close()
            if samples:
                concatenated = np.concatenate(samples, axis=1).squeeze(0)
                audio_data = concatenated.astype(np.float32) / 32768.0
                sr = TARGET_SAMPLE_RATE
        except Exception as av_err:
            logger.debug(f"PyAV decode error: {av_err}")
            audio_data = None

    # 3. Try soundfile / librosa fallback
    if audio_data is None:
        try:
            import soundfile as sf
            data, orig_sr = sf.read(io.BytesIO(audio_bytes))
            if data.ndim > 1:
                data = data.mean(axis=1)
            audio_data = data.astype(np.float32)
            sr = orig_sr
        except Exception:
            try:
                import librosa
                data, orig_sr = librosa.load(io.BytesIO(audio_bytes), sr=TARGET_SAMPLE_RATE)
                audio_data = data.astype(np.float32)
                sr = TARGET_SAMPLE_RATE
            except Exception as lib_err:
                raise ValueError(f"Could not decode audio format: {lib_err}")

    if audio_data is None or len(audio_data) == 0:
        raise ValueError("Decoded audio stream contains no valid frames.")

    # Resample to 16kHz if needed
    if sr != TARGET_SAMPLE_RATE:
        try:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)
            sr = TARGET_SAMPLE_RATE
        except Exception:
            old_len = len(audio_data)
            new_len = int(old_len * TARGET_SAMPLE_RATE / sr)
            audio_data = np.interp(
                np.linspace(0, old_len - 1, new_len),
                np.arange(old_len),
                audio_data
            ).astype(np.float32)
            sr = TARGET_SAMPLE_RATE

    # Preserve raw spectral range for neural vocoder artifact detection up to 8kHz Nyquist frequency
    # No artificial high-frequency cutoff applied so synthetic vocoder artifacts remain intact

    # Create 16-bit PCM WAV bytes
    int16_samples = (np.clip(audio_data, -1.0, 1.0) * 32767.0).astype(np.int16)
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(2)
        wav_out.setframerate(TARGET_SAMPLE_RATE)
        wav_out.writeframes(int16_samples.tobytes())

    return audio_data, sr, wav_buffer.getvalue()
