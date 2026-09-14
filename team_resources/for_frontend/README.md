# Frontend Integration Guide (Meet & Devikrishna)

Welcome! Here is everything you need to connect your **Next.js / Tailwind** dashboard to the live VoxGuard backend stream, including real-time risk updates, post-call SQLite audit history, and latency tracking.

---

## 1. Real-Time WebSocket Endpoint

* **URL**: `ws://localhost:8000/ws/session` (or `ws://localhost:8000/ws/session/{session_id}`)
* **Protocol**: Standard WebSocket (No authentication tokens or headers required for local dev).
* **Handshake Message**: When connected, backend sends an initial JSON event:
  ```json
  {
    "event": "connected",
    "message": "Connected to VoxGuard real-time stream",
    "session_id": "default"
  }
  ```

---

## 2. Incoming Data Shape (`RiskUpdate`)

For every audio chunk processed during a call, your WebSocket listener receives a JSON message matching this strict contract:

```json
{
  "chunk_id": "chunk_001",
  "timestamp": "2026-09-11T10:00:00.000000+00:00",
  "chunk_score": 0.12,
  "rolling_risk_score": 0.12,
  "confidence": 0.94,
  "flags": ["synthetic_artifact"],
  "alert_level": "low"
}
```

### UI Color & Auto-Lock Logic:

| `alert_level` | `rolling_risk_score` | UI Color | Description | Action / Gate Rule |
|---|---|---|---|---|
| `"low"` | `< 0.40` | **Green** (`#10B981`) | Normal genuine human speech | Approve Button: **Unlocked** |
| `"medium"` | `0.40 – 0.70` | **Yellow** (`#F59E0B`) | Elevated risk / Prosody anomalies | Monitor Closely |
| `"high"` | `> 0.70` | **Red** (`#EF4444`) | Possible AI Clone / Fraud Attack | **Auto-Lock Approve Button** (Show "Verify via callback") |

---

## 3. Ready-to-Use React / Next.js Hook

```tsx
// hooks/useVoxGuardSocket.ts
import { useEffect, useState, useCallback } from "react";

export interface RiskUpdate {
  chunk_id: string;
  timestamp: string;
  chunk_score: number;
  rolling_risk_score: number;
  confidence: number;
  flags: string[];
  alert_level: "low" | "medium" | "high";
}

export function useVoxGuardSocket(url = "ws://localhost:8000/ws/session") {
  const [latestData, setLatestData] = useState<RiskUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [history, setHistory] = useState<RiskUpdate[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "connected") {
          setSessionId(payload.session_id);
          return;
        }

        setLatestData(payload);
        setHistory((prev) => [payload, ...prev]);
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    return () => ws.close();
  }, [url]);

  const clearHistory = useCallback(() => setHistory([]), []);

  return { latestData, isConnected, history, sessionId, clearHistory };
}
```

---

## 4. REST API Endpoints

### A. Call Simulation Controls

#### 1. Start Call Simulation
`POST http://localhost:8000/start-simulation` (or `/api/simulation/start`)
```json
{
  "chunk_duration_sec": 3.0,
  "delay_sec": 2.0,
  "scenario": "gradual_escalation"
}
```
*Scenarios available*: `"gradual_escalation"`, `"clean"`, `"suspicious"`

**Response (200 OK):**
```json
{
  "status": "started",
  "message": "Simulation running for scenario 'gradual_escalation' at 2.0s interval",
  "session_id": "session_5f088d84"
}
```

#### 2. Stop Simulation
`POST http://localhost:8000/stop-simulation` (or `/api/simulation/stop`)

---

### B. SQLite Session History & Post-Call Audit (Day 5)

#### 1. List All Past Sessions
`GET http://localhost:8000/sessions` (or `/api/sessions`)

**Response (200 OK):**
```json
{
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "session_5f088d84",
      "total_chunks": 6,
      "avg_latency_ms": 254.3,
      "peak_risk_score": 0.8245,
      "final_alert_level": "high",
      "flags_triggered": ["synthetic_artifact", "prosody_flatness"],
      "start_time": "2026-09-11T10:00:00Z",
      "end_time": "2026-09-11T10:00:15Z"
    }
  ]
}
```

#### 2. Get Detailed Session History
`GET http://localhost:8000/sessions/{session_id}/history` (or `/api/sessions/{session_id}/history`)

**Response (200 OK):**
```json
{
  "session_id": "session_5f088d84",
  "total_chunks": 6,
  "stats": {
    "session_id": "session_5f088d84",
    "total_chunks": 6,
    "avg_latency_ms": 254.3,
    "peak_risk_score": 0.8245,
    "final_alert_level": "high",
    "flags_triggered": ["synthetic_artifact", "prosody_flatness"],
    "start_time": "2026-09-11T10:00:00Z",
    "end_time": "2026-09-11T10:00:15Z"
  },
  "history": [
    {
      "session_id": "session_5f088d84",
      "chunk_id": "chunk_001",
      "timestamp": "2026-09-11T10:00:00Z",
      "chunk_score": 0.08,
      "rolling_risk_score": 0.08,
      "confidence": 0.94,
      "flags": [],
      "alert_level": "low",
      "inference_latency_ms": 248.5
    }
  ]
}
```

---

## 5. Quick Test Tools
1. **Interactive Test Page**: Open [`test_websocket_client.html`](./test_websocket_client.html) directly in any browser for 1-click live testing with zero setup.
2. **Backend Reference Dashboard**: Browse to `http://localhost:8000/demo` for the built-in reference UI.
3. **Swagger API Docs**: Explore schemas and test all endpoints interactively at `http://localhost:8000/docs`.
