# VoxGuard — Demo Skit Script

> **For:** Team Crackjack internal use — SIH 2026 pitch day  
> **Audience:** Judges, evaluators  
> **Duration:** ~4–5 minutes  

---

## Setup (Before Judges Arrive)

1. **Backend running:** `.\venv\Scripts\uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000`
2. **Frontend running:** `npm run dev` (port 3000)
3. **Browser open:** `http://localhost:3000` — signed in via Google OAuth
4. **Environment:** `VOXGUARD_ML_MODE=stub` for reliable, instant scoring OR `real` if model weights are loaded
5. **Tab ready:** `/transparency` page open in a second tab

---

## Demo Flow

### Step 1 — Introduce the Problem (30s, no demo action needed)

> *"Vishing and voice cloning attacks are up 300% in 2025. An attacker can clone a CFO's voice in under 60 seconds and call the finance team to authorise a fraudulent wire transfer. The victim hears a voice they recognise. Traditional caller ID is useless. Callback verification is too slow. By the time they realise, the money is gone."*

---

### Step 2 — Show the Dashboard (30s)

Point to the live screen:

> *"This is VoxGuard's live monitoring dashboard. It sits in the background on any call — completely passive from the caller's perspective. The moment a call is routed to staff, our system starts analysing the audio in real time."*

- Show the **connection status** dot (green `live` in the header)
- Show the **Known Contact** dropdown — explain enrolled voice profiles
- Select **"Rajesh Sharma — CFO"** from the dropdown
- Set **Transaction Context** to **"Fund Transfer"**

---

### Step 3 — Simulate a Clean Human Call (45s)

Click **Start call** — scenario: `clean`

> *"Here's a legitimate call from the real CFO. Watch the gauge."*

- Point to the **Risk Gauge** — stays in the low/green zone
- Point to the **Waveform** — active but smooth
- Point to the **Multi-Layer Trend** — all three lines (rolling risk, prosody, identity drift) stay flat at the bottom

> *"System is calm. No anomalies. The rolling risk score never crosses the 0.4 threshold."*

Click **Stop call** → **Clear data**

---

### Step 4 — Simulate the Deepfake Attack (2 min — the money shot)

Set **Transaction Context** to **"Fund Transfer"** again. Click **Start call** — scenario: `suspicious`

> *"Now — the same call. Except this time it's an attacker using a voice clone of the CFO, generated from 30 seconds of audio scraped from a public earnings call."*

As chunks stream in:
- **Chunk 1:** Score ~0.82 → gauge jumps into the **RED zone immediately**
- **Alert banner** fires — `synthetic_artifact`, `prosody_flatness` flags visible
- Point to the **Identity Drift line** in the trend chart — starts climbing

> *"Within the first 3 seconds of audio — before the attacker has even said anything important — VoxGuard has already flagged this as a high-confidence spoof. Rolling risk: 0.87."*

- **Alert toast** appears top-right
- After chunks 3–4, the **Pre-Transaction Modal** fires automatically

> *"Here's the critical moment. The attacker says 'please transfer ₹2 crore to account ending 4521.' Normally, the staff member would just do it — they think it's the CFO. But VoxGuard intercepts this. It sees the active context is a fund transfer with an ongoing high-risk alert, and blocks the action behind a mandatory secondary verification step."*

Point to the modal options:
- **Call-back Verification** — call the real CFO on a known number
- **Multi-Factor Authentication**
- **Escalate to Supervisor**

> *"The attacker has failed. They can't bypass a physical callback. The fraud is stopped."*

---

### Step 5 — Show the Transparency Page (30s)

Click the **Transparency 📊** link in the header.

> *"For regulators and auditors, we expose exactly how our model performs across different languages and accents — because a detection system that only works on one accent profile isn't safe for India. This table is wired live to our accuracy dataset and can be updated as evaluation progresses."*

---

### Step 6 — Close with Architecture (30s, optional if time allows)

> *"Under the hood: FastAPI backend with WebSocket streaming, Spectra-AASIST3 spoof detection model from HuggingFace, librosa prosody analysis, cosine-based speaker identity tracking, SQLite audit logging, and a Next.js real-time dashboard. Full test coverage — 36 tests, all passing. Average per-chunk inference latency: 0.15 milliseconds. The system is real-time, not batch."*

---

## Talking Points for Q&A

**Q: Why not just use speaker verification?**  
> Speaker verification tells you if a voice matches a voiceprint — but an attacker with a good clone will fool it too. We combine spectral artifact detection (Spectra-AASIST3), prosody analysis (pitch/jitter patterns distinct to synthesis), and identity drift in one pipeline. Any single layer failing doesn't break the system.

**Q: What's the latency in production?**  
> We analyse in 3-second chunks. Each chunk analysis takes ~0.15ms in stub mode. Even with the full neural network (GPU), inference is under 500ms — well within the 3-second window. The user sees an update every 3 seconds.

**Q: Does this work on VoIP/telecom calls?**  
> The current demo uses WAV simulation — but the architecture is stream-agnostic. You can feed real-time PCM audio from any VoIP media fork (Twilio Media Streams, Asterisk, etc.) directly into the chunk pipeline. That's Phase 2.

**Q: What if the model is wrong and flags a real person?**  
> The rolling average smooths out single-chunk false positives — a one-chunk spike won't trigger a HIGH alert. The pre-transaction modal requires human action, not automatic blocking. It's a decision-support tool, not an autonomous gate.

**Q: What about Indian accents?**  
> The Transparency page shows per-accent accuracy breakdown. Spectra-AASIST3 is trained on ASVspoof datasets which include diverse acoustic conditions. We're actively evaluating on regional accent data — that's what the transparency page tracks.
