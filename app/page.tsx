"use client";

import { useState } from "react";
import RiskGauge from "@/components/RiskGauge";
import AlertBanner from "@/components/AlertBanner";
import LiveWaveform from "@/components/LiveWaveform";
import RiskTrend from "@/components/RiskTrend";
import ChunkLog from "@/components/ChunkLog";
import ThemeToggle from "@/components/ThemeToggle";
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

const STATUS_COLOR: Record<string, string> = {
  connecting: "var(--risk-medium)",
  open: "var(--risk-low)",
  closed: "var(--risk-high)",
};

export default function Home() {
  const { latest, history, status } = useRiskSocket(WS_URL);
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
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-6xl px-5 py-8 md:px-10 md:py-10">
        <header className="flex items-center justify-between border-b border-line pb-5">
          <div className="flex items-center gap-3">
            <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
              <rect
                x="0.75"
                y="0.75"
                width="28.5"
                height="28.5"
                style={{ stroke: "var(--ink)" }}
                strokeWidth="1.5"
                fill="none"
              />
              <path
                d="M8 9 L15 21 L22 9"
                style={{ stroke: "var(--ink)" }}
                strokeWidth="2"
                fill="none"
                strokeLinecap="square"
              />
            </svg>
            <div>
              <p className="font-mono text-sm font-medium tracking-wide text-ink">
                VOXGUARD
              </p>
              <p className="text-xs text-muted">Call risk monitor</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 border border-line px-2.5 py-1.5 font-mono text-xs text-muted">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: STATUS_COLOR[status] }}
              />
              {STATUS_LABEL[status]}
            </span>
            <ThemeToggle />
          </div>
        </header>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-ink md:text-2xl">
              Active call session
            </h1>
            <p className="mt-1 text-sm text-muted">
              Live voice-impersonation risk score, updated per audio chunk.
            </p>
          </div>

          {status === "open" && (
            <button
              onClick={handleStartCall}
              disabled={simStatus === "starting" || simStatus === "running"}
              className="border border-line bg-surface px-4 py-2 font-mono text-xs text-ink transition-colors hover:border-ink disabled:opacity-50"
            >
              {simStatus === "idle" && "Start call"}
              {simStatus === "starting" && "Starting…"}
              {simStatus === "running" && "Call running"}
              {simStatus === "error" && "Failed to start — retry"}
            </button>
          )}
        </div>

        <div className="mt-6 grid gap-5 lg:grid-cols-12">
          <section className="flex flex-col gap-5 lg:col-span-7">
            <RiskGauge
              score={latest?.rolling_risk_score ?? 0}
              confidence={latest?.confidence ?? 0}
              alertLevel={latest?.alert_level ?? "low"}
            />
            <LiveWaveform active={status === "open" && hasReceivedData} />
          </section>

          <section className="flex flex-col gap-5 lg:col-span-5">
            <AlertBanner
              alertLevel={latest?.alert_level ?? "low"}
              flags={latest?.flags ?? []}
            />
            <RiskTrend history={history} />
            <ChunkLog history={history} />
          </section>
        </div>

        <div className="mt-5 border border-line bg-surface px-4 py-3 font-mono text-xs text-muted">
          {latest ? (
            <>
              chunk {latest.chunk_id} · {latest.timestamp} · chunk_score{" "}
              {latest.chunk_score.toFixed(2)}
            </>
          ) : (
            `waiting for first chunk… (${STATUS_LABEL[status]})`
          )}
        </div>
      </div>
    </main>
  );
}
