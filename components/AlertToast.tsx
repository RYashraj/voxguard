"use client";

import { useEffect, useRef, useState } from "react";
import { AlertLevel } from "@/types/risk";

interface AlertToastProps {
  alertLevel: AlertLevel;
  chunkId?: string;
  flags?: string[];
  onDismiss?: () => void;
}

export default function AlertToast({
  alertLevel,
  chunkId,
  flags = [],
  onDismiss,
}: AlertToastProps) {
  const [visible, setVisible] = useState(false);
  // Snapshot of the chunk/flags that triggered the toast, frozen at fire
  // time so the toast doesn't silently change content while it's showing.
  const [shown, setShown] = useState<{ chunkId?: string; flags: string[] }>({
    chunkId: undefined,
    flags: [],
  });
  const prevAlertLevelRef = useRef<AlertLevel | undefined>(undefined);

  useEffect(() => {
    const wasHigh = prevAlertLevelRef.current === "high";
    prevAlertLevelRef.current = alertLevel;

    // Fire only on the low/medium -> high transition. Intentionally not
    // depending on chunkId/flags here — otherwise every subsequent
    // WebSocket update while alert_level stays "high" would retrigger
    // the toast (spam).
    if (alertLevel === "high" && !wasHigh) {
      setShown({ chunkId, flags });
      setVisible(true);

      const timer = setTimeout(() => {
        setVisible(false);
        if (onDismiss) onDismiss();
      }, 6000);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alertLevel]);

  if (!visible) return null;

  return (
    <div className="fixed top-5 right-5 z-40 max-w-md border-2 border-red-500 bg-surface p-4 shadow-[0_0_20px_rgba(239,68,68,0.3)] font-mono text-ink">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 text-red-500">
          <span className="h-3 w-3 rounded-full bg-red-500 animate-ping" />
          <strong className="text-sm uppercase tracking-wide text-red-500">
            High Threat In-App Toast
          </strong>
        </div>
        <button
          onClick={() => {
            setVisible(false);
            if (onDismiss) onDismiss();
          }}
          className="text-muted hover:text-ink text-sm font-bold px-1"
        >
          ✕
        </button>
      </div>

      <p className="mt-2 text-xs text-ink">
        Impersonation risk score exceeded threshold on{" "}
        <span className="font-bold text-red-500">{shown.chunkId ?? "current chunk"}</span>.
      </p>

      {shown.flags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {shown.flags.map((flag) => (
            <span
              key={flag}
              className="border border-red-500/40 bg-red-950/20 px-1.5 py-0.5 text-[10px] text-red-400 font-mono"
            >
              {flag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
