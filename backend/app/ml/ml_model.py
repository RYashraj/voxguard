import io
import os
import wave
import math
import struct
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoxGuard.ML")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SAMPLE_RATE = 16000
REQUIRED_SAMPLES = 64600  # ~4 seconds required by Spectra-AASIST3


def parse_audio_bytes(audio_bytes: bytes):
    """
    Parses 16kHz WAV audio bytes and returns (audio_data, rms_energy, flags).
    Handles empty, corrupted, multi-channel, non-16kHz, and silent/short audio safely.
    Does NOT require model initialization.
    """
    if not audio_bytes or len(audio_bytes) < 44:
        return None, 0.0, ["invalid_audio"]

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            sr = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            n_frames = wav.getnframes()

            if n_frames == 0:
                return None, 0.0, ["invalid_audio"]

            frames = wav.readframes(n_frames)

        if sample_width != 2:
            return None, 0.0, ["invalid_audio"]

        total_samples = len(frames) // 2
        if total_samples == 0:
            return None, 0.0, ["invalid_audio"]

        if HAS_NUMPY:
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            if channels > 1:
                audio = audio.reshape(-1, channels).mean(axis=1)

            if sr != SAMPLE_RATE:
                try:
                    import torch
                    import torchaudio
                    waveform = torch.tensor(audio).unsqueeze(0)
                    waveform = torchaudio.functional.resample(waveform, sr, SAMPLE_RATE)
                    audio = waveform.squeeze(0).numpy()
                except Exception:
                    old_indices = np.linspace(0, len(audio) - 1, num=len(audio))
                    new_len = int(len(audio) * SAMPLE_RATE / sr)
                    new_indices = np.linspace(0, len(audio) - 1, num=new_len)
                    audio = np.interp(new_indices, old_indices, audio).astype(np.float32)

            rms_energy = float(np.sqrt(np.mean(audio ** 2)))
            flags = []

            if rms_energy < 0.001:
                flags.append("silent_audio")

            if len(audio) < REQUIRED_SAMPLES:
                flags.append("short_audio")
                repeats = int(np.ceil(REQUIRED_SAMPLES / len(audio)))
                audio = np.tile(audio, repeats)[:REQUIRED_SAMPLES]

            return audio, rms_energy, flags

        else:
            raw_samples = struct.unpack(f"<{total_samples}h", frames)
            if channels > 1:
                mono_samples = [
                    sum(raw_samples[i:i + channels]) / channels
                    for i in range(0, total_samples, channels)
                ]
            else:
                mono_samples = list(raw_samples)

            audio = [s / 32768.0 for s in mono_samples]
            if not audio:
                return None, 0.0, ["invalid_audio"]

            sq_sum = sum(s * s for s in audio)
            rms_energy = math.sqrt(sq_sum / len(audio))
            flags = []

            if rms_energy < 0.001:
                flags.append("silent_audio")

            if len(audio) < REQUIRED_SAMPLES:
                flags.append("short_audio")
                repeats = int(math.ceil(REQUIRED_SAMPLES / len(audio)))
                audio = (audio * repeats)[:REQUIRED_SAMPLES]

            return audio, rms_energy, flags

    except Exception as e:
        logger.debug(f"WAV parse error: {e}")
        return None, 0.0, ["invalid_audio"]


class SpectraAASISTDetector:
    """
    Thread-safe Singleton detector wrapper for Spectra-AASIST3 spoof detection.
    Loads model weights once upon initialization and handles inference safely with concurrency lock.
    """
    def __init__(self, model_name_or_path: str = None):
        self.model_name = model_name_or_path or os.getenv(
            "SPECTRA_MODEL_PATH", "lab260/Spectra-AASIST3"
        )
        self.model = None
        self.is_loaded = False
        self.load_error = None
        self._inference_lock = threading.Lock()
        self._load_model()

    def _load_model(self):
        try:
            import torch
            from transformers import AutoModel

            logger.info("Loading Spectra-AASIST3 model...")
            try:
                self.model = AutoModel.from_pretrained(
                    self.model_name, trust_remote_code=True
                )
            except Exception as auto_err:
                logger.info("AutoModel.from_pretrained failed (%s), loading SpectraAASIST3 via PyTorchModelHubMixin...", auto_err)
                import sys
                import importlib.util
                from huggingface_hub import hf_hub_download

                model_py_path = hf_hub_download(repo_id=self.model_name, filename="model.py")
                spec = importlib.util.spec_from_file_location("spectra_model", model_py_path)
                spectra_module = importlib.util.module_from_spec(spec)
                sys.modules["spectra_model"] = spectra_module
                spec.loader.exec_module(spectra_module)

                SpectraAASIST3 = getattr(spectra_module, "SpectraAASIST3")
                self.model = SpectraAASIST3.from_pretrained(self.model_name)

            self.model.eval()
            self.is_loaded = True
            logger.info("Spectra-AASIST3 model successfully loaded.")
        except Exception as e:
            self.is_loaded = False
            err_type = type(e).__name__
            self.load_error = err_type
            logger.error("model_load_error: Spectra-AASIST3 model failed to load (%s)", err_type)

    def predict_parsed(self, audio, rms_energy: float, flags: list) -> dict:
        """
        Runs model inference on pre-parsed, valid, non-silent audio.
        Uses _inference_lock to prevent simultaneous concurrent forward passes on shared model tensors.
        Spectra-AASIST3 Class Mapping:
          Class 0 = Spoof / AI-generated (high chunk_score)
          Class 1 = Bona-fide / Human (low chunk_score)
        """
        if not self.is_loaded:
            active_flags = sorted(list(set(flags + ["model_unavailable"])))
            return {
                "chunk_score": 0.5,
                "confidence": 0.0,
                "flags": active_flags
            }

        try:
            import torch
            waveform = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)

            # Concurrency Guard: Protect shared model forward pass from race conditions
            with self._inference_lock:
                with torch.no_grad():
                    output = self.model(waveform)
                    logits = output.logits if hasattr(output, "logits") else output
                    probs = torch.softmax(logits, dim=-1)[0]

            # CRITICAL CORRECTED MODEL MAPPING:
            # Class 0 = Spoof / Fake, Class 1 = Bona-fide / Human
            spoof_prob = float(probs[0].item())
            chunk_score = round(max(0.0, min(1.0, spoof_prob)), 4)

            # Calculate confidence score
            raw_conf = float(abs(spoof_prob - 0.5) * 2)
            confidence = round(max(0.70, min(0.99, raw_conf)), 4)

            if chunk_score > 0.70:
                flags.append("synthetic_artifact")
            elif chunk_score > 0.40:
                flags.append("prosody_flatness")

            return {
                "chunk_score": chunk_score,
                "confidence": confidence,
                "flags": sorted(list(set(flags)))
            }
        except Exception as e:
            logger.error("Inference execution error: %s", type(e).__name__)
            return {
                "chunk_score": 0.5,
                "confidence": 0.0,
                "flags": sorted(list(set(flags + ["inference_error"])))
            }


# Thread-safe Singleton model instance
_MODEL_INSTANCE = None
_MODEL_LOCK = threading.Lock()


def get_detector() -> SpectraAASISTDetector:
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        with _MODEL_LOCK:
            if _MODEL_INSTANCE is None:
                _MODEL_INSTANCE = SpectraAASISTDetector()
    return _MODEL_INSTANCE


def analyze_chunk(audio_bytes: bytes) -> dict:
    """
    Standard interface function expected by backend stream processor.
    Validates audio BEFORE calling get_detector() or initializing the model.
    """
    audio, rms_energy, flags = parse_audio_bytes(audio_bytes)

    if "invalid_audio" in flags:
        return {
            "chunk_score": 0.5,
            "confidence": 0.0,
            "flags": ["invalid_audio"]
        }

    if "silent_audio" in flags:
        return {
            "chunk_score": 0.5,
            "confidence": 0.1,
            "flags": sorted(list(set(flags)))
        }

    detector = get_detector()
    return detector.predict_parsed(audio, rms_energy, flags)
