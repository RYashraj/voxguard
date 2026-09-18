# VoxGuard Telephony Robustness Baseline Evaluation

This document presents the empirical robustness baseline for VoxGuard's core Spectra-AASIST3 ML spoof detection pipeline evaluated under simulated telephone call-quality conditions.

> [!IMPORTANT]
> **Evaluation Scope & Safety Guarantee**
> - **Zero Model/Code Alteration**: Model weights, detection thresholds (`>0.70` high, `0.40-0.70` medium, `<0.40` low), rolling risk aggregation, contextual policy, WebSocket schemas, SQLite logging, and frontend code remain completely untouched.
> - **Public Benchmark Data Only**: Uses 3 genuine Indic language speech samples from Google FLEURS and 3 synthetic spoof samples from ASVspoof 2019 LA. No private, customer, or unconsented recordings were used.
> - **In-Memory Audio Processing**: Transformed audio streams were processed in-memory during evaluation; no transformed WAV audio files are committed to the repository.
> - **Prosody Signal Quarantine**: Quarantined prosody heuristics were verified and remain strictly excluded from public risk payloads and flag outputs.

---

## 1. Selected Clips & Call-Quality Profiles

### Balanced Evaluation Subset (6 Audio Clips)

| Clip ID | Class | Language / Source | Native File | Duration |
|---|---|---|---|---|
| `hi_in_spk1_female_1608` | Genuine (`bonafide`) | Hindi (Google FLEURS) | `data/benchmark_indic_language/hi_in_spk1_female_1608.wav` | 21.36s |
| `ta_in_spk1_female_1623` | Genuine (`bonafide`) | Tamil (Google FLEURS) | `data/benchmark_indic_language/ta_in_spk1_female_1623.wav` | 14.10s |
| `te_in_spk1_female_1519` | Genuine (`bonafide`) | Telugu (Google FLEURS) | `data/benchmark_indic_language/te_in_spk1_female_1519.wav` | 10.98s |
| `LA_E_5932896` | Synthetic (`spoof`) | ASVspoof 2019 LA | `data/test_audio/asvspoof_spoof_clips/LA_E_5932896.wav` | 5.80s |
| `LA_E_8877452` | Synthetic (`spoof`) | ASVspoof 2019 LA | `data/test_audio/asvspoof_spoof_clips/LA_E_8877452.wav` | 3.98s |
| `LA_E_6977360` | Synthetic (`spoof`) | ASVspoof 2019 LA | `data/test_audio/asvspoof_spoof_clips/LA_E_6977360.wav` | 1.96s |

### Simulated Telephony Call-Quality Profiles (3 Profiles)

Each clip was evaluated across 3 deterministic simulated conditions (18 total evaluation runs):

1. **`original`**: Unmodified 16 kHz 16-bit mono PCM input audio.
2. **`narrowband_8khz`**: Simulated telephone-style 8 kHz band-limiting via downsampling (16 kHz → 8 kHz) and anti-aliased reconstruction back to pipeline format (8 kHz → 16 kHz).
3. **`narrowband_8khz_noise_20db`**: The 8 kHz narrowband signal mixed with deterministic additive white Gaussian noise at 20 dB Signal-to-Noise Ratio (SNR) using a fixed random seed (`seed=42`).

---

## 2. Per-Clip & Per-Profile Evaluation Results

Evaluated with `VOXGUARD_ML_MODE=real` on the real Spectra-AASIST3 detection engine:

| Clip ID | Label | Profile | Chunk Score | Alert Level | Confidence | Latency | Public Flags |
|---|---|---|---|---|---|---|---|
| `hi_in_spk1_female_1608` | `bonafide` | `original` | `0.0000` | `low` | `0.99` | 48.88s | `[]` |
| `hi_in_spk1_female_1608` | `bonafide` | `narrowband_8khz` | `0.0000` | `low` | `0.99` | 11.55s | `[]` |
| `hi_in_spk1_female_1608` | `bonafide` | `narrowband_8khz_noise_20db` | `0.0000` | `low` | `0.99` | 9.24s | `[]` |
| `ta_in_spk1_female_1623` | `bonafide` | `original` | `0.0000` | `low` | `0.99` | 8.23s | `[]` |
| `ta_in_spk1_female_1623` | `bonafide` | `narrowband_8khz` | `0.0000` | `low` | `0.99` | 6.87s | `[]` |
| `ta_in_spk1_female_1623` | `bonafide` | `narrowband_8khz_noise_20db` | `0.0000` | `low` | `0.99` | 6.83s | `[]` |
| `te_in_spk1_female_1519` | `bonafide` | `original` | `0.0000` | `low` | `0.99` | 6.02s | `[]` |
| `te_in_spk1_female_1519` | `bonafide` | `narrowband_8khz` | `0.0000` | `low` | `0.99` | 5.79s | `[]` |
| `te_in_spk1_female_1519` | `bonafide` | `narrowband_8khz_noise_20db` | `0.0000` | `low` | `0.99` | 5.90s | `[]` |
| `LA_E_5932896` | `spoof` | `original` | `0.9898` | `high` | `0.98` | 4.50s | `["synthetic_artifact"]` |
| `LA_E_5932896` | `spoof` | `narrowband_8khz` | `0.9987` | `high` | `0.99` | 5.11s | `["synthetic_artifact"]` |
| `LA_E_5932896` | `spoof` | `narrowband_8khz_noise_20db` | `0.9998` | `high` | `0.99` | 4.57s | `["synthetic_artifact"]` |
| `LA_E_8877452` | `spoof` | `original` | `0.9810` | `high` | `0.96` | 4.17s | `["short_audio", "synthetic_artifact"]` |
| `LA_E_8877452` | `spoof` | `narrowband_8khz` | `0.9923` | `high` | `0.98` | 4.35s | `["short_audio", "synthetic_artifact"]` |
| `LA_E_8877452` | `spoof` | `narrowband_8khz_noise_20db` | `0.9986` | `high` | `0.99` | 4.16s | `["short_audio", "synthetic_artifact"]` |
| `LA_E_6977360` | `spoof` | `original` | `0.9985` | `high` | `0.99` | 3.55s | `["short_audio", "synthetic_artifact"]` |
| `LA_E_6977360` | `spoof` | `narrowband_8khz` | `0.9987` | `high` | `0.99` | 3.40s | `["short_audio", "synthetic_artifact"]` |
| `LA_E_6977360` | `spoof` | `narrowband_8khz_noise_20db` | `0.9999` | `high` | `0.99` | 3.39s | `["short_audio", "synthetic_artifact"]` |

---

## 3. Summary Statistics by Class & Profile

### Genuine Speech Class Summary (`bonafide`, 9 evaluations)

| Metric | Overall Value | `original` | `narrowband_8khz` | `narrowband_8khz_noise_20db` |
|---|---|---|---|---|
| **Evaluated Clips** | 9 | 3 | 3 | 3 |
| **Mean Chunk Score** | `0.0000` | `0.0000` | `0.0000` | `0.0000` |
| **Median Chunk Score** | `0.0000` | `0.0000` | `0.0000` | `0.0000` |
| **Min / Max Score** | `0.0000 / 0.0000` | `0.0000 / 0.0000` | `0.0000 / 0.0000` | `0.0000 / 0.0000` |
| **Alert Level (Low / Med / High)** | `9 / 0 / 0` | `3 / 0 / 0` | `3 / 0 / 0` | `3 / 0 / 0` |
| **High-Risk False Positives** | **0** | **0** | **0** | **0** |
| **Synthetic Artifact Flags** | **0** | **0** | **0** | **0** |

### Synthetic Spoof Class Summary (`spoof`, 9 evaluations)

| Metric | Overall Value | `original` | `narrowband_8khz` | `narrowband_8khz_noise_20db` |
|---|---|---|---|---|
| **Evaluated Clips** | 9 | 3 | 3 | 3 |
| **Mean Chunk Score** | `0.9953` | `0.9898` | `0.9966` | `0.9994` |
| **Median Chunk Score** | `0.9987` | `0.9898` | `0.9987` | `0.9998` |
| **Min / Max Score** | `0.9810 / 0.9999` | `0.9810 / 0.9985` | `0.9923 / 0.9987` | `0.9986 / 0.9999` |
| **Alert Level (Low / Med / High)** | `0 / 0 / 9` | `0 / 0 / 3` | `0 / 0 / 3` | `0 / 0 / 3` |
| **High-Risk True Positives** | **9 / 9 (100%)** | **3 / 3 (100%)** | **3 / 3 (100%)** | **3 / 3 (100%)** |
| **Synthetic Artifact Flags** | **9 / 9 (100%)** | **3 / 3 (100%)** | **3 / 3 (100%)** | **3 / 3 (100%)** |

---

## 4. Findings & Selected Empirical Conclusion

> [!NOTE]
> **Selected Empirical Conclusion**
> **"No material degradation observed in this small simulated sample."**

Key Empirical Findings:
1. **Zero Genuine False Positives**: All genuine Indic speech samples maintained `chunk_score = 0.0000` and `alert_level = low` across all simulated telephony profiles.
2. **Robust Spoof Detection**: All synthetic spoof samples maintained `chunk_score >= 0.9810` (up to `0.9999`) and triggered `alert_level = high` with the `synthetic_artifact` flag across both 8 kHz narrowband downsampling and 20 dB SNR noise.
3. **Quarantine Verification**: Zero prosody-only heuristics (`prosody_flatness`, `prosody_pitch_instability`, etc.) appeared in the public flag outputs.

---

## 5. Explicit Limitations & Future Evaluation Needs

> [!WARNING]
> **Required Technical Limitations**
> - **Small Sample Size**: This evaluation uses a small, controlled 6-clip baseline (3 genuine, 3 spoof). It serves as a preliminary sanity check, not a full statistical benchmark.
> - **Simulated Telephony vs Real Cellular Networks**: Resampling to 8 kHz and adding 20 dB Gaussian noise does not model real telecom carrier codecs (e.g., AMR-NB, AMR-WB, Opus), packet loss, acoustic reverberation, or microphone distortions.
> - **Not Accuracy / EER / FAR / FRR Metrics**: Results represent single-chunk sample observations and must not be cited as standard performance metrics (Equal Error Rate, False Acceptance Rate, False Rejection Rate).
> - **No Production Threshold Tuning**: Production thresholds (`0.70` high, `0.40` low) were not tuned or fitted to these results and must remain unadjusted until large-scale validation occurs.
> - **Broader Evaluation Required**: Production readiness requires comprehensive benchmarking across diverse real-world telecom codecs, noisy environmental conditions, varied Indian regional dialects/accents, and modern generative voice clone architectures.
