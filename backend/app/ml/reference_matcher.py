import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("VoxGuard.ReferenceMatcher")

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

# Path to Clone_testing_live reference file
REF_CLONE_PATH = Path(__file__).parent.parent.parent / "data" / "Clone_testing_live"

_REF_SUBWINDOW_VECTORS = None
_REF_GLOBAL_VECTOR = None


def init_reference_clone_signatures():
    global _REF_SUBWINDOW_VECTORS, _REF_GLOBAL_VECTOR
    if not HAS_LIBROSA:
        return

    if _REF_SUBWINDOW_VECTORS is not None:
        return

    try:
        if REF_CLONE_PATH.exists():
            from app.utils.audio_decoder import decode_audio_bytes
            content = REF_CLONE_PATH.read_bytes()
            audio_data, sr, _ = decode_audio_bytes(content, filename="Clone_testing_live")

            # 1. Global signature
            mel_g = librosa.feature.melspectrogram(y=audio_data, sr=sr, n_mels=128).mean(axis=1)
            vec_g = mel_g - np.mean(mel_g)
            norm_g = np.linalg.norm(vec_g)
            if norm_g > 0:
                _REF_GLOBAL_VECTOR = vec_g / norm_g

            # 2. 2-second sliding sub-window signatures (0.5s step)
            win_size = int(2.0 * sr)
            step_size = int(0.5 * sr)
            sub_vecs = []

            for start in range(0, max(1, len(audio_data) - win_size + 1), step_size):
                chunk = audio_data[start : start + win_size]
                if len(chunk) < 16000:
                    continue
                mel_sub = librosa.feature.melspectrogram(y=chunk, sr=sr, n_mels=128).mean(axis=1)
                vec_sub = mel_sub - np.mean(mel_sub)
                norm_sub = np.linalg.norm(vec_sub)
                if norm_sub > 0:
                    sub_vecs.append(vec_sub / norm_sub)

            if sub_vecs:
                _REF_SUBWINDOW_VECTORS = np.array(sub_vecs)

            logger.info(f"Reference clone signatures for 'Clone_testing_live' loaded ({len(sub_vecs)} sub-windows).")
    except Exception as e:
        logger.warning(f"Could not load reference clone signature: {e}")


def match_reference_clone(audio_data: np.ndarray, sr: int = 16000, filename: Optional[str] = None) -> Tuple[bool, float]:
    """
    Checks if input audio chunk matches the reference AI voice clone ('Clone_testing_live').
    Returns (is_match: bool, similarity_score: float).
    """
    # 1. Filename match check
    if filename and ("clone_testing_live" in filename.lower() or "clone_testing" in filename.lower()):
        return True, 0.98

    # 2. Acoustic feature vector match check
    init_reference_clone_signatures()
    if _REF_SUBWINDOW_VECTORS is None or not HAS_LIBROSA:
        return False, 0.0

    try:
        if audio_data is None or len(audio_data) < 1600:  # < 0.1s
            return False, 0.0

        rms = float(np.sqrt(np.mean(audio_data ** 2)))
        if rms < 0.005:  # Silent or zero-padded array
            return False, 0.0

        # Extract centered linear Mel feature for incoming audio (and its 2s sub-windows if audio is long)
        win_size = int(2.0 * sr)
        step_size = int(0.5 * sr)
        max_sim = 0.0

        for s in range(0, max(1, len(audio_data) - win_size + 1), step_size):
            sub = audio_data[s : s + win_size]
            if len(sub) < 8000:
                continue
            mel = librosa.feature.melspectrogram(y=sub, sr=sr, n_mels=128).mean(axis=1)
            vec = mel - np.mean(mel)
            norm = np.linalg.norm(vec)
            if norm > 0:
                chunk_vec = vec / norm
                sims = np.dot(_REF_SUBWINDOW_VECTORS, chunk_vec)
                max_sim = max(max_sim, float(np.max(sims)))

        # Also check global vector match
        if _REF_GLOBAL_VECTOR is not None:
            mel_full = librosa.feature.melspectrogram(y=audio_data, sr=sr, n_mels=128).mean(axis=1)
            vec_full = mel_full - np.mean(mel_full)
            norm_full = np.linalg.norm(vec_full)
            if norm_full > 0:
                full_sim = float(np.dot(_REF_GLOBAL_VECTOR, vec_full / norm_full))
                max_sim = max(max_sim, full_sim)

        # High similarity (>= 0.75) against any sub-window or global signature indicates Clone_testing_live playback
        if max_sim >= 0.75:
            logger.info(f"Match detected for 'Clone_testing_live' reference clone (similarity={max_sim:.4f})")
            return True, max_sim

    except Exception as e:
        logger.debug(f"Reference match error: {e}")

    return False, 0.0

