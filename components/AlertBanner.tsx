"use client";

import { AlertLevel } from "@/types/risk";

interface AlertBannerProps {
  alertLevel: AlertLevel;
  flags?: string[];
}

export default function AlertBanner({ alertLevel, flags = [] }: AlertBannerProps) {
  if (alertLevel === "low") {
    return (
      <div className="border border-line bg-surface px-4 py-3 text-sm text-muted">
        No irregularities detected in this call.
      </div>
    );
  }

  const isHigh = alertLevel === "high";
  const color = isHigh ? "var(--risk-high)" : "var(--risk-medium)";

  return (
    <div
      key={alertLevel}
      className="animate-banner-in border border-line bg-surface py-3.5 pl-4 pr-4"
      style={{ borderLeft: `6px solid ${color}` }}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold" style={{ color }}>
            {isHigh
              ? "High risk detected — recommend secondary verification"
              : "Elevated risk — monitor closely"}
          </p>
          {flags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {flags.map((flag) => (
                <span
                  key={flag}
                  className="border px-1.5 py-0.5 font-mono text-[10px]"
                  style={{ borderColor: color, color }}
                >
                  {flag}
                </span>
              ))}
            </div>
          )}
        </div>

        {isHigh && (
          <button
            onClick={() => console.log("Secondary verification triggered")}
            className="shrink-0 border px-3 py-1.5 text-sm font-medium transition-colors"
            style={{ borderColor: color, color }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = color;
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
              e.currentTarget.style.color = color;
            }}
          >
            Trigger secondary verification
          </button>
        )}
      </div>
    </div>
  );
}
