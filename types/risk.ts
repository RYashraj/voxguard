export type AlertLevel = "low" | "medium" | "high";

export type AdvisoryRecommendation =
  | "continue_with_caution"
  | "pause_and_verify"
  | "block_and_report";

export interface RiskAdvisory {
  recommendation: AdvisoryRecommendation;
  reason_codes: string[];
  user_message: string;
  requires_user_confirmation: boolean;
}

export interface RiskUpdate {
  chunk_id: string;
  timestamp: string; // ISO8601
  chunk_score: number; // 0.0 - 1.0
  rolling_risk_score: number; // 0.0 - 1.0
  confidence: number; // 0.0 - 1.0
  flags: string[];
  alert_level: AlertLevel;
  advisory?: RiskAdvisory;
}

export type CallerContext = "known_contact" | "unknown_contact" | "not_provided";

export type TransactionType =
  | "fund_transfer"
  | "otp_or_pin_request"
  | "account_update"
  | "other"
  | "not_provided";

export interface SimulationContext {
  caller_context: CallerContext;
  transaction_type: TransactionType;
  transaction_amount?: number;
  user_confirmation_required: boolean;
}

