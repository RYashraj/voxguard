# VoxGuard

**AI-powered real-time voice cloning & impersonation detection**  
Smart India Hackathon 2026 · PS ID: SIH26104 · Cyber Security Cell, AICTE  
**Team Crackjack**

---

## Problem

Voice cloning technology can now convincingly impersonate a real person in seconds. Attackers exploit this during live phone calls to trick employees into approving fraudulent transactions or leaking sensitive information. Traditional verification (caller ID, callback, recognising a voice) can no longer reliably catch synthetic audio — and by the time the call ends, the damage is already done.

## Solution

VoxGuard processes call audio **in real time, chunk by chunk, while the call is still active** and produces a continuously updated impersonation risk score. When risk crosses configurable thresholds, the dashboard fires alerts and gates sensitive actions behind secondary verification — before any damage can occur.

---

## Architecture

```
Live / simulated call audio (WAV)
          │
          ▼
 Audio Chunker (pydub / wave)
  ┌───────────────────────────────────────────────┐
  │  3-second sliding window chunks               │
  └───────────────────────────────────────────────┘
          │
          ▼
 Multi-Layer ML Analysis (asyncio.to_thread)
  ┌───────────────────────────────────────────────┐
  │  1. Spectra-AASIST3  — spectral spoof detect  │
  │  2. Prosody Scorer   — pitch/jitter/shimmer   │
  │  3. Identity Tracker — speaker drift / cosine │
  └───────────────────────────────────────────────┘
          │
          ▼
 RollingRiskAggregator
  ┌───────────────────────────────────────────────┐
  │  Linearly-weighted 5-chunk rolling average    │
  │  Thresholds: low <0.4 | medium 0.4–0.7 | high >0.7 │
  └───────────────────────────────────────────────┘
          │
          ▼
 WebSocket Broadcast  (RiskUpdate JSON)
  ┌───────────────────────────────────────────────┐
  │  FastAPI ConnectionManager → all live clients │
  └───────────────────────────────────────────────┘
          │
          ▼
 Next.js Live Dashboard
  ┌───────────────────────────────────────────────┐
  │  Risk gauge · Waveform · Multi-layer chart    │
  │  Alert banner · Identity badge · Chunk log    │
  │  Pre-transaction modal (verification gate)    │
  └───────────────────────────────────────────────┘
          │
          ▼
 SQLite Audit Log (async, non-blocking)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), Vanilla CSS, Recharts, WebSocket hook |
| **Auth** | NextAuth.js with Google OAuth |
| **Backend** | FastAPI (Python 3.12), Uvicorn, WebSockets |
| **ML — Detection** | PyTorch, HuggingFace Transformers (Spectra-AASIST3) |
| **ML — Prosody** | librosa, scipy, numpy |
| **ML — Identity** | Speaker embedding cosine drift tracker |
| **Audio** | pydub, soundfile, wave (stdlib fallback) |
| **Persistence** | SQLite (async, aiosqlite) |
| **Testing** | pytest, pytest-asyncio, httpx |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) ffmpeg on PATH for pydub WAV support

### 1. Backend Setup

```bash
# Create virtual environment and install dependencies
python -m venv venv
.\venv\Scripts\pip install -r backend\requirements.txt

# (Optional) Install prosody/audio deps
.\venv\Scripts\pip install librosa soundfile

# Run backend on port 8000
.\venv\Scripts\uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

### 2. Environment Variables (Backend)

| Variable | Default | Description |
|---|---|---|
| `VOXGUARD_ML_MODE` | `real` | `real` = Spectra-AASIST3 model, `stub` = deterministic test values |
| `SPECTRA_MODEL_PATH` | `lab260/Spectra-AASIST3` | HuggingFace model ID or local path |

### 3. Frontend Setup

```bash
# Install Node dependencies
npm install

# Copy and configure environment
cp .env.example .env.local
# Set NEXT_PUBLIC_RISK_WS_URL=ws://localhost:8000/ws/session
# Set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start frontend dev server on port 3000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 4. Run Tests

```bash
# Full backend test suite (36 tests)
.\venv\Scripts\python -m pytest backend/tests/ -v
```

---

## Data Contract

Every WebSocket message from backend → frontend conforms to this schema (enforced by Pydantic v2):

```json
{
  "chunk_id": "chunk_003",
  "timestamp": "2026-09-17T15:00:00.000000+00:00",
  "chunk_score": 0.82,
  "rolling_risk_score": 0.61,
  "confidence": 0.94,
  "flags": ["synthetic_artifact", "prosody_flatness"],
  "alert_level": "high",
  "prosody_score": 0.74,
  "identity_drift": 0.31,
  "transaction_context": "fund_transfer",
  "known_contact": "contact_001",
  "alert_reason": null
}
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `chunk_id` | `string` | e.g. `"chunk_003"` |
| `timestamp` | `string` | ISO 8601 UTC |
| `chunk_score` | `float [0,1]` | Raw per-chunk spoof score |
| `rolling_risk_score` | `float [0,1]` | Linearly-weighted 5-chunk rolling average |
| `confidence` | `float [0,1]` | Model confidence (0 = unavailable) |
| `flags` | `string[]` | Active detection flags |
| `alert_level` | `"low"\|"medium"\|"high"` | Threshold-derived alert level |
| `prosody_score` | `float\|null` | Prosody anomaly (pitch/jitter/shimmer), null if unavailable |
| `identity_drift` | `float\|null` | Speaker cosine drift from session baseline, null if unavailable |
| `transaction_context` | `string\|null` | Business context passed from frontend |
| `known_contact` | `string\|null` | Caller ID passed from frontend |
| `alert_reason` | `string\|null` | Human-readable reason for high alert |

**Known flag values:**

| Flag | Trigger |
|---|---|
| `synthetic_artifact` | `chunk_score > 0.70` |
| `prosody_flatness` | `chunk_score > 0.40` |
| `spectral_discontinuity` | Spectral gap detected |
| `silent_audio` | RMS energy < 0.001 |
| `short_audio` | Audio < 4s (padded automatically) |
| `model_unavailable` | Spectra-AASIST3 failed to load |
| `prosody_error` | librosa/prosody pipeline failed |
| `identity_error` | Speaker tracker failed |
| `inference_error` | PyTorch forward pass error |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/contacts` | List enrolled contacts |
| `GET` | `/contract` | Example RiskUpdate payload |
| `POST` | `/api/v1/session/start` | Start call simulation |
| `POST` | `/api/v1/session/stop` | Stop active simulation |
| `GET` | `/api/v1/sessions` | List all past sessions |
| `GET` | `/api/v1/sessions/{id}/history` | Full chunk history for a session |
| `WS` | `/ws/session` | Real-time RiskUpdate stream |
| `GET` | `/demo` | Standalone HTML demo dashboard |
| `GET` | `/docs` | Swagger / OpenAPI |

---

## Risk Scoring

### Rolling Risk Formula

```
rolling_score = Σ(weight_i × score_i) / Σ(weight_i)

weights = [1, 2, 3, 4, 5]  (most recent chunk = weight 5)
window  = last 5 chunks
```

### Alert Thresholds

| Alert Level | Rolling Score Range |
|---|---|
| 🟢 `low` | < 0.40 |
| 🟡 `medium` | 0.40 – 0.70 |
| 🔴 `high` | > 0.70 |

Thresholds are configurable via `RollingRiskAggregator(low_threshold, high_threshold)`.

---

## Verification Results (Final Integration Day)

| Test suite | Tests | Result |
|---|---|---|
| Aggregator | 6 | ✅ 6/6 |
| Contract | 3 | ✅ 3/3 |
| DB Logging | 6 | ✅ 6/6 |
| Health/API | 4 | ✅ 4/4 |
| Sprint Integration | 4 | ✅ 4/4 |
| ML Integration | 6 | ✅ 6/6 |
| ML Stub | 3 | ✅ 3/3 |
| Simulator | 2 | ✅ 2/2 |
| WebSocket | 2 | ✅ 2/2 |
| **Total** | **36** | ✅ **36/36 PASSED** |

E2E sprint dry run: **3 scenarios × 6 chunks** verified. Avg ML latency: **0.15 ms/chunk**.

---

## Team

| Name | Track |
|---|---|
| Yashraj | Integration, git, docs |
| Shreyas | Backend / real-time API |
| Hetvi, Nandini | ML pipeline (detection + risk scoring) |
| Meet, Devikrishna | Frontend / live dashboard |
