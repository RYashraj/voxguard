# Frontend Integration Guide (Meet & Devikrishna)

Welcome! Here is everything you need to connect your **Next.js / Tailwind** dashboard to the live backend stream.

---

## 1. WebSocket Endpoint
* **URL**: `ws://localhost:8000/ws/session` (or `ws://localhost:8000/ws/session/{sessionId}`)
* **Protocol**: Standard WebSocket (No authorization headers or special query params required).

---

## 2. Incoming Data Shape (`RiskUpdate`)

For every 3-second audio chunk, your WebSocket listener will receive a JSON message matching this shape:

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

### UI Color & Auto-Lock Logic:

| `alert_level` | `rolling_risk_score` | UI Color | Description | Action / Gate Rule |
|---|---|---|---|---|
| `"low"` | `< 0.40` | **Green** (`#10B981`) | Normal genuine human speech | Approve Button: **Unlocked** |
| `"medium"` | `0.40 – 0.70` | **Yellow** (`#F59E0B`) | Elevated risk / Prosody anomalies | Monitor Closely |
| `"high"` | `> 0.70` | **Red** (`#EF4444`) | Possible AI Clone / Fraud Attack | **Auto-Lock Approve Button** (Show "Verify via callback") |

---

## 3. Ready-to-Use React / Next.js Hook

```tsx
// useVoxGuardSocket.ts
import { useEffect, useState } from "react";

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

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "connected") return; // Handshake

        setLatestData(payload);
        setHistory((prev) => [payload, ...prev]);
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    return () => ws.close();
  }, [url]);

  return { latestData, isConnected, history };
}
```

---

## 4. API Endpoints for Calling Simulation

### Start Simulation
```javascript
fetch("http://localhost:8000/start-simulation", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    chunk_duration_sec: 3.0,
    delay_sec: 3.0,
    scenario: "gradual_escalation" // "clean" | "suspicious" | "gradual_escalation"
  })
});
```

### Stop Simulation
```javascript
fetch("http://localhost:8000/stop-simulation", { method: "POST" });
```

---

## 5. Quick Test Tools
1. Double click [`test_websocket_client.html`](./test_websocket_client.html) in your browser to test live streaming with zero setup.
2. View full backend UI reference at `http://localhost:8000/demo`.
