# VoxGuard Backend (`voxguard-backend`)

**Team Crackjack — SIH26104 (AI-Powered Real-Time Voice Cloning Detection)**
**Backend Lead:** Shreyas

This repository contains the real-time FastAPI backend service that ingests audio chunks, processes them through ML detection models (`Spectra-AASIST3`), computes smoothed rolling risk scores, and broadcasts live risk updates via WebSockets.

---

## Architecture & End-to-End Pipeline

```
Audio Input (Live Mic / Sliced WAV Chunks)
               │
               ▼
   Audio Slicer (3s Chunks)
               │
               ▼
      ML Analysis Engine (app.ml.analyzer / Spectra-AASIST3)
               │
               ▼
   RollingRiskAggregator (5-Chunk Weighted Window)
               │
               ▼
      Threshold Logic (Low < 0.4 | Medium 0.4–0.7 | High > 0.7)
               │
               ▼
   WebSocket Broadcast (/ws/session) -> Frontend Dashboard & Alert Gates
```

---

## One-Time Model Setup

Run this command locally to pre-cache the **Spectra-AASIST3** model weights from Hugging Face:

```bash
python -c "from transformers import AutoModel; AutoModel.from_pretrained('lab260/Spectra-AASIST3', trust_remote_code=True)"
```

*Note: Model weights must never be committed to Git repositories.*

---

## Configuration: `VOXGUARD_ML_MODE`

The backend supports switching between the real ML model and simulation stub via environment variable:

- **`VOXGUARD_ML_MODE=real`** *(Default)*: Runs real synchronous Spectra-AASIST3 model inference safely off the main event loop thread via `asyncio.to_thread`.
- **`VOXGUARD_ML_MODE=stub`**: Runs simulated score scenario streams for local UI testing without requiring model weights.

> [!WARNING]
> Only `"real"` or `"stub"` are valid values. Any invalid value will immediately raise a `ValueError` configuration error.

---

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
# Default mode (Real ML model)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Stub mode (Development / Testing)
VOXGUARD_ML_MODE=stub uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

---

## Data Contract (Backend $\rightarrow$ Frontend)

Every message streamed over `/ws/session` strictly follows this agreed JSON format:

```json
{
  "chunk_id": "chunk_001",
  "timestamp": "2026-09-10T15:00:00.000000+00:00",
  "chunk_score": 0.12,
  "rolling_risk_score": 0.12,
  "confidence": 0.94,
  "flags": ["synthetic_artifact"],
  "alert_level": "low"
}
```

### Thresholds & Alert Levels:
- `low`: `rolling_risk_score < 0.40` (Safe call — Green)
- `medium`: `0.40 <= rolling_risk_score <= 0.70` (Elevated risk — Yellow)
- `high`: `rolling_risk_score > 0.70` (High risk AI clone / fraud — Red)

---

## Running Automated Verification & Tests

```bash
# Run full automated backend test suite (100% offline)
python -m unittest discover -s tests -p "test_*.py"

# Or using pytest
python -m pytest tests -v
```
