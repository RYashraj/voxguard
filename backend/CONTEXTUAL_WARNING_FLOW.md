# VoxGuard Explainable Contextual Enrichment & Pre-Transaction Warning Flow

> [!IMPORTANT]
> **SYSTEM DISCLAIMER**: The VoxGuard Contextual Warning Flow is a local simulator-based demo advisory policy layer. It provides explainable, transparent security advisories for demo call scenarios. It is **NOT** an automated financial decision engine and **MUST NOT** be used to execute automated transaction blocks or overrides without explicit human verification.

---

## 1. Overview & Architecture

VoxGuard enriches acoustic deepfake detection telemetry (`RiskUpdate`) with explainable call and transaction context to provide actionable pre-transaction security advisories.

- **Core Data Contract**: The original 7-field `RiskUpdate` WebSocket contract (`chunk_id`, `timestamp`, `chunk_score`, `rolling_risk_score`, `confidence`, `flags`, `alert_level`) remains unchanged and strictly enforced.
- **Additive Extension**: Advisory recommendations are attached as an optional additive `advisory` object in streamed JSON messages.
- **Data Minimisation & In-Memory Storage**: Call/transaction context is retained **ONLY IN PROCESS MEMORY** during active demo sessions and is **NEVER** written to SQLite databases or persistent logs.

---

## 2. Supported Context Data Schema

`SimulationContext` (Pydantic Model):

| Field | Supported Values / Type | Description | Data Minimisation Rule |
| :--- | :--- | :--- | :--- |
| `caller_context` | `known_contact`, `unknown_contact`, `not_provided` | Relationship status of incoming caller. | No free-form caller names, phone numbers, or PII accepted. |
| `transaction_type` | `fund_transfer`, `otp_or_pin_request`, `account_update`, `other`, `not_provided` | Action/transaction requested during the call. | No account numbers, credentials, or sensitive tokens accepted. |
| `transaction_amount` | Optional positive number (float > 0) | Transaction value in INR (₹) for demo display. | Optional numeric value only. |
| `user_confirmation_required` | Boolean (default `true`) | Whether explicit user verification is recommended. | Standard boolean flag. |

---

## 3. Deterministic Advisory Policy Rules & Matrix

The explainable policy engine (`backend/app/services/context_policy.py`) evaluates acoustic alert levels alongside call context deterministically:

| Alert Level | Caller Context | Transaction Type | Amount / Criteria | Recommendation | Reason Codes | User Message |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`high`** | Any | Any | Any | `block_and_report` | `high_acoustic_spoof_risk` (+ context reasons) | *"High voice-cloning risk detected. Do not approve this transaction; verify through an official channel."* |
| **`medium`** | Any | Any | Any | `pause_and_verify` | `medium_acoustic_spoof_risk` (+ context reasons) | *"Suspicious voice acoustic patterns detected. Pause the call and confirm caller identity before proceeding."* |
| **`low`** | `unknown_contact` | `otp_or_pin_request` | Any | `pause_and_verify` | `unknown_caller`, `sensitive_credential_request` | *"Credential or PIN requested by an unknown caller. Pause and verify identity through an official channel."* |
| **`low`** | `unknown_contact` | `fund_transfer` | $\ge \text{₹}10,000$ | `pause_and_verify` | `unknown_caller`, `high_value_transaction` | *"High-value transfer requested by an unknown caller ($\ge$ ₹10,000). Pause and verify before proceeding."* |
| **`low`** | Any | `otp_or_pin_request` | Any | `pause_and_verify` | `sensitive_credential_request` | *"Sensitive credential or PIN requested. Pause and confirm caller identity before sharing credentials."* |
| **`low`** | `known_contact` / `not_provided` | Standard / `not_provided` | $<$ ₹10,000 / None | `continue_with_caution` | `context_not_provided` or context flags | *"Low acoustic risk detected. Proceed with caution and verify sensitive requests."* |

---

## 4. Key Security & Privacy Guarantees

1. **₹10,000 Demo Threshold**: Transfers $\ge$ ₹10,000 requested by an unknown caller trigger a conservative `pause_and_verify` advisory even when acoustic risk is low.
2. **Zero SQLite Persistence**: Session context payloads (`caller_context`, `transaction_type`, `transaction_amount`) are stored strictly in process memory and are **NEVER** logged or persisted into SQLite database records (`session_history`).
3. **No Unvalidated Signal Tampering**: Unvalidated prosody scores and speaker verification metrics **DO NOT** alter acoustic ML scores, rolling risk scores, or alert levels.
4. **Transparent Advisory Only**: Advisories are explainable security suggestions. Users are advised to independently verify suspicious calls via an official bank number or mobile banking app.

---

## 5. REST API Endpoints

- **`POST /sessions/{session_id}/context`**: Set or update in-memory context for an active demo session. Returns `404` if the session is inactive or unknown.
- **`GET /sessions/{session_id}/context`**: Retrieve current in-memory context for an active session. Returns `404` if the session is inactive or unknown.
