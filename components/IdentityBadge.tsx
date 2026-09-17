"use client";

interface IdentityBadgeProps {
  drift: number; // 0.0 to 1.0 (0 = perfect match, 1 = total drift / speaker swap)
  active?: boolean;
}

export default function IdentityBadge({ drift, active = true }: IdentityBadgeProps) {
  const clampedDrift = Math.max(0, Math.min(1, drift));
  const confidencePercent = Math.round((1 - clampedDrift) * 100);
  const isHighDrift = clampedDrift >= 0.5;

  if (!active) {
    return (
      <div className="flex items-center justify-between border border-line bg-surface p-3 font-mono text-xs text-muted">
        <span className="uppercase tracking-wider">Identity Confidence</span>
        <span>-- %</span>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-2 border p-3 font-mono text-xs transition-all duration-300 ${
        isHighDrift
          ? "border-red-500 bg-red-950/30 text-red-400 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.25)]"
          : "border-line bg-surface text-ink"
      }`}
    >
      <div className="flex items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            isHighDrift ? "bg-red-500 animate-ping" : "bg-emerald-500"
          }`}
        />
        <span className="font-bold tracking-wide">
          {isHighDrift ? "⚠️ SPEAKER SWAP ALERT" : "IDENTITY CONFIDENCE"}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-muted">
          Drift: <span className="font-bold text-ink">{Math.round(clampedDrift * 100)}%</span>
        </span>
        <span
          className={`px-2 py-0.5 font-bold rounded ${
            isHighDrift
              ? "bg-red-500 text-white"
              : "bg-emerald-500/10 text-emerald-600 border border-emerald-500/30"
          }`}
        >
          {confidencePercent}% Confidence
        </span>
      </div>
    </div>
  );
}
