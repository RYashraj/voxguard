"use client";

import { useState } from "react";
import RiskGauge from "@/components/RiskGauge";
import AlertBanner from "@/components/AlertBanner";
import LiveWaveform from "@/components/LiveWaveform";
import CallContextInput from "@/components/CallContextInput";
import AdvisoryPanel from "@/components/AdvisoryPanel";
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
      const payload: Record<string, any> = { context: simContext };

      if (sampleType === "deepfake") {
        payload.file_path = "data/test_audio/asvspoof_spoof_clips/LA_E_5932896.wav";
        payload.scenario = "suspicious";
      } else if (sampleType === "genuine") {
        payload.file_path = "data/benchmark_indic_language/hi_in_spk1_female_1608.wav";
        payload.scenario = "clean";
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

      {/* Audio Sample / Demo Scenario Selector */}
      <div className="rounded-xl border border-border bg-surface p-4 text-xs text-foreground space-y-2">
        <div className="flex items-center justify-between">
          <label className="font-semibold text-sm text-foreground" htmlFor="sample-selector">
            Audio Stream Sample
          </label>
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted">
            Model Input
          </span>
        </div>
        <select
          id="sample-selector"
          value={sampleType}
          onChange={(e) => setSampleType(e.target.value)}
          disabled={simStatus === "starting" || simStatus === "running"}
          className="w-full rounded-lg border border-border bg-background px-3 py-1.5 font-sans text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-signal disabled:opacity-50"
        >
          <option value="gradual_escalation">Demo Script (Gradual Escalation: Low → High)</option>
          <option value="deepfake">ASVspoof Synthetic Deepfake (High Risk &gt;90%)</option>
          <option value="genuine">Hindi Genuine Human Speech (Safe ~0-5%)</option>
        </select>
      </div>

      <CallContextInput
        value={simContext}
        onChange={setSimContext}
        disabled={simStatus === "starting" || simStatus === "running"}
      />

      {status === "open" && (
        <div className="flex gap-2">
          <button
            onClick={handleStartCall}
            disabled={simStatus === "starting" || simStatus === "running"}
            className="flex-1 rounded-xl border border-border bg-surface px-4 py-2 font-mono text-xs text-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {simStatus === "idle" && "Start call"}
            {simStatus === "starting" && "Starting…"}
            {simStatus === "running" && "Call running"}
            {simStatus === "error" && "Failed to start — retry"}
          </button>
          {simStatus === "running" && (
            <button
              onClick={handleStopCall}
              className="rounded-xl border border-border bg-surface px-4 py-2 font-mono text-xs text-risk-high transition-opacity hover:opacity-90"
            >
              Stop call
            </button>
          )}
        </div>
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

      <AdvisoryPanel
        advisory={latest?.advisory}
        onStopCall={handleStopCall}
      />

      <div className="rounded-xl border border-border bg-surface px-4 py-3 font-mono text-xs text-muted">
        {latest ? (
          <div className="space-y-1">
            <p>
              Chunk ID:{" "}
              <span className="text-foreground">{latest.chunk_id}</span>
            </p>
            <p>
              Alert Level:{" "}
              <span className="text-foreground uppercase">
                {latest.alert_level}
              </span>
            </p>

            <div className="pt-2 border-t border-border">
              <p className="font-semibold text-foreground mb-1">
                Risk updates payload:
              </p>
              <pre className="font-mono text-[10px] bg-background p-2 rounded text-foreground overflow-x-auto">
                {JSON.stringify(latest, null, 2)}
              </pre>
            </div>
          </div>
        ) : (
          <p>Waiting for risk stream data...</p>
        )}
      </div>
    </main>
  );
}
