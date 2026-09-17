# VoxGuard Prosody & Behavioural Analysis Layer

## Overview

The VoxGuard Prosody & Behavioural Analysis Layer (`backend/app/ml/prosody.py`) extracts explainable acoustic prosody features from live streaming audio chunks (typically 3.0 seconds). It replaces previous score-threshold-generated flags with true, measured acoustic prosody signals.

---

## Extracted Features & Calculation Methodology

### 1. Pitch / Fundamental Frequency (F0 Mean & Standard Deviation)
- **Feature Names**: `pitch_mean_hz`, `pitch_std_hz`, `pitch_variance`
- **Calculation**: Extracted frame-by-frame (30 ms window, 10 ms hop) using normalized autocorrelation or `librosa.pyin` (fundamental frequency range 65 Hz – 400 Hz). Mean and standard deviation are calculated across valid voiced frames.
- **Purpose**: Natural human speech exhibits pitch micro-variations (f0 standard deviation typically > 12–15 Hz). Unusually low pitch variation (< 8.0 Hz) indicates monotonous pitch contour, common in basic text-to-speech (TTS) systems or flat synthetic voices.

### 2. Voiced-Speech Ratio
- **Feature Name**: `voiced_ratio`
- **Calculation**: Ratio of frames identified as voiced (active pitch detection above noise floor) relative to total analyzed frames in the chunk.
- **Purpose**: Evaluates speech continuity. Low voiced ratios (< 0.20) in non-silent audio indicate fragmented, unvoiced, or heavily degraded audio streams.

### 3. Pause Count & Pause-Duration Ratio
- **Feature Names**: `pause_count`, `pause_duration_ratio`
- **Calculation**: Continuous unvoiced/silent frame blocks lasting longer than 200 ms count as a pause interval. `pause_duration_ratio` measures total pause time relative to total chunk duration.
- **Purpose**: Identifies unnatural hesitations, buffering pauses, or abnormal conversational rhythms (> 40% chunk duration).

### 4. Speech Rate Proxy (Voiced-Burst / Energy-Segment Rate)
- **Feature Name**: `speech_rate_proxy` (expressed in voiced-bursts / second)
- **Calculation**: Counts transitions from unvoiced/silent states to active voiced speech segments divided by total chunk duration in seconds.
- **IMPORTANT DISCLAIMER**: This metric is an acoustic voiced-burst proxy rate. It DOES NOT measure words per minute (WPM) or exact syllables per minute, which require full automatic speech recognition (ASR) / text transcription.

### 5. Jitter & Shimmer Status
- **Feature Names**: `jitter`, `shimmer` (Set to `None`)
- **Justification**: Micro-perturbation analysis (cycle-to-cycle period jitter and amplitude shimmer) requires high-precision glottal pulse tracking on long, uncompressed high-sample-rate speech. On 3-second streaming audio chunks (16 kHz / telephony codecs), frame-based jitter/shimmer estimation is technically unreliable and prone to high noise. Standard pitch variation (`pitch_std_hz`) is used instead as the primary variability signal.

---

## Reason Codes and User-Facing Flags

To maintain UI compatibility while keeping precise internal telemetry, VoxGuard separates internal reason codes from user-facing detection flags:

| Internal Reason Code | User-Facing Flag | Description |
| :--- | :--- | :--- |
| `low_f0_variability` | `prosody_flatness` | Pitch std dev < 8.0 Hz across voiced speech frames. |
| `high_pause_ratio` | `high_pause_ratio` | Pause duration exceeds 40% of total chunk duration. |
| `low_voiced_ratio` | `low_voiced_ratio` | Voiced speech constitutes less than 20% of active frames. |
| `insufficient_speech` | `insufficient_speech` | Audio contains fewer than 5 voiced frames; insufficient data for pitch statistics. |
| `silent_audio` | `silent_audio` | Audio RMS energy < 0.001. |
| `invalid_audio` | `invalid_audio` | Malformed WAV header, corrupt payload, or unparseable format. |
| `prosody_unavailable` | `prosody_unavailable` | Fallback status when prosody extraction encounters an error; does not interrupt Spectra ML inference. |

---

## Threshold Calibration & Initial Heuristic Status

> [!WARNING]
> **INITIAL UNCALIBRATED HEURISTICS**:
> The anomaly detection thresholds defined in `app/ml/prosody.py` (e.g., `LOW_F0_STD_THRESHOLD_HZ = 8.0`, `HIGH_PAUSE_RATIO_THRESHOLD = 0.40`) are initial baseline heuristics. They are NOT clinically, acoustically, or scientifically validated across diverse demographic groups, accents, languages, or telephony codecs.

Score fusion (combining prosody score with Spectra acoustic anti-spoofing score) is intentionally deferred. Fusing uncalibrated prosody scores into core risk alerts can introduce false positives for naturally monotone human speakers or non-native accents.

---

## Critical System Disclaimers

### Why Prosody Alone Cannot Prove Synthetic Speech / AI Cloning
1. **Human Variability**: Naturally monotone human speakers, tired callers, or individuals reading scripted text can produce low pitch variation without AI synthesis.
2. **Supporting Signal Only**: Prosody analysis serves strictly as a supporting, explainable behavioral metric. Proof of AI synthetic cloning requires deep acoustic anti-spoofing neural model classification (Spectra-AASIST3).

### Known Technical Limitations
1. **3-Second Streaming Chunks**: Short 3-second evaluation windows limit the observation of multi-sentence macro-prosody and cadence patterns.
2. **Telephony & Codec Distortion**: Telephony codecs (e.g., AMR, G.711, Opus at low bitrates) strip high-frequency harmonics and alter pitch trajectories, reducing pitch tracking precision.
