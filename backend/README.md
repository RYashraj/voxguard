# VoxGuard Backend (`voxguard-backend`)

**Team Crackjack — SIH26104 (AI-Powered Real-Time Voice Cloning Detection)**
**Backend Lead:** Shreyas

This repository contains the real-time FastAPI backend service that ingests audio chunks, processes them through ML detection models, computes smoothed rolling risk scores, and broadcasts live risk updates via WebSockets.

---

## Architecture & End-to-End Pipeline

```
Audio Input (Live Mic / Sliced WAV Chunks)
               │
               ▼
   Audio Slicer (2–4s Chunks)
               │
               ▼
      ML Analysis Engine (analyze_chunk_stub / AASIST)
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

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
# Option A: via uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option B: directly via python
python main.py
```
The server will start at `http://localhost:8000` (Interactive Swagger docs available at `http://localhost:8000/docs`).

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check endpoint (Returns `{"status": "ok"}`) |
| `GET` | `/contract` | Returns an example JSON of the strict contract |
| `WS` | `/ws/session` or `/ws/session/{session_id}` | WebSocket endpoint for live real-time risk streaming |
| `POST` | `/start-simulation` | Starts the Call Simulator (slices audio, runs ML stub, aggregates rolling score, and streams over WebSocket) |
| `POST` | `/stop-simulation` | Stops the running call simulation |

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
- `medium`: `0.40 <= rolling_risk_score <= 0.70` (Elevated risk, monitor closely — Yellow)
- `high`: `rolling_risk_score > 0.70` (High risk AI clone / fraud — Red)

---

## Running Verification & Tests

```bash
# Run full automated test suite (18 tests passing)
python -m pytest backend/tests -v

# Run live Day 3 & Day 4 end-to-end verification
python backend/scripts/verify_day3_day4.py
```
