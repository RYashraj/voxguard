"use client";

import { AlertLevel } from "@/types/risk";

interface AlertBannerProps {
  alertLevel: AlertLevel;
  flags?: string[];
}

export default function AlertBanner({ alertLevel, flags = [] }: AlertBannerProps) {
  if (alertLevel === "low") {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-3 text-sm text-muted">
        <span className="h-2 w-2 rounded-full bg-risk-low" />
        No irregularities detected in this call.
      </div>
    );
  }

  const isHigh = alertLevel === "high";

  return (
    <div
      key={alertLevel}
      className={`animate-fade-in-down rounded-xl border px-4 py-3 ${
        isHigh
          ? "border-risk-high/40 bg-risk-high/10"
          : "border-risk-medium/40 bg-risk-medium/10"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className={`font-medium ${isHigh ? "text-risk-high" : "text-risk-medium"}`}>
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
            className="shrink-0 rounded-lg bg-risk-high px-3 py-1.5 text-sm font-medium text-[#1A0508] transition-opacity hover:opacity-90"
          >
            Trigger secondary verification
          </button>
        )}
      </div>
    </div>
  );
}
