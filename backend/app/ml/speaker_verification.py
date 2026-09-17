"""
VoxGuard Consent-Based Speaker Verification & Identity Drift Tracker

Calculates cross-session speaker identity consistency by comparing ongoing call audio
against a consented genuine reference voice embedding using SpeechBrain ECAPA-TDNN / cosine similarity.

PRIVACY & CONSENT RULES:
1. Reference voice audio MUST be explicitly consented by the user/caller.
2. Raw reference audio and speaker embeddings are stored ONLY IN MEMORY during active call sessions.
3. Reference audio and embeddings are NEVER persisted in SQLite databases or disk logs.
4. Reference state is completely wiped from memory when the session ends or stops.

SECURITY DISCLAIMER:
Speaker verification detects speaker mismatches (identity drift), but does NOT prove whether speech is synthetic.
A speaker mismatch can occur due to legitimate co-callers, handoffs, background chatter, or spoof impersonation.
Prosody and Spectra acoustic anti-spoofing serve as independent signals.
"""

import io
import wave
import logging
import threading
import math
from typing import Dict, Any, Optional, Union, List, Tuple

logger = logging.getLogger("VoxGuard.SpeakerVerification")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# INITIAL UNCALIBRATED HEURISTIC THRESHOLDS FOR IDENTITY DRIFT
# WARNING: Baseline heuristics for demo purposes; not clinically or legally calibrated.
IDENTITY_MISMATCH_DRIFT_THRESHOLD = 0.45  # Identity drift > 0.45 indicates speaker mismatch
MIN_VOICED_AUDIO_DURATION_SEC = 0.5      # Minimum audio duration required for reliable embedding
DEFAULT_SAMPLE_RATE = 16000


def _cosine_similarity(emb1: Any, emb2: Any) -> float:
    """Computes cosine similarity between two 1D embedding vectors."""
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    sim = float(np.dot(emb1, emb2) / (norm1 * norm2))
    return max(-1.0, min(1.0, sim))


class SpeakerEmbeddingModel:
    """
    Thread-safe Singleton wrapper for SpeechBrain ECAPA-TDNN speaker verification model.
    Loads model once upon request and protects forward inference passes with a concurrency lock.
    """
    def __init__(self, model_source: str = "speechbrain/spkrec-ecapa-voxceleb"):
        self.model_source = model_source
        self.classifier = None
        self.is_loaded = False
        self.load_error = None
        self._lock = threading.Lock()

    def load_model(self) -> bool:
        if self.is_loaded:
            return True
        with self._lock:
            if self.is_loaded:
                return True
            try:
                try:
                    from speechbrain.inference.speaker import EncoderClassifier
                except ImportError:
                    from speechbrain.pretrained import EncoderClassifier

                logger.info("Loading SpeechBrain ECAPA-TDNN speaker model (%s)...", self.model_source)
                self.classifier = EncoderClassifier.from_hparams(
                    source=self.model_source,
                    run_opts={"device": "cpu"}
                )
                self.is_loaded = True
                logger.info("SpeechBrain ECAPA-TDNN model loaded successfully.")
                return True
            except Exception as e:
                self.is_loaded = False
                self.load_error = type(e).__name__
                logger.warning("SpeechBrain speaker model unavailable (%s). Returning identity_unavailable safely.", self.load_error)
                return False

    def compute_embedding(self, audio_array: Any, sample_rate: int = DEFAULT_SAMPLE_RATE) -> Optional[Any]:
        """
        Computes 1D numpy speaker embedding for a 16kHz mono audio float array.
        Protected by self._lock for thread safety.
        """
        if not self.is_loaded:
            if not self.load_model():
                return None

        try:
            import torch
            tensor_wav = torch.tensor(audio_array, dtype=torch.float32).unsqueeze(0)
            with self._lock:
                with torch.no_grad():
                    embeddings = self.classifier.encode_batch(tensor_wav)
                    emb_np = embeddings.squeeze().cpu().numpy()
            return emb_np
        except Exception as e:
            logger.error("Error computing speaker embedding: %s", e)
            return None


# Global singleton instance of SpeakerEmbeddingModel
_SPEAKER_MODEL_INSTANCE = None
_SPEAKER_MODEL_LOCK = threading.Lock()


def get_speaker_model() -> SpeakerEmbeddingModel:
    global _SPEAKER_MODEL_INSTANCE
    if _SPEAKER_MODEL_INSTANCE is None:
        with _SPEAKER_MODEL_LOCK:
            if _SPEAKER_MODEL_INSTANCE is None:
                _SPEAKER_MODEL_INSTANCE = SpeakerEmbeddingModel()
    return _SPEAKER_MODEL_INSTANCE


class SessionIdentityTracker:
    """
    Manages in-memory consented speaker identity enrollment and real-time identity drift tracking for a session.
    """
    def __init__(self, session_id: str, custom_model=None):
        self.session_id = session_id
        self.custom_model = custom_model  # Optional injected model/mock for offline testing
        self.reference_embedding: Optional[Any] = None
        self.is_enrolled: bool = False
        self._lock = threading.Lock()

    def enroll_reference(self, reference_input: Union[bytes, Any, List[float]], sample_rate: int = DEFAULT_SAMPLE_RATE) -> dict:
        """
        Enrolls a consented reference audio sample for this session.
        Computes and stores ONLY an in-memory 1D embedding vector.
        """
        with self._lock:
            if not HAS_NUMPY:
                return {"status": "identity_unavailable", "message": "numpy_unavailable"}

            audio = self._parse_to_float_array(reference_input, sample_rate)
            if audio is None or len(audio) == 0:
                return {"status": "reference_unavailable", "message": "invalid_reference_audio"}

            rms_energy = float(np.sqrt(np.mean(audio ** 2)))
            if rms_energy < 0.001:
                return {"status": "reference_unavailable", "message": "silent_reference_audio"}

            duration_sec = len(audio) / sample_rate
            if duration_sec < MIN_VOICED_AUDIO_DURATION_SEC:
                return {"status": "reference_unavailable", "message": "short_reference_audio"}

            if self.custom_model is not None:
                emb = self.custom_model.compute_embedding(audio, sample_rate)
            else:
                model = get_speaker_model()
                emb = model.compute_embedding(audio, sample_rate)

            if emb is None:
                return {"status": "identity_unavailable", "message": "model_unavailable"}

            self.reference_embedding = np.asarray(emb, dtype=np.float32)
            self.is_enrolled = True
            logger.info("Session %s: Consented reference speaker enrolled successfully (in-memory embedding size=%s).", self.session_id, self.reference_embedding.shape)

            return {"status": "ok", "message": "reference_enrolled"}

    def verify_chunk(self, chunk_input: Union[bytes, Any, List[float]], sample_rate: int = DEFAULT_SAMPLE_RATE) -> dict:
        """
        Verifies an ongoing audio chunk against the enrolled in-memory reference embedding.
        Returns speaker_similarity, identity_drift, confidence, status, and flags.
        """
        with self._lock:
            if not self.is_enrolled or self.reference_embedding is None:
                return {
                    "speaker_similarity": 0.0,
                    "identity_drift": 0.0,
                    "confidence": 0.0,
                    "status": "reference_unavailable",
                    "flags": ["reference_unavailable"]
                }

            if not HAS_NUMPY:
                return {
                    "speaker_similarity": 0.0,
                    "identity_drift": 0.0,
                    "confidence": 0.0,
                    "status": "identity_unavailable",
                    "flags": ["identity_unavailable"]
                }

            audio = self._parse_to_float_array(chunk_input, sample_rate)
            if audio is None or len(audio) == 0:
                return {
                    "speaker_similarity": 0.0,
                    "identity_drift": 0.0,
                    "confidence": 0.0,
                    "status": "invalid_audio",
                    "flags": ["invalid_audio"]
                }

            rms_energy = float(np.sqrt(np.mean(audio ** 2)))
            if rms_energy < 0.001:
                return {
                    "speaker_similarity": 0.0,
                    "identity_drift": 0.0,
                    "confidence": 0.0,
                    "status": "silent_audio",
                    "flags": ["silent_audio"]
                }

            duration_sec = len(audio) / sample_rate
            if duration_sec < MIN_VOICED_AUDIO_DURATION_SEC:
                return {
                    "speaker_similarity": 0.0,
                    "identity_drift": 0.0,
                    "confidence": 0.0,
                    "status": "insufficient_speech",
                    "flags": ["insufficient_speech"]
                }

            if self.custom_model is not None:
                chunk_emb = self.custom_model.compute_embedding(audio, sample_rate)
            else:
                model = get_speaker_model()
                chunk_emb = model.compute_embedding(audio, sample_rate)

            if chunk_emb is None:
                return {
                    "speaker_similarity": 0.0,
                    "identity_drift": 0.0,
                    "confidence": 0.0,
                    "status": "identity_unavailable",
                    "flags": ["identity_unavailable"]
                }

            chunk_emb_np = np.asarray(chunk_emb, dtype=np.float32)
            cos_sim = _cosine_similarity(self.reference_embedding, chunk_emb_np)
            speaker_similarity = round(max(0.0, min(1.0, (cos_sim + 1.0) / 2.0)), 4)
            identity_drift = round(max(0.0, min(1.0, 1.0 - speaker_similarity)), 4)
            confidence = 0.85

            flags = []
            if identity_drift > IDENTITY_MISMATCH_DRIFT_THRESHOLD:
                flags.append("identity_mismatch")

            return {
                "speaker_similarity": speaker_similarity,
                "identity_drift": identity_drift,
                "confidence": confidence,
                "status": "ok",
                "flags": sorted(flags)
            }

    def clear(self):
        """Wipes the enrolled reference embedding from memory."""
        with self._lock:
            self.reference_embedding = None
            self.is_enrolled = False
            logger.info("Session %s: Reference speaker embedding wiped from memory.", self.session_id)

    @staticmethod
    def _parse_to_float_array(audio_input: Union[bytes, Any, List[float]], sample_rate: int) -> Optional[Any]:
        """Helper to convert WAV bytes or list to 16kHz float32 numpy array."""
        if not HAS_NUMPY:
            return None

        if isinstance(audio_input, np.ndarray):
            return audio_input.astype(np.float32)
        if isinstance(audio_input, list):
            return np.array(audio_input, dtype=np.float32)
        if isinstance(audio_input, bytes):
            if len(audio_input) < 44:
                return None
            try:
                with wave.open(io.BytesIO(audio_input), "rb") as wav:
                    sr = wav.getframerate()
                    channels = wav.getnchannels()
                    sample_width = wav.getsampwidth()
                    n_frames = wav.getnframes()
                    if n_frames == 0 or sample_width != 2:
                        return None
                    frames = wav.readframes(n_frames)

                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                if channels > 1:
                    audio = audio.reshape(-1, channels).mean(axis=1)

                if sr != DEFAULT_SAMPLE_RATE:
                    old_idx = np.linspace(0, len(audio) - 1, num=len(audio))
                    new_len = int(len(audio) * DEFAULT_SAMPLE_RATE / sr)
                    new_idx = np.linspace(0, len(audio) - 1, num=new_len)
                    audio = np.interp(new_idx, old_idx, audio).astype(np.float32)

                return audio
            except Exception:
                return None
        return None
