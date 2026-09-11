"use client";

import {
  Area,
  AreaChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from "recharts";
import { RiskUpdate } from "@/types/risk";

interface RiskTrendProps {
  history: RiskUpdate[];
}

function levelColor(score: number) {
  if (score > 0.7) return "var(--risk-high)";
  if (score > 0.4) return "var(--risk-medium)";
  return "var(--risk-low)";
}

export default function RiskTrend({ history }: RiskTrendProps) {
  const data = history.map((u, i) => ({
    index: i,
    score: Math.round(u.rolling_risk_score * 100),
    chunkId: u.chunk_id,
  }));

  const current = data.at(-1);
  const lineColor = current ? levelColor(current.score / 100) : "var(--muted)";

  return (
    <div className="border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[11px] uppercase tracking-wide text-muted">
          Score trend
        </p>
        <p className="font-mono text-[11px] text-muted">
          {data.length > 0 ? `${data.length} chunks` : "no chunks yet"}
        </p>
      </div>

      <div className="mt-2 h-28">
        {data.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 4 }}>
              <defs>
                <linearGradient id="riskTrendFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={lineColor} stopOpacity={0.28} />
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
                  fontSize: 11,
                  color: "var(--ink)",
                }}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.chunkId ?? ""}
                formatter={(value) => [`${value}`, "score"]}
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
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center font-mono text-xs text-muted">
            trend appears after the second chunk
          </div>
        )}
      </div>
    </div>
  );
}
