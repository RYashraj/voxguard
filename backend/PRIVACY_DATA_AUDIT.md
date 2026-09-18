# VoxGuard Privacy, Consent, and Data-Retention Audit

This document records the privacy, consent, and data-retention audit for the VoxGuard real-time voice impersonation detection architecture.

---

## 1. Data-Flow Table

| Data Item | Purpose | Storage Location | Retention Period | Protections & Controls |
|---|---|---|---|---|
| **Transient Live-Call Audio** | Real-time acoustic & deepfake feature extraction | In-Memory (RAM) | Discarded immediately after chunk analysis | Never written to disk or SQLite database; processed in volatile RAM only |
| **Consented Reference WAV** | Optional local speaker identity verification | `backend/data/consented_reference_audio/` | Local demo testing only | Excluded from Git via `.gitignore`; optional caller consent model |
| **Speaker Reference Embedding** | In-memory identity drift comparison | Volatile RAM (`SessionIdentityTracker`) | Active call session duration | Cleared via `finally` block on normal call completion, stop, or error exit paths |
| **Derived Risk Scores & Flags** | Operational security monitoring & advisory policy | SQLite `chunk_history` (`backend/data/voxguard.db`) | Local database session history | Allowlisted metadata fields only; no PII, raw audio, or local paths stored |
| **Contextual Transaction Data** | Pre-transaction advisory recommendation | Volatile RAM (`SessionContextManager`) | Active call session duration | Stored in memory only; never persisted to SQLite or disk |
| **Public Benchmark Assets** | Baseline model evaluation & calibration | `backend/data/benchmark_*` | Read-only research assets | Public academic dataset clips (ASVspoof, Google FLEURS) with clear CC-BY/ODC-By licences; `.wav` files excluded from Git |
| **Local Demo Sample Audio** | Presentation & offline video walkthroughs | `backend/data/sample_calls/demo_call.wav` | Static repository asset | Non-sensitive synthetic/demo audio asset |

---

## 2. Asset Classification & Isolation

- **Public Benchmark Assets**: Publicly licensed academic datasets (ASVspoof 2019 LA under ODC-By, Google FLEURS under CC BY 4.0). Used strictly for offline model calibration and Indic language baseline evaluations. Binary `.wav` files are git-ignored.
- **Local Demo Assets**: Pre-recorded sample audio (`demo_call.wav`) provided for presentation demos and testing when live microphone streaming is unavailable.
- **Consented Reference Audio**: User-provided reference audio stored under `backend/data/consented_reference_audio/`. Used solely for opt-in speaker identity verification. Excluded from Git tracking via `.gitignore`.
- **Transient Live-Call Audio**: Streamed audio chunks processed in memory. Audio frames exist in memory only for the duration of model inference (~4 seconds) and are garbage collected immediately.
- **Derived Risk Scores & Flags**: Quantitative output metadata (`chunk_score`, `rolling_risk_score`, `confidence`, `alert_level`, filtered status flags). Non-reconstructible mathematical summary indicators.

---

## 3. Confirmed SQLite Database Allowlist

The SQLite `chunk_history` table schema is strictly restricted to the following 10 allowlisted fields:

1. `id` (INTEGER PRIMARY KEY)
2. `session_id` (TEXT)
3. `chunk_id` (TEXT)
4. `timestamp` (TEXT ISO-8601)
5. `chunk_score` (REAL)
6. `rolling_risk_score` (REAL)
7. `confidence` (REAL)
8. `flags` (TEXT JSON array of filtered public flags)
9. `alert_level` (TEXT: `low` | `medium` | `high`)
10. `inference_latency_ms` (REAL)

### Explicitly Excluded Fields
SQLite **never** stores:
- Raw audio bytes or audio waveforms;
- Local file paths or directory locations;
- Caller names, phone numbers, or PII;
- Bank account numbers, credit card numbers, or OTP/PIN values;
- Call transaction context or banking context objects;
- Transaction advisory recommendation objects;
- Speaker verification embeddings or raw reference audio.

---

## 4. Speaker Verification Consent & Memory Lifecycle

1. **Opt-In Enrollment**: Speaker identity verification is active only when a consented reference audio path is explicitly provided by the caller.
2. **In-Memory Embedding Extraction**: The 1D SpeechBrain ECAPA-TDNN speaker embedding vector is generated in memory during session initialization.
3. **Automated Memory Cleanup**:
   - On normal call completion, `SessionIdentityTracker.clear()` is called.
   - On explicit call cancellation/stop (`POST /stop-simulation`), `clear()` is called.
   - On any stream error or pipeline exception, the `finally` block in `simulate_call()` guarantees `identity_tracker.clear()` is invoked.
   - Setting `reference_embedding = None` and `is_enrolled = False` releases memory for garbage collection.

---

## 5. Audit Corrections & Leak Remediations

- **`.gitignore` Hardening**: Added `backend/data/consented_reference_audio/*.wav` and `backend/data/consented_reference_audio/**/*.wav` to prevent accidental commits of consented reference audio files.
- **API Error Path Sanitization**: Updated `POST /start-simulation` error handling in `app/main.py` so internal exception strings and local filesystem paths are logged server-side and never leaked in HTTP 500 responses.

---

## 6. Known Deployment Limitations

- **Local Demo Scope**: This local prototype does not implement production multi-tenant authentication, KMS/HSM encryption key management, or automated database purge cron schedules.
- **Production Requirements**: Enterprise deployment requires an approved Privacy Policy, explicit consent UI flow, role-based access controls (RBAC), end-to-end TLS encryption, and configurable data retention/deletion TTL policies.

---

## 7. Presentation Privacy Statement ("Judge-Safe")

> **"VoxGuard is privacy-first by design. Call audio is analyzed entirely in-memory and discarded instantly—raw voice recordings, caller PII, and bank transaction details are never saved or sent to the database. VoxGuard persists only anonymous, high-level mathematical risk scores for audit security."**
