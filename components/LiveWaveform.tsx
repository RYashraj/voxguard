"use client";

interface LiveWaveformProps {
  active?: boolean;
}

const SEGMENTS = 6;

// Placeholder column heights (0-1) — Day 3 wired this to the real audio
// stream's amplitude once available.
const COLUMNS = [0.3, 0.55, 0.85, 0.5, 0.95, 0.4, 0.65, 0.8, 0.35, 0.6, 0.25, 0.5];

function segmentColor(segmentIndexFromBottom: number, totalLit: number) {
  const isLit = segmentIndexFromBottom < totalLit;
  if (!isLit) return "var(--line)";
  const ratio = segmentIndexFromBottom / SEGMENTS;
  if (ratio > 0.7) return "var(--risk-high)";
  if (ratio > 0.4) return "var(--risk-medium)";
  return "var(--risk-low)";
}

export default function LiveWaveform({ active = true }: LiveWaveformProps) {
  return (
    <div className="border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[11px] uppercase tracking-wide text-muted">
          Input signal
        </p>
        <span className="flex items-center gap-1.5 font-mono text-xs text-muted">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: active ? "var(--risk-low)" : "var(--line)" }}
          />
          {active ? "streaming" : "no signal"}
        </span>
      </div>
      <div className="mt-3 flex h-12 items-end justify-center gap-2">
        {COLUMNS.map((height, colIndex) => {
          const totalLit = active ? Math.round(height * SEGMENTS) : 1;
          return (
            <div key={colIndex} className="flex w-2.5 flex-1 flex-col-reverse gap-[2px]">
              {Array.from({ length: SEGMENTS }).map((_, segIndex) => (
                <span
                  key={segIndex}
                  className="h-1.5 w-full"
                  style={{ backgroundColor: segmentColor(segIndex, totalLit) }}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
