# VoxGuard Backend (`voxguard-backend`)

**Team Crackjack — SIH26104 (AI-Powered Real-Time Voice Cloning Detection)**
**Backend Lead:** Shreyas

This repository contains the real-time FastAPI backend service that ingests audio chunks, processes them through ML detection models (`Spectra-AASIST3`), computes smoothed rolling risk scores, persists session history in SQLite, and broadcasts live risk updates via WebSockets.

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
   SQLite Session Logger (chunk_history + latency) ◄── non-blocking
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

## Configuration & Environment Variables

- **`VOXGUARD_ML_MODE=real`** *(Default)*: Runs real synchronous Spectra-AASIST3 model inference safely off the main event loop thread via `asyncio.to_thread`.
- **`VOXGUARD_ML_MODE=stub`**: Runs simulated score scenario streams for local UI testing without requiring model weights.
- **`VOXGUARD_DB_PATH`**: Configures the local SQLite database path. Defaults to source-file relative path `backend/data/voxguard.db`.

---

## Database & Session History Logging

Every processed audio chunk is automatically persisted into a local SQLite database table (`chunk_history`) with:
- `session_id`, `chunk_id`, `timestamp`
- `chunk_score`, `rolling_risk_score`, `confidence`
- `flags` (stored as JSON array)
- `alert_level` (`low` | `medium` | `high`)
- `inference_latency_ms` (exact ML inference execution time in milliseconds)

> [!NOTE]
> Database operations are executed asynchronously off the main event loop (`asyncio.to_thread`). Database errors log safe server-side warnings and **never** crash or interrupt WebSocket streaming.

### Resetting the Database
To reset the session history database:
```bash
# Simply remove the database file
rm backend/data/voxguard.db
```
The database and table schema will be recreated automatically on the next request or server startup.

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check endpoint (Returns `{"status": "ok"}`) |
| `GET` | `/contract` | Returns an example JSON of the strict contract |
| `GET` | `/sessions/{session_id}/history` | Returns chronological chunk history for a specific call session |
| `WS` | `/ws/session` or `/ws/session/{session_id}` | WebSocket endpoint for live real-time risk streaming |
| `POST` | `/start-simulation` | Starts Call Simulator |
| `POST` | `/stop-simulation` | Stops running call simulation |

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

---

## Running Automated Verification & Tests

```bash
# Run full automated backend test suite (100% offline)
python -m unittest discover -s tests -p "test_*.py"

# Or using pytest
python -m pytest tests -v
```
