# VoxGuard Real Model Smoke Test Report (Spectra-AASIST3)

This report documents the live end-to-end smoke test of the **Spectra-AASIST3** deepfake voice detection model integrated into the VoxGuard real-time streaming backend pipeline (`VOXGUARD_ML_MODE=real`).

---

## 1. Prerequisites & Environment Setup

- **Python Version**: Python 3.11 (`.venv`)
- **Git Branch**: `feature/ml-backend-integration`
- **Environment Variable**: `VOXGUARD_ML_MODE=real`
- **Model Checkpoints**: `lab260/Spectra-AASIST3` & `facebook/wav2vec2-xls-r-300m` pre-cached in HuggingFace Hub cache.

### Execution Commands:

```powershell
# 1. Activate Python 3.11 virtual environment
cd d:\VoxGuard\voxguard-github-integration\backend
.\.venv\Scripts\Activate.ps1

# 2. Set Real Model Mode
$env:VOXGUARD_ML_MODE = "real"

# 3. Start Backend Uvicorn Server
uvicorn app.main:app --reload

# 4. Run Pytest Test Suite
pytest
```

---

## 2. Model Loading & Verification Result

- **Model Target**: `lab260/Spectra-AASIST3`
- **Base Architecture**: `facebook/wav2vec2-xls-r-300m` + `SpectraAASIST3` graph attention / KAN classifier
- **Loader Mechanism**: `PyTorchModelHubMixin` fallback
- **Model Load Status**: `is_loaded: True` (`load_error: None`)
- **Direct `analyze_chunk()` Smoke Test Output**:
  - Sample File: `team_resources/for_ml/sample_chunks/chunk_001.wav`
  - `chunk_score`: `0.0497`
  - `confidence`: `0.9006`
  - `flags`: `["short_audio"]`

---

## 3. Live Simulation & WebSocket Streaming Verification

- **Trigger Endpoint**: `POST /start-simulation` (`scenario`: `"suspicious"`, `delay_sec`: `0.5`)
- **Captured Session ID**: `session_5f088d84`
- **WebSocket Endpoint**: `ws://127.0.0.1:8000/ws/session`

### Streamed RiskUpdate Messages Summary:

| Chunk ID | Timestamp | Chunk Score | Rolling Risk | Confidence | Flags | Alert Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `chunk_001` | `2026-09-11T09:58:16.119332+00:00` | `0.0497` | `0.0497` | `0.9006` | `["short_audio"]` | `low` |
| `chunk_002` | `2026-09-11T09:58:19.455256+00:00` | `0.0369` | `0.0412` | `0.9261` | `["short_audio"]` | `low` |
| `chunk_003` | `2026-09-11T09:58:22.320432+00:00` | `0.0369` | `0.0390` | `0.9261` | `["short_audio"]` | `low` |
| `chunk_004` | `2026-09-11T09:58:25.317551+00:00` | `0.0369` | `0.0382` | `0.9261` | `["short_audio"]` | `low` |

- **Contract Integrity**: Every streamed message matched the strict 7-field contract (`chunk_id`, `timestamp`, `chunk_score`, `rolling_risk_score`, `confidence`, `flags`, `alert_level`).
- **Error Flags Check**: Verified **0** occurrences of `model_unavailable` or `inference_error` during live execution.

---

## 4. Session History & Latency Summary

Retrieved via `GET /sessions/session_5f088d84/history`:

- **Chunk 1 (Cold Start)**: `24840.85 ms` (Includes initial model instantiation & tensor allocation)
- **Chunk 2 (Warm)**: `2807.05 ms`
- **Chunk 3 (Warm)**: `2338.58 ms`
- **Chunk 4 (Warm)**: `2484.58 ms`
- **Average Warm Inference Latency**: `~2543.4 ms` per ~4s audio chunk on CPU.
- **Persistence Verification**: 100% of chunk records, scores, timestamps, and per-chunk latency metrics were successfully logged to SQLite (`voxguard.db`).

---

## 5. Limitations

- **CPU Inference Speed**: Warm CPU inference latency per chunk averages ~2.5 seconds. For ultra-low-latency production deployment (<500ms), GPU acceleration (CUDA) or ONNX Runtime export is recommended.
- **Single Clip Evaluation**: This smoke test validates system integration, pipeline contracts, and model loading. It does **not** constitute a broad model accuracy benchmark across diverse datasets.

---

## 6. Pre-Demo Checklist

- [x] Python 3.11 virtual environment initialized with all dependencies installed.
- [x] `VOXGUARD_ML_MODE=real` environment variable verified.
- [x] `Spectra-AASIST3` and `wav2vec2-xls-r-300m` model weights pre-cached locally.
- [x] Backend server running on `http://127.0.0.1:8000`.
- [x] Real-time WebSocket streaming verified at `ws://127.0.0.1:8000/ws/session`.
- [x] `/sessions/{session_id}/history` REST persistence verified.
- [x] Complete 30-test backend suite passing (`30 passed`).
