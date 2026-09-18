"use client";

import { useState } from "react";
import { RiskAdvisory } from "@/types/risk";

export const REASON_CODE_LABELS: Record<string, string> = {
  high_acoustic_spoof_risk: "High voice-cloning risk",
  medium_acoustic_spoof_risk: "Moderate voice risk",
  unknown_caller: "Caller is not verified",
  sensitive_credential_request: "Sensitive credential request",
  high_value_transaction: "High-value transaction",
  context_not_provided: "Call context not provided",
  normal_call_flow: "No contextual warning",
};

interface AdvisoryPanelProps {
  advisory?: RiskAdvisory | null;
  onStopCall?: () => void;
}

// Visual-only tone mapping for each advisory recommendation. Reuses the
// same risk color tokens as the rest of the dashboard so the three
// possible states read consistently wherever they appear.
const TONE = {
  continue_with_caution: {
    fg: "text-risk-low",
    border: "border-risk-lowBorder",
    bg: "bg-risk-lowBg",
    dot: "bg-risk-low",
    label: "Advisory",
    title: "Continue carefully",
  },
  pause_and_verify: {
    fg: "text-risk-medium",
    border: "border-risk-mediumBorder",
    bg: "bg-risk-mediumBg",
    dot: "bg-risk-medium",
    label: "Action recommended",
    title: "Pause & Verify",
  },
  block_and_report: {
    fg: "text-risk-high",
    border: "border-risk-highBorder",
    bg: "bg-risk-highBg",
    dot: "bg-risk-high",
    label: "Transaction gated",
    title: "Block & Report",
  },
} as const;

export default function AdvisoryPanel({ advisory, onStopCall }: AdvisoryPanelProps) {
  const [acknowledged, setAcknowledged] = useState(false);

  if (!advisory) {
    return (
      <div className="interactive-surface rounded-card border border-border bg-surface p-5 shadow-card">
        <div className="flex items-center gap-2 text-sm text-muted">
          <span className="h-2 w-2 animate-pulse rounded-full bg-muted/60" />
          <span className="font-medium">Waiting for live risk assessment…</span>
        </div>
      </div>
    );
  }

  const { recommendation, reason_codes, user_message } = advisory;
  const tone = TONE[recommendation];

  const renderReasonBadges = () => (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {reason_codes.map((code) => (
        <span
          key={code}
          className={`inline-flex items-center rounded-full border ${tone.border} bg-surface px-2.5 py-1 text-xs ${tone.fg}`}
        >
          {REASON_CODE_LABELS[code] ?? code.replace(/_/g, " ")}
        </span>
      ))}
    </div>
  );

  return (
    <div className={`interactive-surface animate-fade-in-down rounded-card border shadow-elevated ${tone.border} ${tone.bg} p-5`}>
      <div className="flex items-center justify-between gap-3">
        <div className={`flex items-center gap-2 text-sm font-medium ${tone.fg}`}>
          <span
            className={`h-2 w-2 rounded-full ${tone.dot} ${
              recommendation === "pause_and_verify" ? "animate-pulse" : ""
            } ${recommendation === "block_and_report" ? "animate-ping" : ""}`}
          />
          <span>{tone.title}</span>
        </div>
        <span className={`text-xs font-medium uppercase tracking-wide ${tone.fg} opacity-80`}>
          {tone.label}
        </span>
      </div>

      <p className="mt-2 text-sm leading-relaxed text-foreground">{user_message}</p>
      {renderReasonBadges()}

      {recommendation === "pause_and_verify" && (
        <div className="mt-4">
          {acknowledged ? (
            <p className={`text-sm font-medium ${tone.fg}`}>
              ✓ Verified independently (demo acknowledgement only)
            </p>
          ) : (
            <button
              onClick={() => setAcknowledged(true)}
              className={`btn-tactile rounded-control border ${tone.border} bg-surface px-3.5 py-2 text-sm font-medium ${tone.fg} shadow-card transition-colors hover:bg-risk-mediumBg`}
            >
              I verified independently
            </button>
          )}
        </div>
      )}

      {recommendation === "block_and_report" && (
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button
            disabled
            className="flex-1 cursor-not-allowed rounded-control border border-risk-highBorder bg-surface px-3.5 py-2 text-center text-sm text-muted opacity-70"
          >
            Approve Transaction (Blocked)
          </button>
          {onStopCall && (
            <button
              onClick={onStopCall}
              className="btn-tactile flex-1 rounded-control bg-risk-high px-3.5 py-2 text-center text-sm font-medium text-accent-contrast shadow-card transition-opacity hover:opacity-90"
            >
              End call / verify through official channel
            </button>
          )}
        </div>
      )}
    </div>
  );
}
