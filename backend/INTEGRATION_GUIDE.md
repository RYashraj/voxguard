# VoxGuard Backend — API & Integration Guide

> **Audience:** Frontend engineers, ML engineers, and anyone integrating with the VoxGuard backend.  
> **Status:** Integration-complete, pitch-ready — `develop` branch, SIH 2026 Final Day.

---

## Quick Start

```bash
# From repo root
.\venv\Scripts\uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Backend boots and logs:
```
Initializing VoxGuard Backend...
Default demo audio ready at: backend/data/sample_calls/demo_call.wav
SQLite session database ready.
Pre-loading SpectraAASISTDetector ML model weights...
```

---

## Environment Variables

| Variable | Default | Effect |
|---|---|---|
| `VOXGUARD_ML_MODE` | `real` | `real` = Spectra-AASIST3 inference; `stub` = deterministic test scores |
| `SPECTRA_MODEL_PATH` | `lab260/Spectra-AASIST3` | HuggingFace repo ID or local path to model weights |

Set `VOXGUARD_ML_MODE=stub` for fast local dev without GPU/model download.

---

## WebSocket Contract

Connect to: `ws://localhost:8000/ws/session`

### Handshake (server → client, on connect)
```json
{
  "event": "connected",
  "message": "Connected to VoxGuard real-time stream",
  "session_id": "default"
}
```

### RiskUpdate (server → client, every chunk)
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

### Pre-Transaction Warning (server → client, high-risk gate)
```json
{
  "event": "pretransaction_warning",
  "session_id": "session_abc123",
  "reason": "High voice impersonation risk detected during active session",
  "recommended_actions": ["Call-back Verification", "Multi-Factor Authentication (MFA)", "Escalate to Supervisor"],
  "timestamp": "2026-09-17T15:00:03.000000+00:00"
}
```

### Field Reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `chunk_id` | `string` | ✅ | `chunk_001` ... `chunk_N` |
| `timestamp` | `string` | ✅ | ISO 8601 UTC |
| `chunk_score` | `float [0,1]` | ✅ | Raw per-chunk spoof score |
| `rolling_risk_score` | `float [0,1]` | ✅ | Smoothed 5-chunk weighted rolling avg |
| `confidence` | `float [0,1]` | ✅ | 0.0 when model unavailable |
| `flags` | `string[]` | ✅ | May be empty `[]` |
| `alert_level` | `"low"\|"medium"\|"high"` | ✅ | Derived from rolling score |
| `prosody_score` | `float\|null` | ❌ | null if librosa unavailable |
| `identity_drift` | `float\|null` | ❌ | null if tracker unavailable |
| `transaction_context` | `string\|null` | ❌ | Forwarded from SimulationRequest |
| `known_contact` | `string\|null` | ❌ | Forwarded from SimulationRequest |
| `alert_reason` | `string\|null` | ❌ | Optional human-readable reason |

**Frontend filter:** Only treat messages as `RiskUpdate` if `chunk_id`, `rolling_risk_score`, and `alert_level` are all present. All other messages (handshake, control, warning events) are non-data and must be handled separately.

---

## REST Endpoints

### Health

```
GET /health
GET /api/v1/health
```

**Response:**
```json
{ "status": "ok" }
```

---

### Contacts

```
GET /api/v1/contacts
GET /contacts
```

**Response:**
```json
{
  "total_contacts": 6,
  "contacts": [
    {
      "id": "contact_001",
      "name": "Rajesh Sharma",
      "role": "Chief Financial Officer (CFO)",
      "phone_number": "+91 98765 43210",
      "enrolled": true,
      "risk_profile": "low"
    }
  ]
}
```

---

### Start Simulation

```
POST /api/v1/session/start
POST /api/v1/simulation/start
POST /start-simulation
```

**Request body (all fields optional):**
```json
{
  "caller_id": "contact_001",
  "caller_name": "Rajesh Sharma",
  "transaction_context": "fund_transfer",
  "file_path": null,
  "chunk_duration_sec": 3.0,
  "delay_sec": 3.0,
  "scenario": "gradual_escalation"
}
```

| Field | Type | Default | Options |
|---|---|---|---|
| `caller_id` | `string` | `"unknown"` | Any contact ID or `"unknown"` |
| `transaction_context` | `string` | `"default"` | `"fund_transfer"`, `"information_request"`, `"routine"`, `"default"` |
| `file_path` | `string\|null` | `null` | Path to WAV file; null = demo audio |
| `chunk_duration_sec` | `float` | `3.0` | 0.5 – 10.0 |
| `delay_sec` | `float` | `3.0` | 0.01 – 10.0 |
| `scenario` | `string` | `"gradual_escalation"` | `"default"`, `"clean"`, `"suspicious"`, `"gradual_escalation"` |

**Response:**
```json
{
  "status": "started",
  "message": "Simulation running for scenario 'gradual_escalation' ...",
  "session_id": "session_abc12345",
  "caller_id": "contact_001",
  "transaction_context": "fund_transfer"
}
```

---

### Stop Simulation

```
POST /api/v1/session/stop
POST /api/v1/simulation/stop
POST /stop-simulation
```

**Response:**
```json
{
  "status": "stopped",
  "message": "Simulation stopped successfully",
  "session_id": "session_abc12345"
}
```

---

### Session History

```
GET /api/v1/sessions                          — list all sessions
GET /api/v1/sessions/{session_id}/history     — full chunk log + stats
```

**List response:**
```json
{
  "total_sessions": 3,
  "sessions": [
    {
      "session_id": "session_abc12345",
      "total_chunks": 6,
      "avg_latency_ms": 0.15,
      "peak_risk_score": 0.89,
      "final_alert_level": "high"
    }
  ]
}
```

**History response:**
```json
{
  "session_id": "session_abc12345",
  "total_chunks": 6,
  "stats": {
    "avg_latency_ms": 0.15,
    "peak_risk_score": 0.89,
    "final_alert_level": "high"
  },
  "history": [
    {
      "chunk_id": "chunk_001",
      "timestamp": "...",
      "chunk_score": 0.82,
      "rolling_risk_score": 0.82,
      "confidence": 0.94,
      "flags": ["synthetic_artifact"],
      "alert_level": "high",
      "inference_latency_ms": 0.14
    }
  ]
}
```

---

## Risk Scoring Formula

> ⚠️ **Do not modify thresholds without flagging to the full team.**

```
rolling_score = Σ(i × score_i) / Σ(i)
                for i in 1..min(n, 5)   [oldest=1, most recent=5]

alert_level:
  rolling_score < 0.40  →  "low"
  rolling_score ≤ 0.70  →  "medium"
  rolling_score > 0.70  →  "high"
```

The window size and thresholds are set in `RollingRiskAggregator.__init__()` in  
`backend/app/core/aggregator.py`. The default is `window_size=5`, `low_threshold=0.4`, `high_threshold=0.7`.

---

## ML Pipeline: Detection Layers

### 1. Spectra-AASIST3 (Primary)
- **Model:** `lab260/Spectra-AASIST3` (HuggingFace)
- **Input:** 16kHz mono float32 numpy array, minimum 64600 samples (~4s)
- **Output:** spoof probability (Class 0 = spoof, Class 1 = bona-fide)
- **Concurrency:** Protected by `threading.Lock` (singleton)
- **Fallback:** `chunk_score=0.5`, `confidence=0.0`, flag: `model_unavailable`

### 2. Prosody Scorer
- **Module:** `ml/prosody_score.py`
- **Features:** Pitch mean/std, jitter, shimmer, HNR via librosa
- **Output:** `prosody_score` (0–1 normalised)
- **Fallback:** `prosody_score=null`, flag: `prosody_error`

### 3. Identity Tracker
- **Module:** `ml/identity_tracker.py` + `ml/speaker_test.py`
- **Method:** Cosine similarity drift vs session-baseline speaker embedding
- **Output:** `identity_drift` (0–1)
- **Fallback:** `identity_drift=null`, flag: `identity_error`

All secondary signals are isolated in `try/except` blocks. Failure of any single layer never crashes the stream.

---

## Known Limitations (Demo Day)

| Limitation | Impact | Workaround |
|---|---|---|
| Spectra-AASIST3 requires internet or local weights | No real-time spoof score on air-gapped machines | Set `VOXGUARD_ML_MODE=stub` for demo |
| Windows WDAC policy may block `torch/shm.dll` | PyTorch multi-process GPU sharing disabled | Single-process CPU inference still works |
| ffmpeg not installed | pydub falls back to stdlib `wave` module | WAV files work; MP3/other formats don't |
| Identity tracker requires first-chunk enrollment | `identity_drift=null` for first chunk | Expected — tracker initialises on chunk 1 |
| Transparency page uses placeholder accuracy data | Table shows indicative values, not real eval | ML team to replace `data/transparency.json` |

---

## Running Tests

```bash
# All 36 backend tests
.\venv\Scripts\python -m pytest backend/tests/ -v

# End-to-end sprint verification (no server needed)
.\venv\Scripts\python backend/scripts/verify_day6_sprint.py

# Day 5 comprehensive verification
.\venv\Scripts\python backend/scripts/verify_day5.py
```

**Expected result:** `36 passed` in ~3 minutes.
