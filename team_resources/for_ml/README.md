# ML Integration Guide (Hetvi & Nandini)

Welcome! Here is everything you need to benchmark your deepfake audio detection models, understand how the backend loads your model, and run verification tests.

---

## 1. Current Model Integration Status

* **Integrated Model**: **Spectra-AASIST3** (`lab260/Spectra-AASIST3`) combined with **Wav2Vec2** (`facebook/wav2vec2-xls-r-300m`).
* **Backend Module**: Located in [`backend/app/ml/ml_model.py`](../../backend/app/ml/ml_model.py).
* **Execution Architecture**:
  - **Thread-safe Singleton** (`SpectraAASISTDetector`) to ensure model weights load once in memory.
  - Concurrency locks protecting PyTorch tensors during parallel WebSocket streams.
  - Worker thread offloading via `asyncio.to_thread` to maintain zero stutter on the FastAPI event loop.

---

## 2. Audio Chunk Format Specifications

The backend call simulator slices live call audio into 3-second windows before calling your inference function:

* **Duration**: `3.0 seconds`
* **Sample Rate**: `16,000 Hz (16 kHz)`
* **Channels**: `1 (Mono)`
* **Bit Depth**: `16-bit PCM`
* **Samples per Chunk**: `48,000 samples` (~96 KB raw WAV bytes)
* **Spectra-AASIST3 Target**: Padded / repeated up to 64,600 samples (~4.0s) internally by `parse_audio_bytes()`.

Detailed JSON schema is available in [`audio_specs.json`](./audio_specs.json).

---

## 3. Standard Interface Contract (`analyze_chunk`)

The backend interfaces with the ML module through a single standardized function:

```python
def analyze_chunk(audio_bytes: bytes) -> dict:
    """
    Input:
        audio_bytes (bytes): Raw WAV bytes of a 3-second audio slice (16kHz PCM).
    Output:
        dict:
            - chunk_score (float, 0.0 to 1.0): Spoof score (0.0 = Human, 1.0 = AI Clone)
            - confidence (float, 0.0 to 1.0): Detection confidence score
            - flags (list[str]): List of detected anomalies
    """
```

### Supported Anomaly Flags:
- `synthetic_artifact`: High spoof probability ($> 0.70$)
- `prosody_flatness`: Moderate anomalies ($0.40 – 0.70$)
- `short_audio`: Audio chunk was less than target sample length (auto-padded)
- `silent_audio`: RMS energy below threshold ($< 0.001$)
- `invalid_audio`: Corrupted or non-WAV bytes

---

## 4. How to Test Your Model with the Backend

### Run Automated Day 5 Verification Benchmark:
```powershell
cd backend
python scripts/verify_day5.py
```
This tests:
1. Direct `analyze_chunk()` on sample audio chunks in `team_resources/for_ml/sample_chunks/`.
2. Model loading status and tensor evaluation.
3. Inference latency measurement (logged in milliseconds).
4. SQLite telemetry persistence and mode switching.

### Toggle Real Model vs Fast Stub:
You can switch modes via the `VOXGUARD_ML_MODE` environment variable:
```powershell
# Real Model Mode (PyTorch / Transformers)
$env:VOXGUARD_ML_MODE = "real"

# Fast Stub Mode (Deterministic simulation for UI dev)
$env:VOXGUARD_ML_MODE = "stub"
```

---

## 5. Sample Audio Chunks
Pre-sliced 3.0s WAV files are available in [`sample_chunks/`](./sample_chunks/):
- `chunk_001.wav` to `chunk_006.wav`
