"use client";

import { AlertLevel } from "@/types/risk";

interface AlertBannerProps {
  alertLevel: AlertLevel;
  flags?: string[];
}

export default function AlertBanner({ alertLevel, flags = [] }: AlertBannerProps) {
  if (alertLevel === "low") {
    return (
      <div className="interactive-surface flex items-center gap-2.5 rounded-card border border-border bg-surface px-4 py-3.5 text-sm text-muted shadow-card">
        <span className="h-2 w-2 shrink-0 rounded-full bg-risk-low" />
        No irregularities detected in this call.
      </div>
    );
  }

  const isHigh = alertLevel === "high";

  return (
    <div
      key={alertLevel}
      className={`interactive-surface animate-fade-in-down rounded-card border px-4 py-3.5 shadow-card ${
        isHigh ? "border-risk-highBorder bg-risk-highBg" : "border-risk-mediumBorder bg-risk-mediumBg"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className={`text-sm font-medium ${isHigh ? "text-risk-high" : "text-risk-medium"}`}>
            {isHigh
              ? "High risk detected — recommend secondary verification"
              : "Elevated risk — monitor closely"}
          </p>
          {flags.length > 0 && (
            <p className="mt-1 font-mono text-xs text-muted">
              flags: {flags.join(", ")}
            </p>
          )}
        </div>

        {isHigh && (
          <button
            onClick={() => console.log("Secondary verification triggered")}
            className="btn-tactile shrink-0 rounded-control bg-risk-high px-3.5 py-2 text-sm font-medium text-accent-contrast shadow-card transition-opacity hover:opacity-90"
          >
            Trigger secondary verification
          </button>
        )}
      </div>
    </div>
  );
}
