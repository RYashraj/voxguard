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

export default function AdvisoryPanel({ advisory, onStopCall }: AdvisoryPanelProps) {
  const [acknowledged, setAcknowledged] = useState(false);

  if (!advisory) {
    return (
      <div className="rounded-xl border border-border bg-surface/50 p-4 text-xs text-muted">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-muted/60 animate-pulse" />
          <span className="font-medium">Waiting for live risk assessment…</span>
        </div>
      </div>
    );
  }

  const { recommendation, reason_codes, user_message } = advisory;

  const renderReasonBadges = () => (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {reason_codes.map((code) => (
        <span
          key={code}
          className="inline-flex items-center rounded-md border border-current/20 bg-current/10 px-2 py-0.5 text-[11px] font-mono"
        >
          {REASON_CODE_LABELS[code] ?? code.replace(/_/g, " ")}
        </span>
      ))}
    </div>
  );

  if (recommendation === "continue_with_caution") {
    return (
      <div className="rounded-xl border border-teal-500/30 bg-teal-950/20 p-4 text-teal-200 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <span className="h-2 w-2 rounded-full bg-teal-400" />
            <span>Continue carefully</span>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-wider text-teal-400/80">
            Advisory Gate
          </span>
        </div>
        <p className="text-xs text-teal-200/90">{user_message}</p>
        {renderReasonBadges()}
      </div>
    );
  }

  if (recommendation === "pause_and_verify") {
    return (
      <div className="rounded-xl border border-amber-500/40 bg-amber-950/30 p-4 text-amber-200 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
            <span>Pause & Verify</span>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-wider text-amber-400/80">
            Action Recommended
          </span>
        </div>
        <p className="text-xs text-amber-100/90">{user_message}</p>
        {renderReasonBadges()}
        <div className="pt-1">
          {acknowledged ? (
            <p className="font-mono text-[11px] text-amber-400">
              ✓ Verified independently (demo acknowledgement only)
            </p>
          ) : (
            <button
              onClick={() => setAcknowledged(true)}
              className="rounded-lg border border-amber-400/40 bg-amber-500/20 px-3 py-1.5 font-mono text-xs text-amber-100 transition-colors hover:bg-amber-500/30"
            >
              I verified independently
            </button>
          )}
        </div>
      </div>
    );
  }

  // block_and_report
  return (
    <div className="rounded-xl border border-rose-500/50 bg-rose-950/40 p-4 text-rose-200 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-sm text-rose-300">
          <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping" />
          <span>Block & Report</span>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-wider text-rose-400">
          Transaction Gated
        </span>
      </div>
      <p className="text-xs text-rose-100/90">{user_message}</p>
      {renderReasonBadges()}
      
      <div className="flex flex-col gap-2 pt-2 sm:flex-row">
        <button
          disabled
          className="flex-1 rounded-lg border border-rose-500/30 bg-rose-900/30 px-3 py-2 font-mono text-xs text-rose-400/60 cursor-not-allowed text-center"
        >
          Approve Transaction (Blocked)
        </button>
        {onStopCall && (
          <button
            onClick={onStopCall}
            className="flex-1 rounded-lg border border-rose-400/60 bg-rose-600/30 px-3 py-2 font-mono text-xs text-rose-100 transition-colors hover:bg-rose-600/40 text-center"
          >
            End call / verify through official channel
          </button>
        )}
      </div>
    </div>
  );
}
