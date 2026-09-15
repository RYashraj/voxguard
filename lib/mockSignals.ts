// Task 2 (PS ref 1b/1c): prosody_score and identity_drift are new fields
// the backend/ML team hasn't confirmed on the WebSocket contract yet.
// Real values (u.prosody_score / u.identity_drift) always win when present;
// this mock generator only fills the gap until then, and only when the
// feature flag below is on — flip NEXT_PUBLIC_MOCK_PROSODY_DRIFT=false
// once the real fields are wired in.
export const MOCK_PROSODY_DRIFT_ENABLED =
  process.env.NEXT_PUBLIC_MOCK_PROSODY_DRIFT !== "false";

// Deterministic pseudo-random float in [0, 1), seeded by a string. Using
// chunk_id as the seed (rather than array index or Math.random()) means
// the same chunk always mocks to the same value everywhere it's read
// (RiskTrend chart + Identity Confidence badge), with no flicker on
// re-render and no drift when older history entries get trimmed.
function seededRandom(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  const x = Math.sin(hash) * 43758.5453;
  return x - Math.floor(x);
}

export function getMockProsodyScore(chunkId: string): number {
  return seededRandom(`${chunkId}:prosody_score`);
}

export function getMockIdentityDrift(chunkId: string): number {
  return seededRandom(`${chunkId}:identity_drift`);
}
