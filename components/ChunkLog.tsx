"use client";

import { RiskUpdate } from "@/types/risk";

interface ChunkLogProps {
  history: RiskUpdate[];
}

const LEVEL_COLOR: Record<RiskUpdate["alert_level"], string> = {
  low: "var(--risk-low)",
  medium: "var(--risk-medium)",
  high: "var(--risk-high)",
};

function formatClock(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour12: false,
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function ChunkLog({ history }: ChunkLogProps) {
  const rows = [...history].reverse();

  return (
    <div className="flex flex-1 flex-col border border-line bg-surface">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <p className="font-mono text-[11px] uppercase tracking-wide text-muted">
          Chunk log
        </p>
        <p className="font-mono text-[11px] text-muted">
          last {rows.length || 0}
        </p>
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-1 items-center justify-center px-4 py-8 font-mono text-xs text-muted">
          no chunks received yet
        </div>
      ) : (
        <ul className="max-h-56 divide-y divide-line overflow-y-auto">
          {rows.map((chunk, i) => (
            <li
              key={chunk.chunk_id}
              className="flex items-center gap-3 px-4 py-2 font-mono text-xs"
            >
              <span className="w-6 shrink-0 text-muted">
                {String(rows.length - i).padStart(2, "0")}
              </span>
              <span className="w-16 shrink-0 text-muted">
                {formatClock(chunk.timestamp)}
              </span>
              <span className="flex-1 truncate text-ink">{chunk.chunk_id}</span>
              <span className="w-10 shrink-0 text-right tabular-nums text-muted">
                {Math.round(chunk.chunk_score * 100)}
              </span>
              <span
                className="w-10 shrink-0 text-right tabular-nums font-semibold"
                style={{ color: LEVEL_COLOR[chunk.alert_level] }}
              >
                {Math.round(chunk.rolling_risk_score * 100)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
