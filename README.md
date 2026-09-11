# VoxGuard

**AI-powered real-time voice cloning & impersonation detection**  
Built for Smart India Hackathon 2026 — PS SIH26104 (Cyber Security Cell, AICTE)  
Team Crackjack

---

## Problem
Voice cloning tech can now convincingly impersonate a real person in seconds. Attackers use this to trick employees or individuals **during a live call** into approving fraudulent transactions or leaking sensitive information. Traditional verification (caller ID, callback, "I recognize this voice") can no longer reliably catch it — and by the time a call ends, the damage is already done.

## What VoxGuard Does
VoxGuard processes call audio **in real time, chunk by chunk, while the call is still ongoing** — not after it ends — and produces a continuously updating "impersonation risk score."

### Detection Layers:
- **Acoustic/spectral analysis** — flags synthesis artifacts and spectral signatures typical of AI-generated speech
- **Prosody analysis** — checks pitch variance, pause patterns, and speech rhythm against natural human speech

### Risk Engine:
- Aggregates per-chunk scores into a smoothed rolling risk score
- Fires threshold-based alerts (`low` / `medium` / `high`) as risk builds during the call

### Alerting & Prevention:
- Live dashboard displays the risk score updating in real time with waveform visualization
- High risk triggers visible alerts recommending secondary verification
- Sensitive actions are gated behind verification once risk crosses safety thresholds

---

## How It Works
```
Live/simulated call audio
        │
        ▼
Audio chunked (2–4s windows)
        │
        ▼
Multi-layer voice analysis (acoustic + prosody)
        │
        ▼
Rolling risk scoring engine (aggregation + thresholds)
        │
        ▼
Live dashboard + alerts + verification gate
```

---

## Tech Stack
- **Frontend:** Next.js 14 (App Router), Tailwind CSS, Recharts, WebSockets
- **Backend:** FastAPI (Python), WebSockets, SQLite for session logging
- **ML:** PyTorch + HuggingFace Transformers (wav2vec2/AASIST-based spoof detection), librosa (prosody features), pydub (audio chunking)

---

## Getting Started

### 1. Run the Frontend & Mock Server

```bash
# Install dependencies
npm install

# Start the mock backend server (port 8000)
node server.js

# In another terminal, start the Next.js frontend (port 3000)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the live dashboard.

### 2. Run Tests

```bash
npm test
```

---

## Data Contract
Every risk update flowing from backend to frontend follows this schema:
```json
{
  "chunk_id": "chunk_001",
  "timestamp": "2026-09-11T19:00:00.000Z",
  "chunk_score": 0.45,
  "rolling_risk_score": 0.42,
  "confidence": 0.88,
  "flags": ["synthetic_artifact"],
  "alert_level": "medium"
}
```

---

## Team
- **Yashraj** — Integration, git, docs
- **Shreyas** — Backend / real-time API
- **Hetvi, Nandini** — ML pipeline (detection + risk scoring)
- **Meet, Devikrishna** — Frontend / live dashboard

---

## Roadmap (Phase 2)
- Telecom/VoIP-level integration (carrier partnership, regulatory clearance)
- Banking/enterprise call-center integration (media forking, Twilio-style stream APIs)
- Cross-session speaker verification against enrolled genuine voice samples
- Multilingual & regional accent support
- On-device/edge inference for privacy-preserving deployment
