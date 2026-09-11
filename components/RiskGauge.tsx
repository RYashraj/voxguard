"use client";

import { AlertLevel } from "@/types/risk";

interface RiskGaugeProps {
  score: number; // 0.0 - 1.0
  confidence: number; // 0.0 - 1.0
  alertLevel: AlertLevel;
}

const LEVEL_COLOR: Record<AlertLevel, string> = {
  low: "var(--risk-low)",
  medium: "var(--risk-medium)",
  high: "var(--risk-high)",
};

const LEVEL_LABEL: Record<AlertLevel, string> = {
  low: "Low risk",
  medium: "Elevated risk",
  high: "High risk",
};

// Needle sweeps 180°: -90° (score 0, pointing left) through 0° (score 0.5,
// pointing straight up) to +90° (score 1, pointing right) — reads like a
// physical meter, not a loading spinner.
const CX = 110;
const CY = 118;
const TICK_R = 92;
const BAND_R = 78;
const NEEDLE_R = 70;

function pointOnCircle(radius: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180;
  return {
    x: CX + radius * Math.sin(rad),
    y: CY - radius * Math.cos(rad),
  };
}

function arcPath(radius: number, fromT: number, toT: number) {
  const fromAngle = -90 + fromT * 180;
  const toAngle = -90 + toT * 180;
  const start = pointOnCircle(radius, fromAngle);
  const end = pointOnCircle(radius, toAngle);
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 0 1 ${end.x} ${end.y}`;
}

const TICKS = [0, 0.25, 0.5, 0.75, 1];
const BANDS: { from: number; to: number; color: string }[] = [
  { from: 0, to: 0.4, color: "var(--risk-low)" },
  { from: 0.4, to: 0.7, color: "var(--risk-medium)" },
  { from: 0.7, to: 1, color: "var(--risk-high)" },
];

export default function RiskGauge({ score, confidence, alertLevel }: RiskGaugeProps) {
  const t = Math.min(1, Math.max(0, score));
  const displayScore = Math.round(t * 100);
  const color = LEVEL_COLOR[alertLevel];
  const needleAngle = -90 + t * 180;
  const needleTip = pointOnCircle(NEEDLE_R, needleAngle);

  return (
    <div
      className="flex h-full flex-col border border-line p-6"
      style={{
        backgroundColor: "var(--surface)",
        backgroundImage:
          "linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px)",
        backgroundSize: "16px 16px",
      }}
    >
      <div className="flex items-center justify-between">
        <p className="font-mono text-[11px] uppercase tracking-wide text-muted">
          Rolling risk score
        </p>
        <p className="font-mono text-[11px] text-muted">/ 100</p>
      </div>

      <div className="mb-[-6px] mt-3 flex justify-between px-1.5 font-mono text-[10px] text-muted">
        <span>0</span>
        <span>50</span>
        <span>100</span>
      </div>

      <svg viewBox="0 0 220 130" className="mx-auto w-full max-w-[340px] flex-1">
        {BANDS.map((band) => (
          <path
            key={band.color}
            d={arcPath(BAND_R, band.from, band.to)}
            fill="none"
            style={{ stroke: band.color }}
            strokeWidth={8}
            strokeLinecap="butt"
          />
        ))}

        {TICKS.map((tick) => {
          const angle = -90 + tick * 180;
          const outer = pointOnCircle(TICK_R, angle);
          const inner = pointOnCircle(TICK_R - 8, angle);
          return (
            <line
              key={tick}
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              style={{ stroke: "var(--ink)" }}
              strokeWidth={1.5}
              strokeOpacity={0.4}
            />
          );
        })}

        <line
          x1={CX}
          y1={CY}
          x2={needleTip.x}
          y2={needleTip.y}
          style={{ stroke: "var(--ink)", transition: "all 500ms ease" }}
          strokeWidth={3}
          strokeLinecap="round"
        />
        <circle cx={needleTip.x} cy={needleTip.y} r={3} style={{ fill: "var(--ink)" }} />
        <circle
          cx={CX}
          cy={CY}
          r={7}
          style={{ fill: "var(--surface)", stroke: "var(--ink)" }}
          strokeWidth={2.5}
        />
      </svg>

      <div className="mt-1 flex items-end justify-between border-t border-line pt-5">
        <div>
          <span className="font-mono text-6xl font-semibold leading-none tabular-nums text-ink">
            {displayScore}
          </span>
          <p className="mt-2 text-sm font-medium" style={{ color }}>
            {LEVEL_LABEL[alertLevel]}
          </p>
        </div>
        <div className="text-right">
          <p className="font-mono text-xs text-muted">confidence</p>
          <p className="font-mono text-lg tabular-nums text-ink">
            {Math.round(confidence * 100)}%
          </p>
        </div>
      </div>
    </div>
  );
}
