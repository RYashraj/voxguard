# VoxGuard Integration Hub & Team Resources

Welcome Team Crackjack! This folder contains all the shared contracts, sample data, testing utilities, and integration guides provided by **Shreyas (Backend)** so that the **Frontend team** and **ML team** can easily connect and test their parts without confusion.

---

## Folder Quick Navigation

### 1. [`for_frontend/`](./for_frontend/) (For Meet & Devikrishna)
Contains everything needed to wire up the Next.js / React live dashboard:
- **`README.md`**: Complete integration guide (WebSocket connection, React hook snippet, UI alert color thresholds, and API triggers).
- **`sample_payload.json`**: Exact sample JSON payload matching the contract.
- **`contract_schema.json`**: JSON Schema specification for type checking.
- **`test_websocket_client.html`**: Standalone HTML client to test the live stream in 1 click.

---

### 2. [`for_ml/`](./for_ml/) (For Hetvi & Nandini)
Contains everything needed for model benchmark testing and backend integration:
- **`README.md`**: Audio chunking specifications, PyTorch/Librosa audio loading code snippets, and drop-in instructions.
- **`sample_inference_template.py`**: A ready-to-use Python template showing the exact function signature for `analyze_chunk(audio_bytes)`.
- **`audio_specs.json`**: Audio format parameters (16 kHz, 16-bit mono PCM, 3.0s duration, 48,000 samples).
- **`sample_chunks/`**: Pre-sliced 3.0-second WAV files (`chunk_001.wav` to `chunk_006.wav`) to test your model inference directly on short chunks.

---

## Need Live Backend API & WebSocket?
To run the live backend server on `http://localhost:8000`:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Live Stream Reference Dashboard**: `http://localhost:8000/demo`
- **WebSocket Endpoint**: `ws://localhost:8000/ws/session`
