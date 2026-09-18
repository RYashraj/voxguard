# VoxGuard Prosody Layer Benchmark Evaluation Results

> [!IMPORTANT]
> **DISCLAIMER & PURPOSE**: This document records an offline, evidence-based benchmark validation of VoxGuard's prosody analysis layer (`backend/app/ml/prosody.py`). The evaluation was conducted across public genuine (bonafide) and synthetic (spoof) audio clips from the **ASVspoof 2019 Logical Access (LA)** evaluation dataset.
> **KEY DISCLAIMER**: Prosody metrics are explainable supporting signals ONLY and DO NOT constitute proof of AI synthetic cloning.

---

## 1. Dataset Source & Sample Inventory

- **Dataset Source**: [`SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA`](https://huggingface.co/datasets/SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA)
- **Licensing & Attribution**: Open Data Commons Attribution License (ODC-By v1.0). Attribution: *ASVspoof 2019 Consortium (Yamagishi et al.)*.
- **Total Clips Evaluated**: `13 clips` (`7 bonafide`, `6 spoof`)
- **Additional Downloads**: `0` (Used existing repository benchmark clips).

### Sample Breakdown

1. **Bonafide Human Speech Clips** (7 clips from `backend/data/benchmark_speaker_calibration/`):
   - Reference Speaker (`LA_0030`): `LA_E_5849185` (4.39s)
   - Same Speaker (`LA_0030`): `LA_E_7993804` (2.90s), `LA_E_5688418` (5.71s)
   - Different Speaker B (`LA_0033`): `LA_E_4581379` (2.13s), `LA_E_7824929` (2.77s)
   - Different Speaker C (`LA_0039`): `LA_E_6314733` (2.26s), `LA_E_6670477` (1.92s)

2. **Synthetic Spoof Speech Clips** (6 clips from `backend/data/test_audio/asvspoof_spoof_clips/`):
   - Algorithm A09 (Neural TTS/VC): `LA_E_6977360` (1.96s), `LA_E_6163791` (1.90s)
   - Algorithm A11 (Griffin-Lim / Neural Vocoder): `LA_E_2834763` (1.43s)
   - Algorithm A13 (WaveNet / Neural Vocoder): `LA_E_5932896` (5.80s)
   - Algorithm A14 (Neural Waveform Synthesizer): `LA_E_8877452` (3.98s)
   - Algorithm A16 (Waveform Concatenation / Neural VC): `LA_E_6828287` (1.56s)

---

## 2. Per-Clip Telemetry Results

Evaluated using `backend/scripts/evaluate_prosody_benchmark.py` directly on original 16 kHz WAV audio bytes (preserving original chunk durations):

| Utterance ID | Known Label | Duration (s) | Status | F0 Mean (Hz) | F0 Std (Hz) | Voiced Ratio | Pause Ratio | Speech Rate Proxy | Prosody Score | User Flags / Reason Codes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LA_0030_ref_LA_E_5849185.wav` | `bonafide` | 4.39 s | `ok` | 81.5 Hz | 9.1 Hz | 0.61 | 0.15 | 4.55 Hz | 0.0500 | `none` |
| `LA_0030_same_LA_E_5688418.wav` | `bonafide` | 5.71 s | `ok` | 87.1 Hz | 9.7 Hz | 0.55 | 0.23 | 5.78 Hz | 0.0500 | `none` |
| `LA_0030_same_LA_E_7993804.wav` | `bonafide` | 2.90 s | `ok` | 88.5 Hz | 9.4 Hz | 0.45 | 0.26 | 6.90 Hz | 0.0500 | `none` |
| `LA_0033_diff_LA_E_4581379.wav` | `bonafide` | 2.13 s | `ok` | 215.1 Hz | 21.3 Hz | 0.31 | 0.60 | 1.41 Hz | 0.5000 | `high_pause_ratio` |
| `LA_0033_diff_LA_E_7824929.wav` | `bonafide` | 2.77 s | `ok` | 193.6 Hz | 46.0 Hz | 0.62 | 0.22 | 2.53 Hz | 0.0500 | `none` |
| `LA_0039_diff_LA_E_6314733.wav` | `bonafide` | 2.26 s | `ok` | 158.1 Hz | 64.8 Hz | 0.61 | 0.14 | 6.20 Hz | 0.0500 | `none` |
| `LA_0039_diff_LA_E_6670477.wav` | `bonafide` | 1.92 s | `ok` | 221.2 Hz | 18.6 Hz | 0.29 | 0.58 | 2.09 Hz | 0.5000 | `high_pause_ratio` |
| `LA_E_2834763.wav` | `spoof` (A11) | 1.43 s | `ok` | 207.1 Hz | 10.8 Hz | 0.66 | 0.00 | 3.50 Hz | 0.0500 | `none` |
| `LA_E_5932896.wav` | `spoof` (A13) | 5.80 s | `ok` | 180.7 Hz | 29.1 Hz | 0.64 | 0.08 | 3.96 Hz | 0.0500 | `none` |
| `LA_E_6163791.wav` | `spoof` (A09) | 1.90 s | `ok` | 93.8 Hz | 16.0 Hz | 0.53 | 0.31 | 3.69 Hz | 0.0500 | `none` |
| `LA_E_6828287.wav` | `spoof` (A16) | 1.56 s | `ok` | 80.5 Hz | 7.0 Hz | 0.52 | 0.19 | 6.41 Hz | 0.6429 | `prosody_flatness` |
| `LA_E_6977360.wav` | `spoof` (A09) | 1.96 s | `ok` | 168.9 Hz | 24.2 Hz | 0.80 | 0.00 | 2.04 Hz | 0.0500 | `none` |
| `LA_E_8877452.wav` | `spoof` (A14) | 3.98 s | `ok` | 189.8 Hz | 32.5 Hz | 0.65 | 0.00 | 4.02 Hz | 0.0500 | `none` |

---

## 3. Group-Level Summary Statistics

| Metric | Group | Count | Mean | Median | Minimum | Maximum |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F0 Mean (Hz)** | `bonafide` | 7 | 149.27 Hz | 158.07 Hz | 81.46 Hz | 221.16 Hz |
| | `spoof` | 6 | 153.46 Hz | 174.78 Hz | 80.48 Hz | 207.05 Hz |
| **F0 Standard Deviation (Hz)** | `bonafide` | 7 | 25.54 Hz | 18.60 Hz | 9.05 Hz | 64.81 Hz |
| | `spoof` | 6 | 19.93 Hz | 20.10 Hz | 7.02 Hz | 32.54 Hz |
| **Voiced Speech Ratio** | `bonafide` | 7 | 0.4901 | 0.5455 | 0.2917 | 0.6173 |
| | `spoof` | 6 | 0.6338 | 0.6456 | 0.5192 | 0.8020 |
| **Pause Duration Ratio** | `bonafide` | 7 | 0.3115 | 0.2325 | 0.1372 | 0.6009 |
| | `spoof` | 6 | 0.0948 | 0.0387 | 0.0000 | 0.3053 |
| **Speech Rate Proxy (Hz)** | `bonafide` | 7 | 4.21 Hz | 4.55 Hz | 1.41 Hz | 6.90 Hz |
| | `spoof` | 6 | 3.94 Hz | 3.83 Hz | 2.04 Hz | 6.41 Hz |
| **Prosody Score** | `bonafide` | 7 | 0.1786 | 0.0500 | 0.0500 | 0.5000 |
| | `spoof` | 6 | 0.1488 | 0.0500 | 0.0500 | 0.6429 |

---

## 4. Evaluation Conclusion

**Selected Conclusion Outcome**:
> **“Prosody does not show reliable separation on this sample and must remain informational only.”**

### Rationale:
1. **Overlap in Feature Distributions**: Pitch variability (`F0 std`), speech rate, and pitch means show substantial overlap between genuine human speech and synthetic speech clips. Modern neural vocoders (e.g. A09, A13, A14) synthesize natural prosodic inflection that falls well within normal human pitch variation ranges.
2. **False Positives on Natural Speech**: 2 out of 7 bonafide human clips triggered `high_pause_ratio` due to standard conversational pauses, resulting in higher average prosody scores (`0.1786`) for genuine human speech than for synthetic speech (`0.1488`).
3. **False Negatives on Synthetic Speech**: 5 out of 6 spoof clips passed with baseline prosody scores (`0.0500`), indicating that pitch flatness heuristics alone do not catch modern neural speech synthesis.

---

## 5. Explicit System Guarantees & Constraints

- **Small Benchmark Scope**: This is an internal benchmark evaluation across 13 public clips and does NOT represent production classification accuracy across full caller populations.
- **Not Proof of AI Cloning**: Acoustic prosody metrics alone DO NOT constitute proof that speech is synthetically generated or cloned.
- **Untuned Heuristics**: No prosody thresholds were tuned or fitted on this evaluation set.
- **Strict Control Flow Scoping**: Prosody scores and flags MUST NOT alter alert levels, rolling risk scores, WebSocket payload contracts, SQLite logs, or transaction execution decisions.
- **External Variance Disclaimer**: Accent, native language, microphone frequency response, emotional expressiveness, and telephony codecs (e.g., AMR-WB, G.711) introduce natural prosodic variations that require acoustic anti-spoofing models (Spectra-AASIST3) for primary classification.
