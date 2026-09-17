# VoxGuard API Contract Documentation

This document defines the REST endpoints, WebSocket streaming protocol, data contracts, and error handling for VoxGuard (SIH26104).

---

## 1. Local Development Base URLs & Interactive Documentation
- **Backend API Base URL**: `http://127.0.0.1:8000` (or `http://localhost:8000`)
- **WebSocket Connection URL**: `ws://127.0.0.1:8000/ws/session` (or `ws://127.0.0.1:8000/ws/session/{session_id}`)
- **Interactive OpenAPI (Swagger) UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Built-in Demo Dashboard**: [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)

---

## 2. Core Seven-Field `RiskUpdate` Contract

Every streamed WebSocket chunk payload adheres to the stable seven-field contract:

```json
{
  "chunk_id": "chunk_001",
  "timestamp": "2026-09-18T00:00:00.000000+00:00",
  "chunk_score": 0.0497,
  "rolling_risk_score": 0.0497,
  "confidence": 0.9006,
  "flags": [
    "short_audio"
  ],
  "alert_level": "low"
}
```

### Field Definitions
| Field | Type | Description |
|---|---|---|
| `chunk_id` | `string` | Unique identifier for the chunk (e.g., `"chunk_001"`) |
| `timestamp` | `string` | ISO 8601 UTC timestamp of chunk analysis |
| `chunk_score` | `number` (0.0 – 1.0) | Raw acoustic/impersonation risk score from Spectra-AASIST3 |
| `rolling_risk_score` | `number` (0.0 – 1.0) | Smoothed rolling risk score over recent 5 chunks |
| `confidence` | `number` (0.0 – 1.0) | Model confidence metric for the chunk analysis |
| `flags` | `array of strings` | Filtered public status flags (e.g. `["synthetic_artifact"]`, `["short_audio"]`, `["model_unavailable"]`) |
| `alert_level` | `"low"` \| `"medium"` \| `"high"` | Threat level: `low` (<0.40), `medium` (0.40–0.70), `high` (>0.70) |

### Optional Additive `advisory` Object
When streaming live simulation updates, an additive `advisory` object is attached to the payload:

```json
{
  "chunk_id": "chunk_001",
  "timestamp": "2026-09-18T00:00:00.000000+00:00",
  "chunk_score": 0.0497,
  "rolling_risk_score": 0.0497,
  "confidence": 0.9006,
  "flags": [
    "short_audio"
  ],
  "alert_level": "low",
  "advisory": {
    "recommendation": "continue_with_caution",
    "reason_codes": [
      "normal_call_flow"
    ],
    "user_message": "Low acoustic risk detected. Proceed with caution.",
    "requires_user_confirmation": true
  }
}
```

- **Valid Recommendations**:
  - `"continue_with_caution"`: Low risk call flow or verified contact.
  - `"pause_and_verify"`: Medium risk, unknown caller context, or sensitive transaction (OTP/PIN/fund transfer).
  - `"block_and_report"`: High acoustic risk / synthetic audio artifact detected.
- **Backward Compatibility Guarantee**: Consumers reading only the seven core fields ignore the `advisory` key and remain 100% compatible.

---

## 3. WebSocket Protocol (`WS /ws/session`)

### Connection Endpoint
`ws://127.0.0.1:8000/ws/session` or `ws://127.0.0.1:8000/ws/session/{session_id}`

### Connection Handshake Message
Immediately upon connecting, the server sends a JSON confirmation message:

```json
{
  "event": "connected",
  "message": "Connected to VoxGuard real-time stream",
  "session_id": "session_cfb99113"
}
```

---

## 4. REST Endpoints

### 1. Health Check
- **HTTP Method**: `GET`
- **Path**: `/health`
- **Response** (200 OK):
  ```json
  {
    "status": "ok"
  }
  ```

### 2. Start Simulation
- **HTTP Method**: `POST`
- **Path**: `/start-simulation` (Alias: `/api/simulation/start`)
- **Request Body** (`SimulationRequest`, optional):
  ```json
  {
    "file_path": null,
    "chunk_duration_sec": 3.0,
    "delay_sec": 1.0,
    "scenario": "gradual_escalation",
    "reference_audio_path": null,
    "context": {
      "caller_context": "known_contact",
      "transaction_type": "other",
      "transaction_amount": null,
      "user_confirmation_required": true
    }
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "status": "started",
    "message": "Simulation running for scenario 'gradual_escalation' at 1.0s interval",
    "session_id": "session_cfb99113",
    "total_chunks": null
  }
  ```
- **Errors**: `500 Internal Server Error` (`{"detail": "Failed to start simulation."}`)

### 3. Stop Simulation
- **HTTP Method**: `POST`
- **Path**: `/stop-simulation` (Alias: `/api/simulation/stop`)
- **Response** (200 OK):
  ```json
  {
    "status": "stopped",
    "message": "Simulation stopped successfully",
    "session_id": "session_cfb99113"
  }
  ```

### 4. Update Session Context
- **HTTP Method**: `POST`
- **Path**: `/sessions/{session_id}/context` (Alias: `/api/sessions/{session_id}/context`)
- **Request Body** (`SimulationContext`):
  ```json
  {
    "caller_context": "unknown_contact",
    "transaction_type": "otp_or_pin_request",
    "transaction_amount": 500.0,
    "user_confirmation_required": true
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "session_id": "session_cfb99113",
    "status": "updated",
    "context": {
      "caller_context": "unknown_contact",
      "transaction_type": "otp_or_pin_request",
      "transaction_amount": 500.0,
      "user_confirmation_required": true
    }
  }
  ```
- **Errors**: `404 Not Found` (`{"detail": "Session 'session_xyz' not found or inactive."}`)

### 5. Get Session Context
- **HTTP Method**: `GET`
- **Path**: `/sessions/{session_id}/context` (Alias: `/api/sessions/{session_id}/context`)
- **Response** (200 OK):
  ```json
  {
    "session_id": "session_cfb99113",
    "context": {
      "caller_context": "unknown_contact",
      "transaction_type": "otp_or_pin_request",
      "transaction_amount": 500.0,
      "user_confirmation_required": true
    }
  }
  ```
- **Errors**: `404 Not Found`

### 6. Get Session History
- **HTTP Method**: `GET`
- **Path**: `/sessions/{session_id}/history` (Alias: `/api/sessions/{session_id}/history`)
- **Response** (200 OK):
  ```json
  {
    "session_id": "session_cfb99113",
    "total_chunks": 6,
    "history": [
      {
        "session_id": "session_cfb99113",
        "chunk_id": "chunk_001",
        "timestamp": "2026-09-18T00:00:00Z",
        "chunk_score": 0.0497,
        "rolling_risk_score": 0.0497,
        "confidence": 0.9006,
        "flags": ["short_audio"],
        "alert_level": "low",
        "inference_latency_ms": 12.5
      }
    ]
  }
  ```
- **Privacy Guarantee**: History response excludes raw audio, file paths, caller PII, banking context, advisory objects, and speaker embeddings.
- **Errors**: `404 Not Found` (`{"detail": "No history found for session 'session_xyz'"}`)

---

## 5. Model Execution Modes & Fault Tolerance

- **Real ML Mode** (`VOXGUARD_ML_MODE=real`, default): Runs real Spectra-AASIST3 model inference using PyTorch and Hugging Face weights.
- **Stub Mode** (`VOXGUARD_ML_MODE=stub`): Runs deterministic simulated chunk score trajectories for offline testing.
- **Safe Fallback Behaviour**: If real ML model loading or execution encounters an error, the backend safely returns fallback indicators (`chunk_score=0.5`, `confidence=0.0`, `flags=["inference_error"]` or `flags=["model_unavailable"]`) to keep the real-time stream active without crashing.
