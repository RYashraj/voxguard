export type AlertLevel = "low" | "medium" | "high";

export interface PreTransactionWarning {
  session_id?: string;
  reason: string;
  recommended_actions: string[];
  timestamp: string;
}

export interface ThresholdSettings {
  fund_transfer: number; // 0.0 - 1.0
  information_request: number; // 0.0 - 1.0
  routine: number; // 0.0 - 1.0
}

export interface TransparencyBenchmark {
  accent_language: string;
  accuracy: number; // 0-100, placeholder until real ML team results are available
  sample_size: number;
}

export interface RiskUpdate {
  chunk_id: string;
  timestamp: string; // ISO8601
  chunk_score: number; // 0.0 - 1.0
  rolling_risk_score: number; // 0.0 - 1.0
  confidence: number; // 0.0 - 1.0
  flags: string[];
  alert_level: AlertLevel;
  prosody_score?: number; // 0.0 - 1.0 (prosody anomaly)
  identity_drift?: number; // 0.0 - 1.0 (speaker swap indicator)
}
