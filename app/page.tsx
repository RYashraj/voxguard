"use client";

import { useState } from "react";
import { useSession, signIn, signOut } from "next-auth/react";
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
  const { status: authStatus } = useSession();
  const { latest, history, status: socketStatus, clear } = useRiskSocket(WS_URL);
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

  if (authStatus === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <p className="font-mono text-sm text-muted">Loading...</p>
      </main>
    );
  }

  if (authStatus === "unauthenticated") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-6 rounded-2xl border border-line bg-surface p-10 text-center">
          <svg width="40" height="40" viewBox="0 0 30 30" aria-hidden="true">
            <rect x="0.75" y="0.75" width="28.5" height="28.5" style={{ stroke: "var(--ink)" }} strokeWidth="1.5" fill="none" />
            <path d="M8 9 L15 21 L22 9" style={{ stroke: "var(--ink)" }} strokeWidth="2" fill="none" strokeLinecap="square" />
          </svg>
          <div>
            <h1 className="text-2xl font-semibold text-ink">VoxGuard</h1>
            <p className="mt-2 max-w-sm text-sm text-muted">Sign in with your Google account to access the active call monitoring dashboard.</p>
          </div>
          <button
            onClick={() => signIn("google")}
            className="rounded-lg bg-ink px-6 py-2.5 font-medium text-surface transition-opacity hover:opacity-90"
          >
            Sign in with Google
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-[1600px] w-full px-5 py-8 md:px-10 md:py-10">
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
              <p className="font-mono text-lg font-bold tracking-wide text-ink">
                VOXGUARD
              </p>
              <p className="text-sm text-muted">Call risk monitor</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 border border-line px-3 py-2 font-mono text-sm text-muted">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: STATUS_COLOR[socketStatus] }}
              />
              {STATUS_LABEL[socketStatus]}
            </span>
            <ThemeToggle />
            <button
              onClick={() => signOut()}
              className="border border-line px-4 py-2 font-mono text-sm text-muted hover:text-ink transition-colors"
            >
              Sign out
            </button>
          </div>
        </header>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold text-ink md:text-4xl">
              Active call session
            </h1>
            <p className="mt-2 text-lg text-muted">
              Live voice-impersonation risk score, updated per audio chunk.
            </p>
          </div>

          {socketStatus === "open" && (
            <div className="flex gap-3 items-center">
              <button
                onClick={handleStartCall}
                disabled={simStatus === "starting" || simStatus === "running"}
                className="border border-line bg-surface px-6 py-3 font-mono text-sm font-bold text-ink transition-colors hover:border-ink disabled:opacity-50"
              >
                {simStatus === "idle" && "Start call"}
                {simStatus === "starting" && "Starting…"}
                {simStatus === "running" && "Call running"}
                {simStatus === "error" && "Failed to start — retry"}
              </button>
              
              {simStatus === "running" && (
                <button
                  onClick={async () => {
                    try {
                      await fetch(`${API_BASE_URL}/stop-simulation`, { method: "POST" });
                      setSimStatus("idle");
                    } catch (e) {
                      console.error(e);
                    }
                  }}
                  className="border border-risk-high text-risk-high hover:bg-risk-high hover:text-surface px-6 py-3 font-mono text-sm font-bold transition-colors"
                >
                  Stop call
                </button>
              )}
              
              {(hasReceivedData || history.length > 0) && simStatus === "idle" && (
                <button
                  onClick={clear}
                  className="border border-line px-6 py-3 font-mono text-sm font-bold text-muted transition-colors hover:text-ink hover:border-ink"
                >
                  Clear data
                </button>
              )}
            </div>
          )}
        </div>

        <div className="mt-6 grid gap-5 lg:grid-cols-12">
          <section className="flex flex-col gap-5 lg:col-span-7">
            <RiskGauge
              score={latest?.rolling_risk_score ?? 0}
              confidence={latest?.confidence ?? 0}
              alertLevel={latest?.alert_level ?? "low"}
            />
            <LiveWaveform active={socketStatus === "open" && hasReceivedData} />
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

        <div className="mt-5 border border-line bg-surface px-5 py-4 font-mono text-sm text-muted">
          {latest ? (
            <>
              chunk {latest.chunk_id} · {latest.timestamp} · chunk_score{" "}
              {latest.chunk_score.toFixed(2)}
            </>
          ) : (
            `waiting for first chunk… (${STATUS_LABEL[socketStatus]})`
          )}
        </div>
      </div>
    </main>
  );
}
