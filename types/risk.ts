export type AlertLevel = "low" | "medium" | "high";

export interface RiskUpdate {
  chunk_id: string;
  timestamp: string; // ISO8601
  chunk_score: number; // 0.0 - 1.0
  rolling_risk_score: number; // 0.0 - 1.0
  confidence: number; // 0.0 - 1.0
  flags: string[];
  alert_level: AlertLevel;
}
