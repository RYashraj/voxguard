# VoxGuard Demonstration Runbook

A step-by-step guide for presenting and running the VoxGuard real-time voice impersonation detection system (SIH26104 - Team Crackjack).

---

## 1. Prerequisites

Before starting the demo, ensure the following are available:
- **Python 3.11+**: Environment initialized at `backend/.venv/` with PyTorch, SpeechBrain, and FastAPI installed.
- **Node.js 18+**: Frontend dependencies installed (`npm install`).
- **Hugging Face Model Cache**: Pre-cached weights stored at `D:\hf_cache` (no online Hugging Face credentials required during live presentation).
- **No Private Credentials**: No cloud API keys or sensitive banking credentials are needed.

---

## 2. Startup Commands (Two Terminals)

### Terminal 1: Backend Server (Port 8000)
```powershell
cd D:\VoxGuard\voxguard-github-integration\backend
$env:VOXGUARD_ML_MODE = "real"
$env:HF_HOME = "D:\hf_cache"
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2: Frontend Dashboard (Port 3000)
```powershell
cd D:\VoxGuard\voxguard-github-integration
npm run dev
```

---

## 3. System Health & Dashboard Verification

1. **Verify Backend Health**:
   Open `http://127.0.0.1:8000/health` in a browser or terminal.
   **Expected Response**: `{"status": "ok"}`

2. **Open Frontend Dashboard**:
   Navigate browser to [http://localhost:3000](http://localhost:3000)

3. **Alternative Built-in Dashboard**:
   Navigate browser to [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)

---

## 4. Three Scripted Demonstration Flows

### Flow 1: Genuine Call + Known Contact (`continue_with_caution`)
- **Settings**:
  - Sample Audio: `demo_call.wav`
  - Caller Context: **Known Contact** (`known_contact`)
  - Transaction Type: **General Conversation** (`other`)
- **Action**: Click **Start Call** on the dashboard.
- **Observed Behavior**:
  - Spectra-AASIST3 score: Low (~0.0497)
  - Alert Level: `low` (Green)
  - Advisory Recommendation: **Continue with Caution** (`continue_with_caution`)
  - Reason Code: `normal_call_flow`
- **Presenter Script**:
  > *"Here we start a standard call simulation from an enrolled contact. The real Spectra-AASIST3 model detects low acoustic risk, and because the caller is a verified known contact, VoxGuard advises 'Continue with caution' without blocking the user."*

---

### Flow 2: Unknown Caller + Sensitive OTP/PIN Request (`pause_and_verify`)
- **Settings**:
  - Sample Audio: `demo_call.wav`
  - Caller Context: **Unknown Contact** (`unknown_contact`)
  - Transaction Type: **OTP / PIN Request** (`otp_or_pin_request`)
- **Action**: Update Context on Dashboard and click **Start Call**.
- **Observed Behavior**:
  - Spectra-AASIST3 score: Low (~0.0497)
  - Alert Level: `low`
  - Advisory Recommendation: **Pause and Verify** (`pause_and_verify`)
  - Reason Codes: `unknown_caller`, `sensitive_transaction_request`
  - Action Gate: "Approve Transaction" button is disabled; "Verify Caller" action highlighted.
- **Presenter Script**:
  > *"Now notice what happens when an unverified caller requests a sensitive OTP or PIN. Even though the acoustic score alone is low, VoxGuard's contextual policy detects the high-risk transaction request from an unknown caller and immediately elevates the advisory to 'Pause and verify'."*

---

### Flow 3: Synthetic Voice Clone Sample (`block_and_report`)
- **Settings**:
  - Sample Audio: `data/test_audio/asvspoof_spoof_demo.wav`
  - Scenario: **Suspicious / Synthetic**
- **Action**: Click **Start Call**.
- **Observed Behavior**:
  - Spectra-AASIST3 score: High (>0.99)
  - Alert Level: `high` (Red)
  - Public Flag: `synthetic_artifact`
  - Advisory Recommendation: **Block and Report** (`block_and_report`)
  - Action Gate: "End Call" button is highlighted; transaction approval is locked.
- **Presenter Script**:
  > *"Finally, we stream a synthetic voice clone sample from the public ASVspoof benchmark. The Spectra-AASIST3 model immediately detects synthetic spectral artifacts with high risk (>0.99), triggering an automated 'Block and report' advisory to protect the user."*

---

## 5. How to Reset a Demo & Retrieve Session History

1. **Reset Demo State**:
   Click **End Call** or **Stop Call** on the dashboard (or send `POST /stop-simulation`). This terminates the stream and wipes in-memory identity embeddings.

2. **Retrieve Session History**:
   Query session history for audit verification:
   `http://127.0.0.1:8000/sessions/{session_id}/history`
   **Expected Response**: JSON array of chunk records containing only allowlisted risk metadata.

---

## 6. Safe Troubleshooting Guide

| Issue | Cause | Resolution |
|---|---|---|
| **Model Unavailable flag** | HF cache path or env variable missing | Ensure `$env:VOXGUARD_ML_MODE = "real"` and `$env:HF_HOME = "D:\hf_cache"` are set before starting Uvicorn. |
| **WebSocket Cannot Connect** | Backend server not running | Verify Uvicorn terminal is active on port 8000. |
| **Frontend Cannot Reach Backend** | Port collision or CORS issue | Ensure Uvicorn is on port 8000 and Next.js is on port 3000. |
| **Slow Initial Inference** | PyTorch & wav2vec2 weights warm-up on CPU | First chunk execution takes a few seconds while loading model tensors into memory. Subsequent chunks process smoothly. |

---

## 7. Honest Technical Limitations (If Asked)

If judges or reviewers ask detailed technical questions, state these honest facts:
1. **CPU Latency**: CPU inference latency takes ~4–8 seconds per chunk. Production deployment uses GPU inference for sub-second latency.
2. **Prosody Layer**: Prosody feature analysis is currently informational for internal research and quarantined from public risk flags until benchmark calibration is completed.
3. **Indic Language Baseline**: Our Indian language baseline measured false-positive behavior on 10 genuine public FLEURS clips; multilingual deepfake detection accuracy requires testing on synthetic Indic voice clones.
4. **Speaker Verification**: Speaker identity drift detection requires opt-in caller consent and further multi-speaker calibration before operational deployment.
