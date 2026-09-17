import torch
import torch.nn.functional as F
import numpy as np
import threading
import logging
import torchaudio

logger = logging.getLogger("VoxGuard.Identity")

class IdentityTracker:
    """
    Robust thread-safe Identity Tracker utilizing SpeechBrain's ECAPA-TDNN 
    for speaker verification and impersonation detection.
    """
    def __init__(self, reference_audio_path: str = None, reference_embedding: torch.Tensor = None):
        self.classifier = None
        self.is_loaded = False
        self._lock = threading.Lock()
        
        self.reference_embedding = reference_embedding
        self._load_model()
        
        if reference_audio_path and self.reference_embedding is None:
            self.enroll(reference_audio_path)

    def _load_model(self):
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            logger.info("Loading ECAPA-TDNN Speaker Verification model...")
            self.classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                # save_dir="pretrained_models/spkrec-ecapa-voxceleb"
            )
            self.classifier.eval()
            self.is_loaded = True
            logger.info("ECAPA-TDNN loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ECAPA-TDNN: {e}")
            self.is_loaded = False

    def _get_embedding(self, audio_path: str) -> torch.Tensor:
        if not self.is_loaded:
            raise RuntimeError("ECAPA-TDNN model is not loaded.")
            
        with self._lock:
            # speechbrain loads audio and processes it internally, but we should handle it robustly
            signal, fs = torchaudio.load(audio_path)
            if fs != 16000:
                signal = torchaudio.functional.resample(signal, fs, 16000)
            
            # Ensure mono
            if signal.shape[0] > 1:
                signal = signal.mean(dim=0, keepdim=True)
                
            embeddings = self.classifier.encode_batch(signal)
            return embeddings.squeeze()

    def enroll(self, audio_path: str):
        """Enroll the reference speaker from their first chunk of audio."""
        logger.info(f"Enrolling reference speaker from {audio_path}")
        self.reference_embedding = self._get_embedding(audio_path)
        
    def check_drift(self, audio_path: str) -> float:
        """
        Compare the incoming audio against the enrolled reference embedding.
        Returns the identity drift score (0.0 to 1.0).
        0.0 = Exact match. 1.0 = Completely different speaker.
        """
        if self.reference_embedding is None:
            raise ValueError("No reference speaker enrolled.")
            
        current_embedding = self._get_embedding(audio_path)
        
        similarity = F.cosine_similarity(
            self.reference_embedding, 
            current_embedding, 
            dim=0
        ).item()
        
        # similarity is between -1 and 1. We map it to drift:
        # High similarity (~1.0) -> Drift ~0.0
        # Low similarity (<0.5) -> Drift >0.5
        identity_drift = max(0.0, min(1.0, 1.0 - similarity))
        
        return round(identity_drift, 4)
