# VoxGuard Integration Hub & Team Resources

Welcome Team Crackjack! This folder contains all the shared contracts, sample data, testing utilities, and integration guides provided by **Shreyas (Backend)** so that the **Frontend team** and **ML team** can easily connect and test their parts without friction.

---

## Folder Quick Navigation

### 1. [`for_frontend/`](./for_frontend/) (For Meet & Devikrishna)
Contains everything needed to wire up the Next.js / React live dashboard:
- **`README.md`**: Complete integration guide (WebSocket live streaming, React hooks, UI alert color rules, simulation triggers, and Day 5 SQLite session history endpoints).
- **`sample_payload.json`**: Exact sample JSON payload matching the contract.
- **`contract_schema.json`**: JSON Schema specification for type validation.
- **`test_websocket_client.html`**: Standalone HTML client with live risk gauges, start/stop controls, and SQLite session audit log fetcher.

---

### 2. [`for_ml/`](./for_ml/) (For Hetvi & Nandini)
Contains everything needed for model benchmark testing and backend integration:
- **`README.md`**: Audio specifications, Spectra-AASIST3 integration details, interface contract, and benchmark instructions.
- **`sample_inference_template.py`**: Python template showing the exact function signature for `analyze_chunk(audio_bytes)`.
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
- `python backend/scripts/verify_day1_day2.py`: Verifies FastAPI scaffold, Pydantic contracts, and Call Simulator slicing.
- `python backend/scripts/verify_day3_day4.py`: Verifies RollingRiskAggregator math and ML Stub streaming.
- `python backend/scripts/verify_day5.py`: Verifies Spectra-AASIST3 model inference, SQLite session logging, and per-chunk latency metrics.
