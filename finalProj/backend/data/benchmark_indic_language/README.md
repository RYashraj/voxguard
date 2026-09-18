# VoxGuard Indic Language Baseline Benchmark Dataset

This directory contains metadata and local calibration clips for VoxGuard's baseline evaluation on genuine public speech across Indian languages.

## Dataset Attribution & Provenance
- **Dataset Name**: Google FLEURS (Few-shot Learning Evaluation of Universal Speech Models)
- **Source Repository**: [https://huggingface.co/datasets/google/fleurs](https://huggingface.co/datasets/google/fleurs)
- **Paper / Citation**: Conneau et al., *FLEURS: Few-shot Learning Evaluation of Universal Speech Models*, arXiv:2205.12446 (2022).
- **Licence**: Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
- **Confirmation**: All selected clips are confirmed genuine (bonafide) human speech recordings from the Google FLEURS validation split. No synthetic or voice-clone clips are included.

## Languages Evaluated
1. **Hindi** (`hi_in`)
2. **Gujarati** (`gu_in`)
3. **Bengali** (`bn_in`)
4. **Tamil** (`ta_in`)
5. **Telugu** (`te_in`)

## Inventory of Clips (10 Clips Total)
| Language | Code | Speaker ID | Gender | Utterance ID | Audio File |
|---|---|---|---|---|---|
| Hindi | `hi_in` | `hi_in_spk1` | Female | `1608` | `hi_in_spk1_female_1608.wav` |
| Hindi | `hi_in` | `hi_in_spk2` | Male | `1602` | `hi_in_spk2_male_1602.wav` |
| Gujarati | `gu_in` | `gu_in_spk1` | Female | `1595` | `gu_in_spk1_female_1595.wav` |
| Gujarati | `gu_in` | `gu_in_spk2` | Male | `1560` | `gu_in_spk2_male_1560.wav` |
| Bengali | `bn_in` | `bn_in_spk1` | Female | `1612` | `bn_in_spk1_female_1612.wav` |
| Bengali | `bn_in` | `bn_in_spk2` | Female | `1619` | `bn_in_spk2_female_1619.wav` |
| Tamil | `ta_in` | `ta_in_spk1` | Female | `1623` | `ta_in_spk1_female_1623.wav` |
| Tamil | `ta_in` | `ta_in_spk2` | Male | `1644` | `ta_in_spk2_male_1644.wav` |
| Telugu | `te_in` | `te_in_spk1` | Female | `1519` | `te_in_spk1_female_1519.wav` |
| Telugu | `te_in` | `te_in_spk2` | Male | `1577` | `te_in_spk2_male_1577.wav` |

## Storage Policy
Audio files (`*.wav`) are git-ignored via `.gitignore` to prevent committing binary audio data to the codebase. `manifest.json` and `README.md` remain version-controlled.
