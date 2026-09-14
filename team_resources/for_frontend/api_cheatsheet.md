# VoxGuard Backend API Cheatsheet (For Frontend Team)

Base URL: `http://localhost:8000`  
WebSocket: `ws://localhost:8000/ws/session` (or `/api/v1/ws/session`)

---

## 1. Known Contacts & Caller Setup (Task 1)

### `GET /api/v1/contacts` (or `/contacts`)
Retrieves list of enrolled executive/employee contacts for the **Known Contact** dropdown, including fallback unknown caller.

**Response (200 OK):**
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
    },
    {
      "id": "contact_002",
      "name": "Priya Patel",
      "role": "Director of Information Technology",
      "phone_number": "+91 98123 45678",
      "enrolled": true,
      "risk_profile": "low"
    },
    {
      "id": "contact_003",
      "name": "Vikram Malhotra",
      "role": "Chief Executive Officer (CEO)",
      "phone_number": "+91 98989 12345",
      "enrolled": true,
      "risk_profile": "low"
    },
    {
      "id": "contact_004",
      "name": "Ananya Iyer",
      "role": "Senior Finance Controller",
      "phone_number": "+91 97654 32109",
      "enrolled": true,
      "risk_profile": "low"
    },
    {
      "id": "contact_005",
      "name": "Sameer Deshmukh",
      "role": "Head of Treasury Operations",
      "phone_number": "+91 99887 76655",
      "enrolled": true,
      "risk_profile": "low"
    },
    {
      "id": "unknown",
      "name": "Unknown / External Caller",
      "role": "Unenrolled External Line",
      "phone_number": "+91 91234 56789",
      "enrolled": false,
      "risk_profile": "high"
    }
  ]
}
```

---

## 2. Session Start & Simulation Controls

### `POST /api/v1/session/start` (or `/start-simulation`)
Starts a live audio stream session with caller identification and transaction context.

**Request Body (JSON):**
```json
{
  "caller_id": "contact_001",
  "caller_name": "Rajesh Sharma",
  "transaction_context": "fund_transfer",
  "scenario": "gradual_escalation",
  "delay_sec": 2.0
}
```

*Transaction Context Options*:
- `"fund_transfer"`: High-value wire / transfer approval.
- `"information_request"`: Password / sensitive info inquiry.
- `"routine"`: Everyday regular business call.

*Scenario Options*:
- `"gradual_escalation"`: Normal speech transitioning to AI clone.
- `"clean"`: 100% genuine human speech (Low Alert).
- `"suspicious"`: Instant deepfake attack call (High Alert).

**Response (200 OK):**
```json
{
  "status": "started",
  "message": "Simulation running for scenario 'gradual_escalation' at 2.0s interval (Caller: contact_001, Context: fund_transfer)",
  "session_id": "session_5f088d84",
  "caller_id": "contact_001",
  "transaction_context": "fund_transfer"
}
```

---

### `POST /api/v1/session/stop` (or `/stop-simulation`)
Stops any currently running session.

**Response (200 OK):**
```json
{
  "status": "stopped",
  "message": "Simulation stopped successfully",
  "session_id": "session_5f088d84"
}
```

---

## 3. Real-Time Streaming

### `WS /ws/session` (or `/api/v1/ws/session`)
Stream of `RiskUpdate` JSON messages for each audio chunk:
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

## 4. SQLite Session History & Post-Call Audit

### `GET /api/v1/sessions` (or `/sessions`)
List all previous sessions.

### `GET /api/v1/session/{session_id}/history` (or `/sessions/{session_id}/history`)
Retrieve full chunk history and aggregate metrics for a session.
