"use client";

import { useState } from "react";
import RiskGauge from "@/components/RiskGauge";
import AlertBanner from "@/components/AlertBanner";
import LiveWaveform from "@/components/LiveWaveform";
import { useRiskSocket } from "@/hooks/useRiskSocket";

// Day 5: pointed at Shreyas's real backend (falls back to the Day 3 mock
// server if the env vars aren't set, so local dev without the backend
// running still works).
const WS_URL = process.env.NEXT_PUBLIC_RISK_WS_URL ?? "ws://localhost:8080";
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const STATUS_LABEL: Record<string, string> = {
  connecting: "connecting…",
  open: "live",
  closed: "reconnecting…",
};

export default function Home() {
  const { latest, status } = useRiskSocket(WS_URL);
  const hasReceivedData = latest !== null;

  const [simStatus, setSimStatus] = useState<
    "idle" | "starting" | "running" | "error"
  >("idle");

  async function handleStartCall() {
    setSimStatus("starting");
    try {
      const res = await fetch(`${API_BASE_URL}/start-simulation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Empty body — backend defaults to the demo WAV + gradual_escalation
        // scenario when no fields are given.
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error(`start-simulation failed: ${res.status}`);
      setSimStatus("running");
    } catch (err) {
      console.error("Failed to start simulation", err);
      setSimStatus("error");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-12">
      <header>
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs uppercase tracking-wide text-signal">
            VoxGuard
          </p>
          <span className="flex items-center gap-1.5 font-mono text-xs text-muted">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                status === "open"
                  ? "bg-risk-low"
                  : status === "connecting"
                  ? "bg-risk-medium"
                  : "bg-risk-high"
              }`}
            />
            {STATUS_LABEL[status]}
          </span>
        </div>
        <h1 className="mt-1 text-2xl font-semibold text-foreground">
          Call risk monitor
        </h1>
        <p className="mt-1 text-sm text-muted">
          Live voice-impersonation risk score for the active call.
        </p>
      </header>

      {status === "open" && (
        <button
          onClick={handleStartCall}
          disabled={simStatus === "starting" || simStatus === "running"}
          className="rounded-xl border border-border bg-surface px-4 py-2 font-mono text-xs text-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {simStatus === "idle" && "Start call"}
          {simStatus === "starting" && "Starting…"}
          {simStatus === "running" && "Call running"}
          {simStatus === "error" && "Failed to start — retry"}
        </button>
      )}

      <LiveWaveform active={hasReceivedData} />

      <RiskGauge
        score={latest?.rolling_risk_score ?? 0}
        confidence={latest?.confidence ?? 0}
        alertLevel={latest?.alert_level ?? "low"}
      />

      <AlertBanner
        alertLevel={latest?.alert_level ?? "low"}
        flags={latest?.flags ?? []}
      />

      <div className="rounded-xl border border-border bg-surface px-4 py-3 font-mono text-xs text-muted">
        {latest ? (
          <>
            chunk {latest.chunk_id} · {latest.timestamp} · chunk_score{" "}
            {latest.chunk_score.toFixed(2)}
          </>
        ) : (
          `waiting for first chunk… (${STATUS_LABEL[status]})`
        )}
      </div>
    </main>
  );
}
