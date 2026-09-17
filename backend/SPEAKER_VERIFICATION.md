1: # VoxGuard Consent-Based Speaker Verification & Identity Drift Layer
2: 
3: ## Overview
4: 
5: The VoxGuard Speaker Verification & Identity Drift Layer (`backend/app/ml/speaker_verification.py`) provides cross-session speaker identity consistency tracking. It compares ongoing call audio chunks against a consented genuine reference voice embedding using a deep ECAPA-TDNN speaker embedding architecture (`speechbrain/spkrec-ecapa-voxceleb`) and cosine similarity scoring.
6: 
7: ---
8: 
9: ## Reference Audio Path Safety & Privacy Controls
10: 
11: 1. **Local Demo Reference Path Safety**:
12:    - `reference_audio_path` is for **local demo use only**.
13:    - Paths are accepted **only** if they resolve strictly inside the directory:
14:      ```text
15:      backend/data/consented_reference_audio/
16:      ```
17:    - Any path attempting directory traversal (e.g. `../`), referencing locations outside the allowed folder, pointing to non-WAV files, referencing missing files, or containing invalid WAV headers is strictly rejected with a clear status code (`invalid_reference_path`).
18: 
19: 2. **Explicit User Consent & In-Memory Only**:
20:    - Reference voice audio MUST be explicitly consented by the caller/user prior to session enrollment.
21:    - Audio bytes and computed 192-dimensional speaker embeddings are stored **ONLY IN MEMORY** inside active `SessionIdentityTracker` instances.
22: 
23: 3. **Zero Persistence & Copying**:
24:    - Reference audio files are **NEVER** copied to disk, saved to databases, or uploaded to cloud endpoints during enrollment.
25:    - Upon session termination or clearing (`tracker.clear()`), reference embeddings are immediately erased from memory.
26: 
27: ---
28: 
29: ## Technical Architecture & Calculation Methodology
30: 
31: ### 1. Reference Enrollment
32: - At session initialization, a consented 16 kHz WAV reference audio path inside `backend/data/consented_reference_audio/` or raw bytes is passed to `enroll_reference_path()` or `enroll_reference()`.
33: - The path is validated using strict resolution checks (`validate_consented_reference_path()`).
34: - The SpeechBrain ECAPA-TDNN classifier encodes the reference waveform into a 192-dimensional embedding vector $v_{\text{ref}}$.
35: - The raw reference audio buffer is discarded, leaving only $v_{\text{ref}}$ in memory.
36: 
37: ### 2. Chunk Verification & Similarity Semantics
38: - For each incoming call audio chunk, the model encodes a chunk embedding vector $v_{\text{chunk}}$.
39: - **Raw Cosine Similarity** is preserved internally for diagnostic precision:
40:   $$\text{raw\_cosine\_similarity} = \frac{v_{\text{ref}} \cdot v_{\text{chunk}}}{\|v_{\text{ref}}\| \|v_{\text{chunk}}\|}$$
41: - **Bounded Speaker Similarity** is reported as a clearly documented bounded 0–1 value:
42:   $$\text{speaker\_similarity} = \max\left(0.0, \min\left(1.0, \frac{\text{raw\_cosine\_similarity} + 1.0}{2.0}\right)\right)$$
43: - **Identity Drift** is derived as:
44:   $$\text{identity\_drift} = 1.0 - \text{speaker\_similarity}$$
45: 
46: ### 3. Reason Codes and Flags
47: 
48: | Status Code | Description | User/UI Flag |
49: | :--- | :--- | :--- |
50: | `ok` | Speaker embedding successfully computed and compared. | `identity_mismatch` (if `identity_drift > 0.45`) |
51: | `invalid_reference_path` | Reference audio path is outside `consented_reference_audio/`, missing, or invalid WAV. | `invalid_reference_path` |
52: | `reference_unavailable` | No reference audio was enrolled for the active session. | `reference_unavailable` |
53: | `insufficient_speech` | Chunk duration < 0.5s or contains insufficient voiced frames. | `insufficient_speech` |
54: | `silent_audio` | Chunk RMS energy < 0.001. | `silent_audio` |
55: | `identity_unavailable` | SpeechBrain dependency or model weights unavailable. | `identity_unavailable` |
56: 
57: ---
58: 
59: ## Calibration & Threshold Guidance
60: 
61: > [!IMPORTANT]
62: > The default mismatch threshold (`identity_drift > 0.45`) is an initial baseline demo heuristic. It MUST be calibrated against real same-speaker and different-speaker dataset measurements before operational deployment. Identity drift does **NOT** automatically alter alert levels, rolling risk, or transaction decisions.
63: 
64: ### Calibration Helper Script
65: VoxGuard includes an offline threshold calibration utility:
66: ```bash
67: python backend/scripts/calibrate_speaker_threshold.py --same-dir <path_to_same_speaker_wavs> --diff-dir <path_to_diff_speaker_wavs> [--ref <reference_wav>]
68: ```
69: 
70: - **Inputs**: Directories containing explicitly consented same-speaker WAVs and different-speaker WAVs.
71: - **Output**: Formatted table of pairwise similarity and drift metrics, along with recommended threshold ranges based on observed score distributions.
72: - **Safety Guarantee**: Operates completely offline, without downloading models or accessing unconsented voice data.
73: 
74: ---
75: 
76: ## Critical System Disclaimers
77: 
78: ### Spoof Detection vs. Speaker Verification
79: 
80: | Metric | Core Model | Question Answered |
81: | :--- | :--- | :--- |
82: | **Acoustic Anti-Spoofing** | Spectra-AASIST3 (`chunk_score`) | *"Is this voice signal generated by an AI model/cloner or a real human mouth?"* |
83: | **Speaker Verification** | SpeechBrain ECAPA-TDNN (`identity_drift`) | *"Does this voice signal match the enrolled reference identity for this call session?"* |
84: 
85: ### Why Speaker Mismatch Does NOT Prove AI Cloning
86: 1. **Legitimate Speaker Swaps**: A call handoff, co-caller, or background speaker intervention produces a high identity drift (speaker mismatch), even though both speakers are live humans.
87: 2. **Channel & Mic Variation**: Switching from a speakerphone to a headset or changing network codecs can alter spectral color, increasing identity drift.
88: 3. **Independent Signals**: Speaker identity drift is a security context signal. AI deepfake detection requires Spectra-AASIST3 acoustic classification.
89: 
90: ---
91: 
92: ## Limitations on Short Telephony Audio
93: - **Chunk Windowing**: 3-second streaming chunks contain limited phonetic variability compared to full 10-second enrollment phrases.
94: - **Noise & Codecs**: Telephony codecs (e.g., AMR-WB, G.711) and background noise degrade embedding alignment, requiring safe fallback status (`insufficient_speech`).

