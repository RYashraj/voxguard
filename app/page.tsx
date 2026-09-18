"use client";

import { useState } from "react";
import RiskGauge from "@/components/RiskGauge";
import AlertBanner from "@/components/AlertBanner";
import LiveWaveform from "@/components/LiveWaveform";
import CallContextInput from "@/components/CallContextInput";
import AdvisoryPanel from "@/components/AdvisoryPanel";
import LiveVoiceDetector from "@/components/LiveVoiceDetector";
import ThemeToggle from "@/components/ThemeToggle";
import Logo from "@/components/Logo";
import AmbientBackground from "@/components/AmbientBackground";
import BootIntro from "@/components/BootIntro";
import { useRiskSocket } from "@/hooks/useRiskSocket";
import { SimulationContext } from "@/types/risk";

const WS_URL = process.env.NEXT_PUBLIC_RISK_WS_URL ?? "ws://127.0.0.1:8000/ws/session";
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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

  const [sampleType, setSampleType] = useState<string>("gradual_escalation");

  const [simContext, setSimContext] = useState<SimulationContext>({
    caller_context: "not_provided",
    transaction_type: "not_provided",
    user_confirmation_required: true,
  });

  async function handleStartCall() {
    setSimStatus("starting");
    try {
      const payload: {
        context?: SimulationContext;
        file_path?: string;
        scenario?: string;
      } = { context: simContext };

      if (sampleType === "deepfake") {
        payload.file_path = "data/test_audio/asvspoof_spoof_clips/LA_E_5932896.wav";
        payload.scenario = "suspicious";
      } else if (sampleType === "genuine") {
        payload.file_path = "data/benchmark_indic_language/hi_in_spk1_female_1608.wav";
        payload.scenario = "clean";
      } else if (sampleType === "user_human") {
        payload.file_path = "data/sample_calls/shreyas_human_sample.wav";
        payload.scenario = "clean";
      } else if (sampleType === "user_clone") {
        payload.file_path = "data/sample_calls/shreyas_clone_sample.wav";
        payload.scenario = "suspicious";
      } else {
        payload.file_path = "data/sample_calls/gradual_escalation.wav";
        payload.scenario = "gradual_escalation";
      }

      const res = await fetch(`${API_BASE_URL}/start-simulation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`start-simulation failed: ${res.status}`);
      setSimStatus("running");
    } catch (err) {
      console.error("Failed to start simulation", err);
      setSimStatus("error");
    }
  }

  async function handleStopCall() {
    try {
      await fetch(`${API_BASE_URL}/stop-simulation`, { method: "POST" });
      setSimStatus("idle");
    } catch (err) {
      console.error("Failed to stop simulation", err);
    }
  }

  const [activeView, setActiveView] = useState<"stream" | "detector">("detector");

  return (
    <div className="relative isolate min-h-screen">
      <BootIntro />
      <AmbientBackground />
      <main className="mx-auto min-h-screen w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-12">
        <header className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <Logo />
              <span className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-xs text-muted shadow-card">
                <span
                  className={`h-1.5 w-1.5 shrink-0 rounded-full ${status === "open"
                    ? "bg-risk-low"
                    : status === "connecting"
                      ? "bg-risk-medium animate-pulse"
                      : "bg-risk-high"
                    }`}
                />
                {STATUS_LABEL[status]}
              </span>
            </div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
              Voice Impersonation & Clone Detection
            </h1>
            <p className="mt-1.5 max-w-md text-sm leading-relaxed text-muted">
              AI-powered real-time detection of synthetic speech and voice cloning.
            </p>
          </div>
          <ThemeToggle />
        </header>

        {/* Primary View Mode Switcher */}
        <div className="mt-6 flex flex-wrap items-center gap-3 border-b border-border pb-4">
          <button
            onClick={() => setActiveView("detector")}
            className={`btn-tactile flex items-center gap-2 rounded-control px-4 py-2 text-sm font-medium transition-colors ${
              activeView === "detector"
                ? "bg-accent text-accent-contrast shadow-card"
                : "border border-border bg-surface text-muted hover:text-foreground"
            }`}
          >
            <span>🎙️</span> Real-Time Voice Detector (Mic & Upload)
          </button>
          <button
            onClick={() => setActiveView("stream")}
            className={`btn-tactile flex items-center gap-2 rounded-control px-4 py-2 text-sm font-medium transition-colors ${
              activeView === "stream"
                ? "bg-accent text-accent-contrast shadow-card"
                : "border border-border bg-surface text-muted hover:text-foreground"
            }`}
          >
            <span>📞</span> Live Call Stream Monitor
          </button>
        </div>

        {/* View 1: Real-Time Voice Detector (Mic & Upload) */}
        {activeView === "detector" && (
          <div className="mt-6">
            <LiveVoiceDetector apiBaseUrl={API_BASE_URL} />
          </div>
        )}

        {/* View 2: Live Call Stream Monitor */}
        {activeView === "stream" && (
          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
            {/* Main column */}
            <div className="flex min-w-0 flex-col gap-6">
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

              <AdvisoryPanel
                advisory={latest?.advisory}
                onStopCall={handleStopCall}
              />
            </div>

            {/* Side column: simulator controls + session detail */}
            <div className="flex min-w-0 flex-col gap-6">
              <div className="interactive-surface rounded-card border border-border bg-surface p-5 shadow-card space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-foreground" htmlFor="sample-selector">
                    Audio stream sample
                  </label>
                  <span className="text-xs text-muted">Model input</span>
                </div>
                <select
                  id="sample-selector"
                  value={sampleType}
                  onChange={(e) => setSampleType(e.target.value)}
                  disabled={simStatus === "starting" || simStatus === "running"}
                  className="w-full rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground transition-colors hover:border-border-strong focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent disabled:opacity-50"
                >
                  <option value="user_human">👤 My Human Voice (Shreyas - Genuine ~0% risk)</option>
                  <option value="user_clone">🤖 My AI Clone Voice (Shreyas - ElevenLabs high risk)</option>
                  <option value="gradual_escalation">Demo script (gradual escalation: low → high)</option>
                  <option value="deepfake">ASVspoof synthetic deepfake (high risk &gt;90%)</option>
                  <option value="genuine">Hindi genuine human speech (safe ~0-5%)</option>
                </select>

                {status === "open" && (
                  <div className="flex gap-2 pt-1">
                    <button
                      onClick={handleStartCall}
                      disabled={simStatus === "starting" || simStatus === "running"}
                      className="btn-tactile flex-1 rounded-control bg-accent px-4 py-2 text-sm font-medium text-accent-contrast shadow-card transition-opacity hover:opacity-90 disabled:opacity-50"
                    >
                      {simStatus === "idle" && "Start call"}
                      {simStatus === "starting" && "Starting…"}
                      {simStatus === "running" && "Call running"}
                      {simStatus === "error" && "Failed to start — retry"}
                    </button>
                    {simStatus === "running" && (
                      <button
                        onClick={handleStopCall}
                        className="btn-tactile rounded-control border border-risk-highBorder bg-surface px-4 py-2 text-sm font-medium text-risk-high transition-colors hover:bg-risk-highBg"
                      >
                        Stop call
                      </button>
                    )}
                  </div>
                )}
              </div>

              <CallContextInput
                value={simContext}
                onChange={setSimContext}
                disabled={simStatus === "starting" || simStatus === "running"}
              />

              <div className="interactive-surface rounded-card border border-border bg-surface-raised p-4 shadow-card">
                {latest ? (
                  <div className="space-y-2 text-sm">
                    <p className="flex items-center justify-between text-muted">
                      <span>Chunk ID</span>
                      <span className="font-mono text-xs text-foreground">{latest.chunk_id}</span>
                    </p>
                    <p className="flex items-center justify-between text-muted">
                      <span>Alert level</span>
                      <span className="font-mono text-xs uppercase text-foreground">
                        {latest.alert_level}
                      </span>
                    </p>

                    <details className="pt-2">
                      <summary className="cursor-pointer text-xs font-medium text-muted transition-colors hover:text-foreground">
                        Risk updates payload
                      </summary>
                      <pre className="mt-2 max-w-full overflow-x-auto rounded-control bg-background p-3 font-mono text-[11px] text-foreground">
                        {JSON.stringify(latest, null, 2)}
                      </pre>
                    </details>
                  </div>
                ) : (
                  <p className="text-sm text-muted">Waiting for risk stream data...</p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
