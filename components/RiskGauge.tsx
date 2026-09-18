"use client";

import { AlertLevel } from "@/types/risk";

interface RiskGaugeProps {
  score: number; // 0.0 - 1.0
  confidence: number; // 0.0 - 1.0
  alertLevel: AlertLevel;
}

const LEVEL_COLOR_VAR: Record<AlertLevel, string> = {
  low: "var(--risk-low)",
  medium: "var(--risk-medium)",
  high: "var(--risk-high)",
};

const LEVEL_BADGE_BG_VAR: Record<AlertLevel, string> = {
  low: "var(--risk-low-bg)",
  medium: "var(--risk-medium-bg)",
  high: "var(--risk-high-bg)",
};

const LEVEL_LABEL: Record<AlertLevel, string> = {
  low: "Low risk",
  medium: "Elevated risk",
  high: "High risk",
};

const LEVEL_DESCRIPTION: Record<AlertLevel, string> = {
  low: "No irregular voice patterns in the current window.",
  medium: "Some signals are drifting from the caller's baseline.",
  high: "Strong indicators of voice impersonation.",
};

export default function RiskGauge({ score, confidence, alertLevel }: RiskGaugeProps) {
  const clamped = Math.min(1, Math.max(0, score));
  const displayScore = Math.round(clamped * 100);
  const color = LEVEL_COLOR_VAR[alertLevel];

  // Arc geometry: 270° sweep starting at 135°, so the gauge reads like an
  // instrument dial rather than a full clock face.
  const radius = 84;
  const circumference = 2 * Math.PI * radius;
  const sweepFraction = 0.75; // 270 / 360
  const arcLength = circumference * sweepFraction;
  const filled = arcLength * clamped;

  return (
    <div className="interactive-surface rounded-card border border-border bg-surface p-6 shadow-elevated sm:p-8">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-foreground">Rolling risk score</h2>
        <span
          className="rounded-full px-2.5 py-1 text-xs font-medium transition-colors"
          style={{ color, backgroundColor: LEVEL_BADGE_BG_VAR[alertLevel] }}
        >
          {LEVEL_LABEL[alertLevel]}
        </span>
      </div>

      <div className="mt-4 flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:justify-center sm:gap-10">
        <div className="relative h-52 w-52 shrink-0">
          <svg viewBox="0 0 200 200" className="h-full w-full -rotate-[225deg]">
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke="var(--gauge-track)"
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${arcLength} ${circumference}`}
            />
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${filled} ${circumference}`}
              style={{
                transition: "stroke-dasharray 500ms ease, stroke 500ms ease",
              }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono text-5xl font-semibold tabular-nums text-foreground">
              {displayScore}
            </span>
            <span className="mt-1 text-xs uppercase tracking-wide text-muted">
              out of 100
            </span>
          </div>
        </div>

        <div className="flex w-full max-w-xs flex-col gap-3 text-center sm:text-left">
          <p className="text-sm leading-relaxed text-muted">{LEVEL_DESCRIPTION[alertLevel]}</p>
          <div className="flex items-center justify-center gap-2 text-sm sm:justify-start">
            <span className="text-muted">Model confidence</span>
            <span className="font-mono font-medium text-foreground">
              {Math.round(confidence * 100)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
