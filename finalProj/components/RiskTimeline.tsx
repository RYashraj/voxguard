"use client";

import { RiskUpdate } from "@/types/risk";

interface RiskTimelineProps {
  history: RiskUpdate[];
}

function tone(score: number) {
  if (score > 0.7) return "var(--risk-high)";
  if (score > 0.4) return "var(--risk-medium)";
  return "var(--risk-low)";
}

export default function RiskTimeline({ history }: RiskTimelineProps) {
  const points = history.slice(-12);

  return (
    <section className="interactive-surface rounded-card border border-border bg-surface p-5 shadow-card sm:p-6" aria-label="Risk timeline">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Risk timeline</h2>
          <p className="mt-1 text-sm text-muted">Green is normal, yellow is an early warning, red locks sensitive actions. Playback controls the timeline.</p>
        </div>
        <div className="flex gap-3 text-sm text-muted">
          <span><i className="legend-dot bg-risk-low" /> Normal</span>
          <span><i className="legend-dot bg-risk-medium" /> Warning</span>
          <span><i className="legend-dot bg-risk-high" /> Block</span>
        </div>
      </div>

      <div className="mt-5 h-44 rounded-control border border-border bg-background px-3 py-3">
        {points.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">Start a call to see the risk build over time.</div>
        ) : (
          <div className="flex h-full items-end gap-2 sm:gap-3">
            {points.map((point) => (
              <div key={point.chunk_id} className="flex min-w-0 flex-1 flex-col items-center justify-end gap-2">
                <span className="font-mono text-xs font-semibold text-foreground">{Math.round(point.rolling_risk_score * 100)}</span>
                <div className="flex h-24 w-full items-end rounded-sm bg-surface-sunken">
                  <div
                    className="w-full rounded-sm transition-all duration-500"
                    style={{ height: `${Math.max(6, point.rolling_risk_score * 100)}%`, backgroundColor: tone(point.rolling_risk_score) }}
                    title={`${point.chunk_id}: ${Math.round(point.rolling_risk_score * 100)}%`}
                  />
                </div>
                <span className="font-mono text-xs text-muted">{point.chunk_id.replace("chunk_", "#")}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}