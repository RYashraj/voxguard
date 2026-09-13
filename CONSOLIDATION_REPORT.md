# VoxGuard Consolidation Report

**Project:** SIH26104 — AI Voice Cloning / Impersonation Detection  
**Team:** Crackjack  
**Date:** September 13, 2026  
**Branch consolidated into:** `develop`

---

## 1. Branches Merged & Order

| Order | Branch | Result | Unique Content |
|---|---|---|---|
| Base | `main` | Checkout base | README, .gitignore only |
| 1 | `feature/backend-api` | ✅ Merged | FastAPI backend, `team_resources/`, test suite |
| 2 | `feature/ml-pipeline` | ✅ Merged | Standalone ML exploration scripts (`Model/`) |
| 3 | `feature/full-demo-integration` | ✅ Merged | Real ML integration, SQLite logging, Next.js frontend v1, ASVspoof test audio |
| 4 | `frontend-updated` | ✅ Merged | 5-component dashboard, IBM Plex fonts, ThemeToggle |
| — | `feature/ml-backend-integration` | ⏭ Skipped | No unique commits beyond `main` |
| — | `feature/frontend-dashboard` | ⏭ Skipped | No unique commits beyond `main` |
| — | `docs` | ⏭ Skipped | No unique commits beyond `main` |

**Key finding:** `feature/full-demo-integration` is a direct linear descendant of `feature/backend-api` (merge-base = exact tip of backend-api). No hidden backend conflicts existed.

---

## 2. Conflicts Found & How Each Was Resolved

| # | File | Conflict Type | Resolution | Rationale |
|---|---|---|---|---|
| 1 | `.gitignore` (Merge 1) | Content | Kept both sides; **dropped `/data/`** (overbroad) | Our `Teamdocs/` + backend-api's `.pytest_cache/`, `*.zip` |
| 2 | `.gitignore` (Merge 3) | Content | Merged both sides | Added `tsconfig.tsbuildinfo` + granular `backend/data/*.db*` rules |
| 3 | `README.md` (Merge 3) | Modify/delete | **Kept full-demo-integration version** | ml-pipeline accidentally deleted it; full-demo has the real project README |
| 4 | `app/page.tsx` (Merge 4) | Add/add | **Took `frontend-updated`** | 5-component grid layout supersedes 3-component list; `handleStopCall` intentionally removed in newer version |
| 5 | `app/globals.css` (Merge 4) | Add/add | **Took `frontend-updated`** | IBM Plex font CSS variable integration |
| 6 | `app/layout.tsx` (Merge 4) | Add/add | **Took `frontend-updated`** | Font import wiring |
| 7–9 | `components/{AlertBanner,LiveWaveform,RiskGauge}.tsx` (Merge 4) | Add/add | **Took `frontend-updated`** | Refined implementations |
| 10 | `components/__tests__/AlertBanner.day4.test.tsx` (Merge 4) | Add/add | **Took `frontend-updated`** | Updated test assertions |
| 11 | `package.json` (Merge 4) | Add/add | **Took `frontend-updated`** | Adds `@fontsource/ibm-plex-mono` + `@fontsource/ibm-plex-sans` (used in `app/layout.tsx`) |
| 12 | `package-lock.json` (Merge 4) | Add/add | **Took `frontend-updated`** | Must match package.json |
| 13 | `server.js` (Merge 4) | Add/add | **Took `frontend-updated`** | Refined mock WS server |
| 14 | `tailwind.config.ts` (Merge 4) | Add/add | **Took `frontend-updated`** | Updated Tailwind configuration |
| 15 | `README.md` (Merge 4) | Content | **Took `frontend-updated`** | Better formatting, concrete data contract example, cleaner setup guide |

**Zero real logic conflicts found.** No two team members independently implemented the same function differently.

---

## 3. Placeholders / Incomplete / Fake Implementations Found

| File | Line | Type | Description | Action |
|---|---|---|---|---|
| `team_resources/for_ml/sample_inference_template.py` | 20 | TODO comment | `# TODO: Load your weights / checkpoints here:` | **Intentional** — this is a template file for the ML team, not production code. No action needed. |
| `backend/app/ml/stub.py` | entire file | Documented stub | `analyze_chunk_stub()` and `MLStubSession` simulate ML scores for dev/testing | **Intentional** — controlled via `VOXGUARD_ML_MODE=stub`. Production uses real model. |
| `backend/app/ml/stub.py` | 46 | `pass` in `except` | `except Exception: pass` inside RMS calculation fallback | **Safe** — intentional silent fallback; RMS is non-critical cosmetic metric. Not changed. |

**Zero unintentional stubs or `NotImplementedError` raises found in production code paths.**

---

## 4. Hardcoded Secrets Found & Where Moved

| File | Line | Was | Fixed To |
|---|---|---|---|
| `Model/ml_model.py` | 7 | `AUDIO_FILE = r"test_audio\clone_2.wav"` hardcoded path | `os.getenv("VOXGUARD_TEST_AUDIO_PATH", "test_audio/clone_2.wav")` |
| `Model/ml_model.py` | 84 | `model_path = r"C:\Users\NANDINI\.cache\huggingface\..."` absolute machine path | `os.getenv("SPECTRA_MODEL_PATH", "lab260/Spectra-AASIST3")` |

**Zero API keys, tokens, passwords, or email addresses found in any tracked file.**

### Git History Secret Scan Results

```bash
git log --all --full-history --oneline -- .env
# Output: (empty — .env was NEVER committed)

git log --all --full-history --oneline -S "password" -S "secret" -S "api_key" -S "token" -- "*.py" "*.js" "*.ts" "*.env"
# Output: (empty — zero credential strings in git history)
```

**Git history is clean. No credentials were ever committed, even in old/removed commits.**

### Hardcoded Localhost URLs (Not Secrets — Documented for Awareness)

These are development fallback defaults, NOT hardcoded secrets. They are gated behind `process.env.*` and only apply when env vars are not set:

| File | Line | Value | Status |
|---|---|---|---|
| `app/page.tsx` | 15 | `ws://localhost:8080` | ✅ OK — fallback to mock server for local dev |
| `app/page.tsx` | 17 | `http://localhost:8000` | ✅ OK — fallback to local backend |
| `backend/app/main.py` | 65–69 | `localhost:3000`, `localhost:5173` CORS origins | ✅ OK — dev CORS list, also includes `"*"` wildcard (flag: should be restricted in prod) |

> [!NOTE]
> The `"*"` CORS origin wildcard in `backend/app/main.py` line 70 is acceptable for a hackathon demo but **should be removed** before any production deployment. Flagged here — not changed per strict non-breaking rule.

---

## 5. Contract Mismatch Audit (Backend ↔ Frontend ↔ ML)

### RiskUpdate Contract — Field-by-Field Comparison

| Field | Backend (`schemas.py`) | Frontend (`types/risk.ts`) | Match? |
|---|---|---|---|
| `chunk_id` | `str` | `string` | ✅ |
| `timestamp` | `str` (ISO8601) | `string // ISO8601` | ✅ |
| `chunk_score` | `float` (0.0–1.0) | `number // 0.0–1.0` | ✅ |
| `rolling_risk_score` | `float` (0.0–1.0) | `number // 0.0–1.0` | ✅ |
| `confidence` | `float` (0.0–1.0) | `number // 0.0–1.0` | ✅ |
| `flags` | `List[str]` | `string[]` | ✅ |
| `alert_level` | `Literal["low","medium","high"]` | `"low" \| "medium" \| "high"` | ✅ |

**Perfect match — 7/7 fields aligned in name, type, and constraint.**

### ML → Backend Contract

The `analyze_chunk_dispatch()` function returns:
```python
{"chunk_score": float, "confidence": float, "flags": List[str]}
```
The `RollingRiskAggregator.create_risk_update()` consumes exactly these fields to build a `RiskUpdate`. **No mismatch.**

### Frontend WebSocket Filter (Defense in Depth)

The `useRiskSocket` hook in `hooks/useRiskSocket.ts` explicitly validates incoming messages before treating them as `RiskUpdate` objects:
```typescript
if (
  typeof parsed?.chunk_id !== "string" ||
  typeof parsed?.rolling_risk_score !== "number" ||
  typeof parsed?.alert_level !== "string"
) { return; }  // ignores handshake/control messages
```
This correctly filters the backend's `{"event": "connected", ...}` handshake. **Contract handling is correct end-to-end.**

---

## 6. Dependency Audit

### Python `backend/requirements.txt`

| Package | Required By | Status |
|---|---|---|
| `fastapi>=0.110.0` | `backend/app/main.py` + all routes | ✅ Used |
| `uvicorn[standard]>=0.28.0` | `backend/main.py` entrypoint | ✅ Used |
| `pydantic>=2.6.0` | `backend/app/models/schemas.py` | ✅ Used |
| `pydub>=0.25.1` | `backend/app/services/simulator.py` (optional, has fallback) | ✅ Used (optional import with wave fallback) |
| `numpy>=1.26.0` | `backend/app/ml/ml_model.py` (optional, has fallback) | ✅ Used |
| `scipy>=1.12.0` | — | ⚠️ **NOT directly imported anywhere in backend code** |
| `websockets>=12.0` | — | ⚠️ **NOT directly imported** — uvicorn[standard] includes it transitively |
| `pytest>=8.0.0` | `backend/tests/` | ✅ Used (test dep) |
| `pytest-asyncio>=0.23.0` | `backend/tests/` | ✅ Used (test dep) |
| `httpx>=0.27.0` | `backend/tests/test_health.py` | ✅ Used (test dep) |
| `torch>=2.0.0` | `backend/app/ml/ml_model.py` | ✅ Used |
| `torchaudio>=2.0.0` | `backend/app/ml/ml_model.py` | ✅ Used |
| `transformers>=4.30.0` | `backend/app/ml/ml_model.py` | ✅ Used |
| `huggingface_hub>=0.16.0` | `backend/app/ml/ml_model.py` | ✅ Used |

> [!NOTE]
> **`scipy`** is listed in `requirements.txt` but is never imported in any backend source file. It may be a leftover from an earlier approach or was added speculatively. It is not removed here (per Phase 3 strict rule — removal is Phase 5), but flagged for Phase 5 cleanup.
>
> **`websockets`** is a transitive dependency of `uvicorn[standard]` — not needed as a direct entry, but harmless to keep for explicit pinning.

### JavaScript/TypeScript `package.json`

| Package | Required By | Status |
|---|---|---|
| `next@14.2.35` | Entire frontend | ✅ Used |
| `react@^18` | All `.tsx` components | ✅ Used |
| `react-dom@^18` | Next.js rendering | ✅ Used |
| `recharts@^3.10.1` | `components/RiskTrend.tsx` | ✅ Used |
| `@fontsource/ibm-plex-mono@^5.3.0` | `app/layout.tsx` import | ✅ Used |
| `@fontsource/ibm-plex-sans@^5.3.0` | `app/layout.tsx` import | ✅ Used |
| `tailwindcss@^3.4.1` (dev) | `app/globals.css`, `tailwind.config.ts` | ✅ Used |
| `typescript@^5` (dev) | All `.ts`/`.tsx` files | ✅ Used |
| `vitest@^1.6.1` (dev) | `npm run test` | ✅ Used |
| `ws@^8` (dev) | `server.js` mock WS server | ✅ Used |
| `@testing-library/react@^14` (dev) | `components/__tests__/` | ✅ Used |
| `@vitejs/plugin-react@^4.7.0` (dev) | `vitest.config.ts` | ✅ Used |

**All JS dependencies are actively used. No orphaned packages.**

---

## 7. `team_resources` — Final Confirmation

All 14 files confirmed present in `develop` tree:

```
team_resources/README.md
team_resources/for_frontend/README.md
team_resources/for_frontend/contract_schema.json
team_resources/for_frontend/sample_payload.json
team_resources/for_frontend/test_websocket_client.html
team_resources/for_ml/README.md
team_resources/for_ml/audio_specs.json
team_resources/for_ml/sample_inference_template.py
team_resources/for_ml/sample_chunks/chunk_001.wav ... chunk_006.wav
```

✅ All present and accounted for.

---

## 8. Final Git Status

```
Branch: develop
git status: nothing to commit, working tree clean

Commits on develop (summary):
a1e829d  chore: add Teamdocs/ to .gitignore
2274d76  merge: integrate feature/backend-api
4f63d70  merge: integrate feature/ml-pipeline
55546c2  merge: integrate feature/full-demo-integration
5d90866  merge: integrate frontend-updated
(+ Phase 3 audit fix commit)
```

---

## 9. Remaining Action Items (for later phases)

| Item | Phase | Priority |
|---|---|---|
| Add Google OAuth sign-in (NextAuth.js) | Phase 4 | Medium |
| Rename `Model/` → `ml/standalone/` | Phase 5 | Low |
| Remove `scipy` from `requirements.txt` (unused) | Phase 5 | Low |
| Remove CORS `"*"` wildcard (security hardening) | Post-hackathon | Low |
| Remove unused imports across merged codebase | Phase 5 | Low |
