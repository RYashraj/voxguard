# VoxGuard

**AI-powered real-time voice cloning & impersonation detection**
Built for Smart India Hackathon 2026 — PS SIH26104 (Cyber Security Cell, AICTE)
Team Crackjack

## Problem
Voice cloning tech can now convincingly impersonate a real person in seconds. Attackers use this to trick employees or individuals **during a live call** into approving fraudulent transactions or leaking sensitive information. Traditional verification (caller ID, callback, "I recognize this voice") can no longer reliably catch it — and by the time a call ends, the damage is already done.

## What VoxGuard does
VoxGuard processes call audio **in real time, chunk by chunk, while the call is still ongoing** — not after it ends — and produces a continuously updating "impersonation risk score."

**Detection layers:**
- **Acoustic/spectral analysis** — flags synthesis artifacts and spectral signatures typical of AI-generated speech
- **Prosody analysis** — checks pitch variance, pause patterns, and speech rhythm against natural human speech

**Risk engine:**
- Aggregates per-chunk scores into a smoothed rolling risk score
- Fires threshold-based alerts (low / medium / high) as risk builds during the call

**Alerting & prevention:**
- Live dashboard shows the risk score updating in real time
- High risk triggers a visible alert recommending secondary verification (e.g. callback)
- Sensitive actions (e.g. approving a transaction) are gated behind verification once risk crosses threshold — the system can't stop the call itself, but it stops the human from acting blindly

## How it works
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

For the hackathon build, the "live call" is either a mic-captured live conversation or a pre-recorded file streamed in real chunks — architecturally identical to a real live call, since the whole pipeline works on a rolling stream, not a finished recording. Real telephony/carrier integration is future scope (see Roadmap).

## Tech Stack
- **Backend:** FastAPI (Python), WebSockets, SQLite for session logging
- **ML:** PyTorch + HuggingFace Transformers (wav2vec2/AASIST-based spoof detection), librosa (prosody features), pydub (audio chunking)
- **Frontend:** Next.js + Tailwind, WebSocket client, Recharts for live risk visualization

## Setup
```bash
# backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

## Data contract
Every risk update flowing from backend to frontend follows this shape:
```json
{
  "chunk_id": "string",
  "timestamp": "iso8601",
  "chunk_score": 0.0,
  "rolling_risk_score": 0.0,
  "confidence": 0.0,
  "flags": ["synthetic_artifact"],
  "alert_level": "low"
}
```

## Team
- **Yashraj** — Integration, git, docs
- **Shreyas** — Backend / real-time API
- **Hetvi, Nandini** — ML pipeline (detection + risk scoring)
- **Meet, Devikrishna** — Frontend / live dashboard

## Roadmap (Phase 2)
- Telecom/VoIP-level integration (carrier partnership, regulatory clearance)
- Banking/enterprise call-center integration (media forking, Twilio-style stream APIs)
- Cross-session speaker verification against enrolled genuine voice samples
- Multilingual & regional accent support
- On-device/edge inference for privacy-preserving deployment
