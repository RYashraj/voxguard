# ASVspoof 2019 LA Speaker Verification Calibration Benchmark Subset

> [!IMPORTANT]
> **DISCLAIMER & PURPOSE**: This dataset subset is sourced from the public research benchmark **ASVspoof 2019 Logical Access (LA)**. It is strictly used as an offline benchmark calibration set for internal machine learning evaluation of speaker identity drift thresholds.
> **CLEAR STATEMENT**: For internal benchmark calibration only. Not used as a consented customer identity or production enrollment.

---

## Dataset & Licensing Attribution

- **Dataset Name**: ASVspoof 2019 Logical Access (LA) Evaluation Set
- **Source URL**: [`SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA`](https://huggingface.co/datasets/SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA)
- **Licensing & Attribution**: Open Data Commons Attribution License (ODC-By v1.0).
- **Attribution**: ASVspoof 2019 Consortium (Yamagishi et al., "ASVspoof 2019: Future Horizons in Spoofed and Fake Audio Detection").

---

## Benchmark Audio Subset Inventory

All audio clips are 16,000 Hz Mono 16-bit PCM WAV format extracted from `bonafide` evaluation recordings.

| # | Speaker ID | Utterance ID | Label | Duration (s) | Exact Role | File Path |
| :- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `LA_0030` | `LA_E_5849185` | `bonafide` | 4.39 s | `reference` | `reference_speaker/LA_0030_ref_LA_E_5849185.wav` |
| 2 | `LA_0030` | `LA_E_7993804` | `bonafide` | 2.90 s | `same speaker` | `same_speaker/LA_0030_same_LA_E_7993804.wav` |
| 3 | `LA_0030` | `LA_E_5688418` | `bonafide` | 5.71 s | `same speaker` | `same_speaker/LA_0030_same_LA_E_5688418.wav` |
| 4 | `LA_0033` | `LA_E_4581379` | `bonafide` | 2.13 s | `different speaker` | `different_speaker/LA_0033_diff_LA_E_4581379.wav` |
| 5 | `LA_0033` | `LA_E_7824929` | `bonafide` | 2.77 s | `different speaker` | `different_speaker/LA_0033_diff_LA_E_7824929.wav` |
| 6 | `LA_0039` | `LA_E_6314733` | `bonafide` | 2.26 s | `different speaker` | `different_speaker/LA_0039_diff_LA_E_6314733.wav` |
| 7 | `LA_0039` | `LA_E_6670477` | `bonafide` | 1.92 s | `different speaker` | `different_speaker/LA_0039_diff_LA_E_6670477.wav` |

---

## Observed Calibration Results (SpeechBrain ECAPA-TDNN)

Evaluated using `backend/scripts/calibrate_speaker_threshold.py` with SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`):

### Per-File Comparison Telemetry

| File | Known Relationship | Raw Cosine Sim | Bounded Speaker Sim | Identity Drift |
| :--- | :--- | :--- | :--- | :--- |
| `LA_0030_same_LA_E_5688418.wav` | Same Speaker (`LA_0030`) | `0.8617` | `0.9308` | `0.0692` |
| `LA_0030_same_LA_E_7993804.wav` | Same Speaker (`LA_0030`) | `0.4908` | `0.7454` | `0.2546` |
| `LA_0033_diff_LA_E_4581379.wav` | Different Speaker (`LA_0033`) | `0.0827` | `0.5414` | `0.4586` |
| `LA_0033_diff_LA_E_7824929.wav` | Different Speaker (`LA_0033`) | `0.1723` | `0.5861` | `0.4139` |
| `LA_0039_diff_LA_E_6314733.wav` | Different Speaker (`LA_0039`) | `0.1210` | `0.5605` | `0.4395` |
| `LA_0039_diff_LA_E_6670477.wav` | Different Speaker (`LA_0039`) | `0.1577` | `0.5788` | `0.4212` |

### Summary Statistics Table

| Category | Count | Sim Mean (Std) | Drift Mean (Std) | Drift Range [Min, Max] |
| :--- | :--- | :--- | :--- | :--- |
| **Same-Speaker** | 2 | `0.8381` (`0.0927`) | `0.1619` (`0.0927`) | `[0.0692, 0.2546]` |
| **Different-Speaker** | 4 | `0.5667` (`0.0173`) | `0.4333` (`0.0173`) | `[0.4139, 0.4586]` |

### Observed Separation & Suggested Threshold

- **Group Separation**: Clean separation observed. Max same-speaker drift (`0.2546`) is well below min different-speaker drift (`0.4139`), leaving a clear separation gap of `0.1593`.
- **Suggested Threshold Range**: `0.2746` to `0.3939` (Identity Drift).
- **Optimal Midpoint Threshold**: `0.3342` (Identity Drift).

### Key Limitations

1. **Small Sample Size**: Evaluated on 7 clips (2 same-speaker comparisons, 4 different-speaker comparisons).
2. **Audio Duration Variability**: Shorter same-speaker clips (e.g. 2.9s `LA_E_7993804`) show higher drift (`0.2546`) than longer clips (5.7s `LA_E_5688418`, `0.0692`).
3. **Environment & Codec Uniformity**: Benchmark clips are studio-quality 16 kHz WAVs without telephony codec compression (e.g. G.711 / AMR-WB) or ambient room noise.

---

## Calibration Usage Command

```bash
python backend/scripts/calibrate_speaker_threshold.py \
  --reference backend/data/benchmark_speaker_calibration/reference_speaker/LA_0030_ref_LA_E_5849185.wav \
  --same-dir backend/data/benchmark_speaker_calibration/same_speaker \
  --diff-dir backend/data/benchmark_speaker_calibration/different_speaker
```
