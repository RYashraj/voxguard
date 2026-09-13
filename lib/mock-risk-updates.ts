import { RiskUpdate } from "@/types/risk";

// Simulated call: risk climbs steadily as more audio chunks arrive.
// - alert_level is "low" while rolling_risk_score stays under 0.4
// - "medium" once it crosses 0.4 (early warning, per Day 4 spec)
// - "high" once it crosses 0.7
function levelFor(score: number): RiskUpdate["alert_level"] {
  if (score > 0.7) return "high";
  if (score > 0.4) return "medium";
  return "low";
}

const ROLLING_SCORES = [0.1, 0.18, 0.27, 0.35, 0.44, 0.52, 0.61, 0.7, 0.78, 0.85];

export const MOCK_RISK_UPDATES: RiskUpdate[] = ROLLING_SCORES.map((rolling, i) => {
  const timestamp = new Date(Date.UTC(2026, 8, 7, 10, 0, i * 2)).toISOString();
  const level = levelFor(rolling);

  return {
    chunk_id: `chunk_${String(i + 1).padStart(3, "0")}`,
    timestamp,
    chunk_score: Math.min(1, Math.max(0, rolling + (i % 2 === 0 ? 0.05 : -0.03))),
    rolling_risk_score: rolling,
    confidence: 0.7 + i * 0.02,
    flags: level === "high" ? ["synthetic_artifact"] : level === "medium" ? ["prosody_anomaly"] : [],
    alert_level: level,
  };
});
