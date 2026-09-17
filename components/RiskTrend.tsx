"use client";

import {
  Area,
  AreaChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from "recharts";
import { RiskUpdate } from "@/types/risk";
import {
  MOCK_PROSODY_DRIFT_ENABLED,
  getMockProsodyScore,
  getMockIdentityDrift,
} from "@/lib/mockSignals";

interface RiskTrendProps {
  history: RiskUpdate[];
}

function levelColor(score: number) {
  if (score > 0.7) return "var(--risk-high)";
  if (score > 0.4) return "var(--risk-medium)";
  return "var(--risk-low)";
}

export default function RiskTrend({ history }: RiskTrendProps) {
  const data = history.map((u, i) => {
    // Mock fallback (feature-flagged) prosody & identity_drift if the WS
    // payload didn't include them yet — see lib/mockSignals.ts.
    const prosodyVal =
      u.prosody_score ?? (MOCK_PROSODY_DRIFT_ENABLED ? getMockProsodyScore(u.chunk_id) : 0);

    const driftVal =
      u.identity_drift ?? (MOCK_PROSODY_DRIFT_ENABLED ? getMockIdentityDrift(u.chunk_id) : 0);

    return {
      index: i,
      score: Math.round(u.rolling_risk_score * 100),
      prosody: Math.round(prosodyVal * 100),
      drift: Math.round(driftVal * 100),
      chunkId: u.chunk_id,
    };
  });

  const current = data.at(-1);
  const lineColor = current ? levelColor(current.score / 100) : "var(--muted)";

  return (
    <div className="border border-line bg-surface p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-mono text-sm uppercase tracking-wide text-muted font-semibold">
          Multi-Layer Risk Trend
        </p>
        <div className="flex flex-wrap items-center gap-4 font-mono text-xs text-muted">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: lineColor }} />
            Rolling Risk
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-500" />
            Prosody Anomaly
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
            Identity Drift
          </span>
        </div>
      </div>

      <div className="mt-3 h-32">
        {data.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 4 }}>
              <defs>
                <linearGradient id="riskTrendFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={lineColor} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <YAxis domain={[0, 100]} hide />
              <ReferenceLine y={40} stroke="var(--line)" strokeDasharray="2 3" />
              <ReferenceLine y={70} stroke="var(--line)" strokeDasharray="2 3" />
              <Tooltip
                cursor={{ stroke: "var(--line)", strokeWidth: 1 }}
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--line)",
                  borderRadius: 0,
                  fontFamily: "IBM Plex Mono, monospace",
                  fontSize: 13,
                  color: "var(--ink)",
                }}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.chunkId ?? ""}
                formatter={(value, name) => {
                  const labels: Record<string, string> = {
                    score: "Rolling Risk",
                    prosody: "Prosody Anomaly",
                    drift: "Identity Drift",
                  };
                  return [`${value}%`, labels[String(name)] ?? name];
                }}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke={lineColor}
                strokeWidth={2}
                fill="url(#riskTrendFill)"
                isAnimationActive={false}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="prosody"
                stroke="#a855f7"
                strokeWidth={2}
                strokeDasharray="4 2"
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="drift"
                stroke="#ef4444"
                strokeWidth={2.5}
                dot={false}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center font-mono text-sm text-muted">
            multi-layer trend appears after the second chunk
          </div>
        )}
      </div>
    </div>
  );
}
