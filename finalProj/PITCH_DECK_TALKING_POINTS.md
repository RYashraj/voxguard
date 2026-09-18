# VoxGuard Pitch Deck Talking Points

## Slide 1: The Threat

Voice cloning turns a short voice sample into a convincing social-engineering weapon. A caller can sound familiar while asking for an OTP, PIN, fund transfer, or privileged approval.

## Slide 2: The Product

**VoxGuard is a real-time voice-integrity layer for high-risk calls.** It continuously analyzes streamed audio, enriches the signal with caller and transaction context, and gives the user an actionable risk decision before a sensitive action is approved.

## Slide 3: How It Works

```text
Call audio chunks
      |
      v
Acoustic anti-spoof signal
      |
      +--> Prosody telemetry
      |
      v
Rolling risk engine
      |
      +--> Caller and transaction context
      |
      v
Explainable advisory + transaction gate
```

## Slide 4: The Differentiator

Most demos stop at “fake or real audio.” VoxGuard connects detection to prevention:

- Unknown caller + OTP request -> pause and verify.
- Sustained high spoof risk -> block approval.
- Every decision includes machine-readable reason codes.
- The user sees the recommended next action immediately.

## Slide 5: Live Demo

Use the default **OTP scam preset**:

1. Unknown caller is already selected.
2. OTP/PIN request is already selected.
3. Synthetic benchmark audio is streamed in chunks.
4. Risk rises in the dashboard.
5. `synthetic_artifact` appears.
6. Advisory becomes `block_and_report`.
7. Approve transaction is disabled.

## Slide 6: Privacy By Design

- Audio is processed in memory during the local demo.
- SQLite stores risk metadata, not raw audio, context, or embeddings.
- Reference-speaker embeddings are designed to remain in memory only.
- No banking credentials, OTP values, phone numbers, or account numbers are collected.

## Slide 7: Evidence

Use precise claims:

- Five-chunk weighted rolling risk scoring is implemented and tested.
- Ten genuine Google FLEURS clips across five Indian languages produced zero observed high-risk false positives in the evaluated conditions.
- Selected ASVspoof clips remained high-risk under simulated 8 kHz and 20 dB noise conditions.
- The backend and frontend contracts are covered by automated tests.

Never call the Indian-language result a 0% false-positive rate or multilingual clone-detection accuracy.

## Slide 8: Identity Verification Roadmap

The codebase includes an opt-in ECAPA-TDNN speaker-verification layer for comparing a live chunk with a consented reference embedding.

For the current prototype, it is presented honestly as an auxiliary identity-drift capability. Production integration requires calibration, consent UX, and channel-robust threshold validation.

## Closing Statement

> “VoxGuard does not ask the user to recognize a voice under pressure. It turns acoustic evidence and transaction context into a visible, explainable intervention before the sensitive action is approved.”
