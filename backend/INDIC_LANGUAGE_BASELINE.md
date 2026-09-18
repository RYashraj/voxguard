# VoxGuard Indian Language Baseline Evaluation Report

This document records an empirical baseline evaluation of VoxGuard's current real Spectra-AASIST3 ML detector on genuine public speech across 5 Indian languages.

## 1. Data Source & Licence Attribution
- **Dataset**: Google FLEURS (Few-shot Learning Evaluation of Universal Speech Models)
- **Source Repository**: [https://huggingface.co/datasets/google/fleurs](https://huggingface.co/datasets/google/fleurs)
- **Paper / Citation**: Conneau et al., *FLEURS: Few-shot Learning Evaluation of Universal Speech Models*, arXiv:2205.12446 (2022).
- **Licence**: Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
- **Genuine Confirmation**: All 10 clips are confirmed genuine (bonafide) human speech recordings from the Google FLEURS validation split. No synthetic, AI-generated, or cloned clips were evaluated.

### Clip Inventory
| Language | Code | Utterance ID | Gender | Duration (s) | Filename |
|---|---|---|---|---|---|
| Hindi | `hi_in` | `1608` | Female | 21.36s | `hi_in_spk1_female_1608.wav` |
| Hindi | `hi_in` | `1602` | Male | 12.24s | `hi_in_spk2_male_1602.wav` |
| Gujarati | `gu_in` | `1595` | Female | 11.88s | `gu_in_spk1_female_1595.wav` |
| Gujarati | `gu_in` | `1560` | Male | 6.30s | `gu_in_spk2_male_1560.wav` |
| Bengali | `bn_in` | `1612` | Female | 6.60s | `bn_in_spk1_female_1612.wav` |
| Bengali | `bn_in` | `1619` | Female | 13.08s | `bn_in_spk2_female_1619.wav` |
| Tamil | `ta_in` | `ta_in_1623` | Female | 14.10s | `ta_in_spk1_female_1623.wav` |
| Tamil | `ta_in` | `ta_in_1644` | Male | 11.10s | `ta_in_spk2_male_1644.wav` |
| Telugu | `te_in` | `te_in_1519` | Female | 10.98s | `te_in_spk1_female_1519.wav` |
| Telugu | `te_in` | `te_in_1577` | Male | 3.84s | `te_in_spk2_male_1577.wav` |

---

## 2. Per-Clip Evaluation Results (Real Spectra-AASIST3 Model)
Evaluated in `VOXGUARD_ML_MODE=real` mode using `backend/scripts/evaluate_indic_language_baseline.py`:

| Language | Utterance ID | Gender | Duration (s) | Chunk Score | Confidence | Alert Level | Public Flags | Latency (s) |
|---|---|---|---|---|---|---|---|---|
| Hindi | `1608` | Female | 21.36s | `0.0000` | `0.9900` | `low` | `none` | 46.11s |
| Hindi | `1602` | Male | 12.24s | `0.0000` | `0.9900` | `low` | `none` | 5.66s |
| Gujarati | `1595` | Female | 11.88s | `0.0000` | `0.9900` | `low` | `none` | 5.85s |
| Gujarati | `1560` | Male | 6.30s | `0.0000` | `0.9900` | `low` | `none` | 5.32s |
| Bengali | `1612` | Female | 6.60s | `0.0000` | `0.9900` | `low` | `none` | 5.99s |
| Bengali | `1619` | Female | 13.08s | `0.0000` | `0.9900` | `low` | `none` | 8.11s |
| Tamil | `1623` | Female | 14.10s | `0.0000` | `0.9900` | `low` | `none` | 8.50s |
| Tamil | `1644` | Male | 11.10s | `0.0000` | `0.9900` | `low` | `none` | 7.01s |
| Telugu | `1519` | Female | 10.98s | `0.0000` | `0.9900` | `low` | `none` | 7.30s |
| Telugu | `1577` | Male | 3.84s | `0.0000` | `0.9900` | `low` | `short_audio` | 4.53s |

---

## 3. Per-Language Summary Table
| Language | Count | Mean Score | Median Score | Min Score | Max Score | Low / Med / High | `synthetic_artifact` Count | Avg Latency (s) |
|---|---|---|---|---|---|---|---|---|
| **Hindi** (`hi_in`) | 2 | `0.0000` | `0.0000` | `0.0000` | `0.0000` | 2 / 0 / 0 | 0 | 25.88s |
| **Gujarati** (`gu_in`) | 2 | `0.0000` | `0.0000` | `0.0000` | `0.0000` | 2 / 0 / 0 | 0 | 5.59s |
| **Bengali** (`bn_in`) | 2 | `0.0000` | `0.0000` | `0.0000` | `0.0000` | 2 / 0 / 0 | 0 | 7.05s |
| **Tamil** (`ta_in`) | 2 | `0.0000` | `0.0000` | `0.0000` | `0.0000` | 2 / 0 / 0 | 0 | 7.75s |
| **Telugu** (`te_in`) | 2 | `0.0000` | `0.0000` | `0.0000` | `0.0000` | 2 / 0 / 0 | 0 | 5.92s |

---

## 4. Explicit Limitations
1. **Genuine-Speech Baseline Only**: This evaluation measures observed false-positive behaviour on genuine public speech across 5 Indian languages. It does **not** prove multilingual deepfake-detection accuracy and must never be described as such.
2. **No Synthetic Spoof Benchmark Evaluated**: No Indian-language synthetic speech or voice-clone benchmark (e.g. Indic TTS / voice clones) has been evaluated yet.
3. **Regional Accent Coverage**: Accent or dialect coverage cannot be claimed from this small 10-clip sample.
4. **Fairness & Telephony Robustness**: Production fairness, language robustness, and telephony-codec robustness require larger, representative, and consented evaluation datasets across diverse Indian languages and telephony conditions.
5. **No Threshold Mutations**: No model parameters, risk thresholds, or classification rules were altered as a result of this evaluation.

---

## 5. Conclusion
> **No high-risk false positives observed in this small genuine-speech sample.**
