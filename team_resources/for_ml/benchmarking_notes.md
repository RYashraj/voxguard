# ML Benchmarking & Optimization Notes (Hetvi & Nandini)

This guide contains performance tips, latency targets, and architecture recommendations for our deepfake voice detection pipeline.

---

## 1. Latency Targets for Real-Time Live Streaming

Because audio chunks arrive in **3.0-second windows**:
* **Target Inference Latency**: `< 1,000 ms` (1.0 second) per chunk.
* **Ideal Streaming Latency**: `< 500 ms` for real-time live feeling.
* **Warm vs Cold Start**: Initial model weight loading takes longer on first import. The backend uses a **Singleton pattern** (`SpectraAASISTDetector`) so loading happens only once on startup.

---

## 2. Audio Processing Rules

1. **Sampling Rate**: Always convert or resample to `16,000 Hz` (`16 kHz`).
2. **Channel Format**: Mono (1 channel).
3. **Bit Depth**: 16-bit PCM integer scaled to `float32` $[-1.0, 1.0]$.
4. **Length Padding**:
   - `Spectra-AASIST3` requires fixed length `64,600 samples` (~4.03s).
   - If chunk is shorter, repeat/tile the waveform using `np.tile(audio, repeats)[:64600]`.

---

## 3. How Anomaly Flags Work

Your model can output custom flags in the `flags` list. The backend displays them in real time:

| Flag Name | Meaning | Suggested Trigger Threshold |
| :--- | :--- | :--- |
| `synthetic_artifact` | High probability of AI synthesis or phase vocoder artifacts | `chunk_score > 0.70` |
| `prosody_flatness` | Unnatural pitch / rhythm consistency | `chunk_score > 0.40` |
| `spectral_discontinuity` | Sudden spectral shifts between phonemes | Moderate anomalies |
| `short_audio` | Audio slice was under the target length and was padded | Auto-flagged by parser |
| `silent_audio` | Low RMS energy below threshold ($< 0.001$) | Auto-flagged by parser |

---

## 4. Optimization Recommendations

If CPU inference latency is $> 1,500$ ms on laptops without CUDA:
1. **GPU Acceleration**: Set PyTorch device to `cuda` if available:
   ```python
   device = "cuda" if torch.cuda.is_available() else "cpu"
   model = model.to(device)
   ```
2. **ONNX Runtime Conversion**: Converting PyTorch models to ONNX Runtime typically yields a $3\times$ to $5\times$ speedup on CPU.
3. **Quantization**: Using `torch.quantization.quantize_dynamic` on linear layers can reduce latency by ~40%.
