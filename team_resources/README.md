# VoxGuard Integration Hub & Team Resources

Welcome Team Crackjack! This folder contains all the shared contracts, sample data, testing utilities, API cheatsheets, and integration guides provided by **Shreyas (Backend)** so that the **Frontend team** and **ML team** have everything they need to connect, benchmark, and demo without friction.

---

## Folder Quick Navigation

### 1. [`for_frontend/`](./for_frontend/) (For Meet & Devikrishna)
Contains everything needed to wire up the Next.js / React live dashboard:
- **`README.md`**: Complete integration guide (WebSocket live streaming, React hooks, UI alert color rules, simulation triggers, and Day 5 SQLite session history endpoints).
- **`types.ts`**: Complete TypeScript definitions for WebSocket messages, REST payloads, and SQLite history records.
- **`useVoxGuardSocket.ts`**: Ready-to-use React/Next.js custom hook for live streaming and auto-lock logic.
- **`api_cheatsheet.md`**: Complete REST & WebSocket API reference table with cURL snippets.
- **`sample_payload.json`**: Exact sample JSON message for real-time WebSocket `RiskUpdate`.
- **`sample_history_payload.json`**: Sample JSON response from `GET /sessions/{session_id}/history`.
- **`sample_sessions_list.json`**: Sample JSON response from `GET /sessions`.
- **`contract_schema.json`**: JSON Schema specification for type validation.
- **`test_websocket_client.html`**: Standalone HTML client with live risk gauges, start/stop controls, and SQLite session audit log fetcher.

---

### 2. [`for_ml/`](./for_ml/) (For Hetvi & Nandini)
Contains everything needed for model benchmark testing and backend integration:
- **`README.md`**: Audio specifications, Spectra-AASIST3 integration details, interface contract, and benchmark instructions.
- **`test_model_offline.py`**: Standalone offline benchmark runner that tests your model on sample chunks and prints per-chunk latency and scores.
- **`sample_inference_template.py`**: Python starter template showing the exact function signature for `analyze_chunk(audio_bytes)`.
- **`sample_ml_output.json`**: Exact JSON dictionary output structure expected from `analyze_chunk()`.
- **`benchmarking_notes.md`**: Latency targets, GPU acceleration, and ONNX optimization recommendations.
- **`audio_specs.json`**: Audio format parameters (16 kHz, 16-bit mono PCM, 3.0s duration, 48,000 samples).
- **`sample_chunks/`**: Pre-sliced 3.0-second WAV files (`chunk_001.wav` to `chunk_006.wav`) to test model inference directly on short chunks.

---

## Live Backend API & WebSocket Access

To run the live backend server on `http://localhost:8000`:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Live Stream Reference Dashboard**: `http://localhost:8000/demo`
- **Past Sessions Audit API**: `http://localhost:8000/sessions`
- **WebSocket Endpoint**: `ws://localhost:8000/ws/session`

---

## Automated Verification Scripts (Backend)
- `python scripts/verify_day1_day2.py`: Verifies FastAPI scaffold, Pydantic contracts, and Call Simulator slicing.
- `python scripts/verify_day3_day4.py`: Verifies RollingRiskAggregator math and ML Stub streaming.
- `python scripts/verify_day5.py`: Verifies Spectra-AASIST3 model inference, SQLite session logging, and per-chunk latency metrics.
- `python scripts/verify_day6.py`: Verifies multi-scenario stability (Clean, ASVspoof attack, Gradual escalation) and multi-viewer WebSocket broadcasting.
