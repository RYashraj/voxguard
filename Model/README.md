# VOXGUARD — Voice Deepfake Detection

VOXGUARD is an AI-powered cybersecurity solution designed to detect AI-generated and cloned voices in real time and identify potential voice impersonation attacks.

## Current ML Module

The current ML module evaluates incoming audio using two pretrained speech models:

### 1. Spectra-AASIST3
- Speech anti-spoofing model
- Detects whether speech is genuine or spoofed/synthetic
- Input: 16 kHz mono audio
- Class 0: Spoof / Fake
- Class 1: Bona fide / Real

### 2. Bisher Wav2Vec2 Deepfake Audio Detection
- Fine-tuned Wav2Vec2 audio classification model
- Class 0: Fake
- Class 1: Real
- Currently used as a baseline for comparison

## Current Testing

Initial testing has been performed using genuine and AI-cloned voice samples.

| Test | Audio | Actual Type | Bisher | Spectra-AASIST3 |
|---|---|---|---|---|
| T001 | clone_1.wav | AI-Cloned | REAL ❌ | FAKE ✅ |
| T002 | real_1.wav | Genuine | REAL ✅ | REAL ✅ |
| T003 | clone_2.wav | AI-Cloned | REAL ❌ | FAKE ✅ |

### Initial Observation

- Bisher: 1/3 correct
- Spectra-AASIST3: 3/3 correct
- Two false negatives were observed with Bisher.
- Spectra correctly detected both tested AI-cloned samples.

These results are based on a small initial test set and should not be considered final model accuracy.

## Testing Strategy

Future testing will evaluate:

- Genuine voices
- AI-cloned voices
- Different speakers
- Short audio samples
- Noisy audio
- Compressed / telephone-quality audio
- Different accents and languages
- Unseen voice-cloning methods
- False positives and false negatives

## Current Architecture

Incoming Audio
↓
Audio Preprocessing
↓
Deepfake Detection
↓
Risk Score
↓
Alert / Verification Recommendation

The planned system will process audio in short chunks to support real-time risk assessment.

## Future Enhancements

### Speaker Verification
An optional second layer using a speaker-verification model such as ECAPA-TDNN can be added for enrolled trusted contacts.

This layer would verify:

"Is this actually the person they claim to be?"

It would complement deepfake detection rather than replace it.

### Additional Future Improvements

- Robustness against telephone compression and noise
- Detection of unseen cloning techniques
- Indian language and regional accent testing
- Context-aware fraud risk assessment
- Privacy-preserving / edge inference
- Improved adaptive risk scoring

## Project Structure

ml_model.py
requirements.txt
README.md
.gitignore

Local files such as virtual environments, test audio, results, and downloaded model weights are excluded from the repository.

## Disclaimer

The current results are preliminary and are intended for research and development. Model performance will be evaluated on a larger and more diverse test set before deployment.