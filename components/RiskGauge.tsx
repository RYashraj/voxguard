"use client";

import { AlertLevel } from "@/types/risk";

interface RiskGaugeProps {
  score: number; // 0.0 - 1.0
  confidence: number; // 0.0 - 1.0
  alertLevel: AlertLevel;
}

const LEVEL_COLOR: Record<AlertLevel, string> = {
  low: "#34D399",
  medium: "#F5B942",
  high: "#F0546B",
};

const LEVEL_LABEL: Record<AlertLevel, string> = {
  low: "Low risk",
  medium: "Elevated risk",
  high: "High risk",
};

export default function RiskGauge({ score, confidence, alertLevel }: RiskGaugeProps) {
  const clamped = Math.min(1, Math.max(0, score));
  const displayScore = Math.round(clamped * 100);
  const color = LEVEL_COLOR[alertLevel];

  // Arc geometry: 270° sweep starting at 135°, so the gauge reads like an
  // instrument dial rather than a full clock face.
  const radius = 84;
  const circumference = 2 * Math.PI * radius;
  const sweepFraction = 0.75; // 270 / 360
  const arcLength = circumference * sweepFraction;
  const filled = arcLength * clamped;

  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-border bg-surface p-8">
      <div className="relative h-56 w-56">
        <svg viewBox="0 0 200 200" className="h-full w-full -rotate-[225deg]">
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="#1C2843"
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
          <span className="font-mono text-5xl font-semibold tabular-nums" style={{ color }}>
            {displayScore}
          </span>
          <span className="mt-1 text-xs uppercase tracking-wide text-muted">
            rolling risk
          </span>
        </div>
      </div>

      <div className="flex w-full items-center justify-between text-sm">
        <span className="font-medium" style={{ color }}>
          {LEVEL_LABEL[alertLevel]}
        </span>
        <span className="font-mono text-muted">
          confidence {Math.round(confidence * 100)}%
        </span>
      </div>
    </div>
  );
}
