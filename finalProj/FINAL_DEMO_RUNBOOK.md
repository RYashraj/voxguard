# VoxGuard Final Demo Runbook

**Problem Statement:** SIH26104  
**Team:** Crackjack  
**Demo mode:** Stub mode by default for deterministic local presentation  
**Frontend:** http://localhost:3000  
**Backend:** http://127.0.0.1:8000

## What Judges See

VoxGuard demonstrates a live call-risk workflow:

1. A call stream arrives in rolling audio chunks.
2. Acoustic spoof risk is updated continuously.
3. Caller and transaction context enrich the decision.
4. The advisory engine explains the recommended action.
5. The sensitive transaction gate locks when risk becomes high.
6. Raw audio is not written to SQLite history.

The bundled ASVspoof sample is a public synthetic-speech benchmark clip. It is not presented as a clone of a specific real person.

## Start The Demo

Open two PowerShell terminals from `FinalProj`.

### Terminal 1: Backend

```powershell
Set-Location "C:\SmartIndiaHackathon\FInalProj\backend"
.\.venv\Scripts\Activate.ps1
$env:VOXGUARD_ML_MODE = "stub"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If the virtual environment does not exist:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Terminal 2: Frontend

```powershell
Set-Location "C:\SmartIndiaHackathon\FInalProj"
npm.cmd install
npm.cmd run dev
```

Open http://localhost:3000.

## Primary 60-Second Flow

1. Confirm the dashboard status changes to `live`.
2. Keep the default sample: **Demo script (gradual escalation: low -> high)**.
3. Confirm the visible input source says **Demo audio file**.
4. Confirm the context shows:
   - Caller Status: `Unknown contact`
   - Transaction Type: `OTP or PIN request`
5. Click **Start call**.
6. Point to the **Risk timeline**: bars begin green, cross yellow, then turn red.
7. When yellow appears, explain the early-warning advisory and reason codes.
8. When red appears, point out `synthetic_artifact`, **Block & Report**, and the disabled approval control.
9. Use **Clear call and reset graph** before repeating the demo.

### Presenter Script

> “This is a simulated live call stream, processed chunk by chunk rather than after the call ends. The caller is unknown and is requesting an OTP. VoxGuard combines the acoustic spoof signal with the transaction context, explains the reason codes, and blocks the sensitive approval path when risk crosses the high threshold.”

The OTP preset intentionally uses baseline demo audio plus risky transaction context. It demonstrates contextual fraud prevention, not synthetic-audio detection. The ASVspoof preset is the separate synthetic-audio lane.

## Live Microphone Flow

1. Choose **Live microphone** under Call input.
2. Click **Start call** and allow browser microphone permission.
3. Speak normally for three seconds at a time. The browser sends PCM WAV chunks to `WS /ws/live`.
4. Watch the `mic_001`, `mic_002`, ... updates appear in the same risk timeline.
5. Stop with **Stop call** or reset with **Clear call and reset graph**.

The current stub mode demonstrates the streaming and UI behavior deterministically. Real acoustic model inference requires cached Spectra-AASIST3 weights and a working PyTorch installation.

## Clone Identity Limitation

The repository includes an opt-in ECAPA speaker-verification implementation, but it does not contain a consented same-person reference recording plus a consented cloned-person recording. The current demo can therefore prove synthetic-artifact risk and contextual fraud prevention, but it must not claim that ASVspoof proves a clone of a specific person. Add a consented human reference and clone pair before presenting identity verification as the primary USP.

The consented pair is now present under `backend/data/consented_reference_audio/identity_demo/`. To enable the live comparison panel, install the optional identity runtime once:

```powershell
cd C:\SmartIndiaHackathon\FInalProj\backend
.\.venv\Scripts\python.exe -m pip install -r requirements-identity.txt
```

The first comparison downloads the SpeechBrain ECAPA-TDNN weights. The result appears in the dashboard's **Clone identity lab** panel and at `GET /identity-demo/compare`.

## Secondary Flows

### Context-only social-engineering warning

- Sample: **Baseline audio sample**
- Caller Status: **Unknown contact**
- Transaction Type: **OTP or PIN request**
- Expected result: low acoustic risk plus `pause_and_verify`

Presenter line:

> “Even when the acoustic score is low, an unknown caller requesting a sensitive credential is not allowed to pass silently. The system recommends independent verification.”

### Gradual escalation

- Sample: **Demo script (gradual escalation: low -> high)**
- Context: any selected context
- Expected result: low, then medium, then high as simulated chunks progress.

### Clean call

- Sample: **Hindi genuine human speech**
- Caller Status: **Known contact**
- Transaction Type: **Other**
- Expected result: `continue_with_caution` with no transaction block.

## Health Check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

## Fallback Verification

If the browser UI is unavailable, run the backend integration check while both servers are running:

```powershell
Set-Location "C:\SmartIndiaHackathon\FInalProj\backend"
.\.venv\Scripts\python.exe scripts\live_e2e_verify.py
```

The check covers health, frontend reachability, API contract, WebSocket handshake, simulation start, streamed risk updates, stop, and SQLite history.

## Real Model Mode

The real Spectra-AASIST3 weights were not present in the audited machine cache. Do not switch to real mode during the presentation unless the weights have been separately cached and verified.

When available:

```powershell
$env:VOXGUARD_ML_MODE = "real"
$env:HF_HOME = "C:\Users\<USER>\.cache\huggingface"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Honest Technical Position

- The current demo proves real-time streaming orchestration, synthetic-speech risk scoring, contextual warnings, explainable advisories, transaction gating, and privacy-oriented metadata logging.
- ECAPA-TDNN speaker verification code is included as an opt-in auxiliary layer, but it is not part of the default public risk decision path.
- Indian-language evidence is a small genuine-speech false-positive baseline, not proof of synthetic-clone accuracy across all Indian languages.
- The live sample is a public synthetic benchmark clip, not a teammate voice clone.
