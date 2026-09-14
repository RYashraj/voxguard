# VoxGuard Backend API Cheatsheet (For Frontend Team)

Base URL: `http://localhost:8000`  
WebSocket: `ws://localhost:8000/ws/session`

---

## 1. Real-Time Streaming

### `WS /ws/session` (or `/ws/session/{session_id}`)
Connect via standard WebSocket.
- **On Open**: Receives `{"event": "connected", "message": "...", "session_id": "..."}`
- **During Stream**: Receives `RiskUpdate` JSON message for every 3-second audio chunk:
  ```json
  {
    "chunk_id": "chunk_001",
    "timestamp": "2026-09-14T10:15:00.000000+00:00",
    "chunk_score": 0.1245,
    "rolling_risk_score": 0.1245,
    "confidence": 0.9230,
    "flags": [],
    "alert_level": "low"
  }
  ```

---

## 2. Simulation & Call Control

### `POST /start-simulation` (or `/api/simulation/start`)
Triggers the Call Simulator to slice audio and broadcast risk updates live.

**Request Body (JSON):**
```json
{
  "chunk_duration_sec": 3.0,
  "delay_sec": 2.0,
  "scenario": "gradual_escalation"
}
```
*Allowed Scenarios*:
- `"gradual_escalation"`: Normal speech transitioning to AI voice clone.
- `"clean"`: 100% human speech (Always Low Alert).
- `"suspicious"`: Instant high-risk deepfake attack call.

**Response (200 OK):**
```json
{
  "status": "started",
  "message": "Simulation running for scenario 'gradual_escalation' at 2.0s interval",
  "session_id": "session_5f088d84"
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/start-simulation \
  -H "Content-Type: application/json" \
  -d '{"scenario": "gradual_escalation", "delay_sec": 1.5}'
```

---

### `POST /stop-simulation` (or `/api/simulation/stop`)
Stops any active simulation stream immediately.

**Response (200 OK):**
```json
{
  "status": "stopped",
  "message": "Simulation stopped successfully",
  "session_id": "session_5f088d84"
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/stop-simulation
```

---

## 3. SQLite Session History & Post-Call Audit (Day 5)

### `GET /sessions` (or `/api/sessions`)
Lists all previous call sessions stored in the SQLite database.

**Response (200 OK):**
```json
{
  "total_sessions": 1,
  "sessions": [
    {
      "session_id": "session_5f088d84",
      "total_chunks": 6,
      "avg_latency_ms": 254.32,
      "peak_risk_score": 0.8736,
      "final_alert_level": "high",
      "flags_triggered": ["synthetic_artifact", "prosody_flatness"],
      "start_time": "2026-09-14T10:15:00.000000+00:00",
      "end_time": "2026-09-14T10:15:18.000000+00:00"
    }
  ]
}
```

**cURL:**
```bash
curl http://localhost:8000/sessions
```

---

### `GET /sessions/{session_id}/history` (or `/api/sessions/{session_id}/history`)
Returns the complete chronological chunk list and latency data for a call session.

**Response (200 OK):**
See [`sample_history_payload.json`](./sample_history_payload.json).

**cURL:**
```bash
curl http://localhost:8000/sessions/session_5f088d84/history
```

---

## 4. Utility Endpoints

### `GET /health`
```json
{ "status": "ok" }
```

### `GET /contract`
Returns an example `RiskUpdate` object for schema validation.

### `GET /demo`
Serves the built-in reference UI dashboard.
