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
    <div className="flex items-center justify-between rounded-xl border border-border bg-surface px-4 py-3">
      <div className="flex h-10 items-end gap-1">
        {BARS.map((bar, i) => (
          <span
            key={i}
            className="w-1.5 rounded-full bg-signal"
            style={{
              height: `${bar.h * 100}%`,
              animationName: active ? "waveform-bar" : "none",
              animationDuration: "900ms",
              animationTimingFunction: "ease-in-out",
              animationIterationCount: "infinite",
              animationDelay: bar.d,
              opacity: active ? 0.9 : 0.25,
            }}
          />
        ))}
      </div>
      <span className="font-mono text-xs uppercase tracking-wide text-muted">
        {active ? "streaming" : "no signal"}
      </span>
    </div>
  );
}
