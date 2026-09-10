# ML Integration Guide (Hetvi & Nandini)

Welcome! Here is everything you need to test your spoof/cloning detection models against real audio chunks and prepare your code for backend integration.

---

## 1. Audio Chunk Format Specifications
The backend slices live call audio into 3-second windows before calling your inference function:

* **Duration**: `3.0 seconds`
* **Sample Rate**: `16,000 Hz (16 kHz)`
* **Channels**: `1 (Mono)`
* **Bit Depth**: `16-bit PCM`
* **Samples per Chunk**: `48,000 samples` (~96 KB raw WAV bytes)

Detailed JSON schema is available in [`audio_specs.json`](./audio_specs.json).

---

## 2. Sample Audio Chunks for Model Testing
We have pre-sliced 6 test chunks inside [`sample_chunks/`](./sample_chunks/):
- `chunk_001.wav` to `chunk_006.wav`

You can test your model inference script against these `.wav` files directly to benchmark inference speed and accuracy on short 3-second slices.

---

## 3. Function Contract to Implement

Your model module only needs to expose **one function**: `analyze_chunk(audio_bytes: bytes) -> dict`:

```python
def analyze_chunk(audio_bytes: bytes) -> dict:
    """
    Input:
        audio_bytes (bytes): Raw WAV bytes of a 3-second audio slice (16kHz PCM).
    Output:
        dict:
            - chunk_score (float, 0.0 to 1.0): Risk score (0.0 = Safe human, 1.0 = Deepfake clone)
            - confidence (float, 0.0 to 1.0): Detection confidence
            - flags (list[str]): List of detected artifacts (e.g. ['synthetic_artifact', 'prosody_flatness'])
    """
    return {
        "chunk_score": 0.88,
        "confidence": 0.95,
        "flags": ["synthetic_artifact", "prosody_flatness"]
    }
```

A starter template is provided in [`sample_inference_template.py`](./sample_inference_template.py).

---

## 4. No Rolling Window or Threshold Code Needed!
You do **not** need to write rolling average or threshold logic. The backend's `RollingRiskAggregator` automatically:
1. Maintains the 5-chunk weighted rolling window.
2. Smooths out momentary spikes.
3. Automatically triggers the alert levels (`low < 0.4`, `medium 0.4–0.7`, `high > 0.7`).
4. Broadcasts updates over WebSockets and auto-locks the frontend approval gate.

---

## 5. What to Hand Over for Day 5
When your model is ready, just provide:
1. Your completed `analyze_chunk` Python file.
2. Your model weights file (e.g., `.pt`, `.onnx`, or HuggingFace model repo).
3. Two test WAV recordings for the Evaluation Day pitch demo:
   - `clean_human.wav` (15–20s normal speech)
   - `cloned_voice.wav` (15–20s AI clone speech)
