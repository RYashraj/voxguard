"use client";

interface LiveWaveformProps {
  active?: boolean;
}

// Placeholder bar heights/delays — Day 3 will swap this for amplitude
// derived from the real audio stream.
const BARS = [
  { h: 0.4, d: "0ms" },
  { h: 0.75, d: "90ms" },
  { h: 1, d: "180ms" },
  { h: 0.55, d: "270ms" },
  { h: 0.85, d: "360ms" },
  { h: 0.35, d: "450ms" },
  { h: 0.65, d: "540ms" },
  { h: 0.9, d: "630ms" },
  { h: 0.45, d: "720ms" },
  { h: 0.7, d: "810ms" },
  { h: 0.3, d: "900ms" },
  { h: 0.6, d: "990ms" },
];

export default function LiveWaveform({ active = true }: LiveWaveformProps) {
  return (
    <div className="interactive-surface flex items-center justify-between rounded-card border border-border bg-surface px-4 py-3.5 shadow-card">
      <div className="flex h-9 items-end gap-1">
        {BARS.map((bar, i) => (
          <span
            key={i}
            className="w-1.5 rounded-full bg-accent"
            style={{
              height: `${bar.h * 100}%`,
              animationName: active ? "waveform-bar" : "none",
              animationDuration: "900ms",
              animationTimingFunction: "ease-in-out",
              animationIterationCount: "infinite",
              animationDelay: bar.d,
              opacity: active ? 0.85 : 0.25,
            }}
          />
        ))}
      </div>
      <span className="flex items-center gap-1.5 text-xs text-muted">
        <span className={`h-1.5 w-1.5 rounded-full ${active ? "bg-risk-low" : "bg-muted"}`} />
        {active ? "streaming" : "no signal"}
      </span>
    </div>
  );
}
