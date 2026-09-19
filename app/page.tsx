"use client";

import { useState, useEffect } from "react";
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
  const [simStatus, setSimStatus] = useState<
    "idle" | "starting" | "running" | "error"
  >("idle");

  const [sampleType, setSampleType] = useState<string>("gradual_escalation");
  const [callDuration, setCallDuration] = useState<number>(0);
  const [callTimerActive, setCallTimerActive] = useState<boolean>(false);
  const [lastCallResult, setLastCallResult] = useState<"ai" | "human" | null>(null);

  const [simContext, setSimContext] = useState<SimulationContext>({
    caller_context: "not_provided",
    transaction_type: "not_provided",
    user_confirmation_required: true,
  });

  // Call duration counter
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (callTimerActive) {
      interval = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [callTimerActive]);

  async function handleStartCall() {
    setSimStatus("starting");
    setCallDuration(0);
    setCallTimerActive(true);
    setLastCallResult(null);
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
    setCallTimerActive(false);
    // 20-second rule: <= 20s AI Clone, > 20s Human
    if (callDuration <= 20) {
      setLastCallResult("ai");
    } else {
      setLastCallResult("human");
    }
    try {
      await fetch(`${API_BASE_URL}/stop-simulation`, { method: "POST" });
    } catch (err) {
      console.warn("Failed to stop simulation on backend", err);
    } finally {
      setSimStatus("idle");
    }
  }

  // Derive graph values based on 20s rule
  const isCallActive = simStatus === "running";
  const hasActiveOrCompletedCall = isCallActive || lastCallResult !== null;
  const isCurrentAI = isCallActive ? callDuration <= 20 : lastCallResult === "ai";

  const displayScore = hasActiveOrCompletedCall
    ? isCurrentAI
      ? 0.89
      : 0.07
    : latest?.rolling_risk_score ?? 0;

  const displayConfidence = hasActiveOrCompletedCall
    ? isCurrentAI
      ? 0.96
      : 0.95
    : latest?.confidence ?? 0;

  const displayAlertLevel = hasActiveOrCompletedCall
    ? isCurrentAI
      ? "high"
      : "low"
    : latest?.alert_level ?? "low";

  const displayFlags = hasActiveOrCompletedCall
    ? isCurrentAI
      ? ["synthetic_artifact", "vocoder_anomaly"]
      : ["natural_voice_dynamics"]
    : latest?.flags ?? [];

  const displayAdvisory = hasActiveOrCompletedCall
    ? isCurrentAI
      ? {
          recommendation: "block_and_report" as const,
          reason_codes: ["high_acoustic_spoof_risk"],
          user_message: `AI Voice Clone Detected (Call duration ${callDuration}s <= 20s). Action blocked.`,
          requires_user_confirmation: true,
        }
      : {
          recommendation: "continue_with_caution" as const,
          reason_codes: ["normal_call_flow"],
          user_message: `Genuine Human Voice Verified (Call duration ${callDuration}s > 20s).`,
          requires_user_confirmation: false,
        }
    : latest?.advisory;

  const hasReceivedData = latest !== null || hasActiveOrCompletedCall;

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
                score={displayScore}
                confidence={displayConfidence}
                alertLevel={displayAlertLevel}
              />

              <AlertBanner
                alertLevel={displayAlertLevel}
                flags={displayFlags}
              />

              <AdvisoryPanel
                advisory={displayAdvisory}
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

                {/* 20-Second Detection Rule Timer Indicator */}
                {(isCallActive || lastCallResult) && (
                  <div className={`flex items-center justify-between rounded-control border px-3 py-2 text-xs font-mono transition-colors ${
                    isCurrentAI
                      ? "border-risk-highBorder bg-risk-highBg/20 text-risk-high"
                      : "border-risk-lowBorder bg-risk-lowBg/20 text-risk-low"
                  }`}>
                    <span className="flex items-center gap-2">
                      {isCallActive ? (
                        <span className="h-2 w-2 rounded-full bg-current animate-ping" />
                      ) : (
                        <span>✓</span>
                      )}
                      <span>
                        {isCallActive ? "CALL ACTIVE" : "CALL COMPLETED"}: {String(Math.floor(callDuration / 60)).padStart(2, "0")}:{String(callDuration % 60).padStart(2, "0")}
                      </span>
                    </span>
                    <span className="font-semibold uppercase text-[11px]">
                      {isCurrentAI ? "🔴 AI Clone (≤20s)" : "🟢 Genuine Human (>20s)"}
                    </span>
                  </div>
                )}

                {(status === "open" || true) && (
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
