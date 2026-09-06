# VoxGuard

**AI-powered real-time voice cloning & impersonation detection**
Built for Smart India Hackathon 2026 — PS SIH26104 (Cyber Security Cell, AICTE)
Team Crackjack

## Problem
Voice cloning tech can now convincingly impersonate a real person in seconds. Attackers use this to trick employees or individuals during calls into approving fraudulent transactions or leaking sensitive information. Traditional verification (caller ID, callback, "I recognize this voice") can no longer reliably catch it.

## What VoxGuard does
VoxGuard analyzes call audio in near real time and produces a live "impersonation risk score" from two signals:
- **Deepfake/synthetic-speech detection** — flags acoustic signs of AI-generated audio
- **Speaker verification** — compares the caller's voice against a known genuine sample

When risk crosses a threshold, VoxGuard alerts the user and recommends secondary verification (e.g. callback).

## Tech Stack
- Backend: FastAPI (Python)
- ML: HuggingFace Transformers (deepfake detection) + SpeechBrain (speaker verification)
- Frontend: Next.js + Tailwind

## Setup
```bash
# backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

## Team
- Yashraj — Integration, git, review, docs
- Hetvi — ML pipeline
- Shreyas — Backend/API
- Meet — Frontend/Dashboard

## Roadmap (Phase 2)
- Telecom/VoIP integration
- Multilingual & regional accent support
- On-device/privacy-preserving inference
- Banking/enterprise API integration
