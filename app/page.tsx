"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useSession, signIn, signOut } from "next-auth/react";
import RiskGauge from "@/components/RiskGauge";
import AlertBanner from "@/components/AlertBanner";
import LiveWaveform from "@/components/LiveWaveform";
import LiveTranscript from "@/components/LiveTranscript";
import RiskTrend from "@/components/RiskTrend";
import ChunkLog from "@/components/ChunkLog";
import PreTransactionModal from "@/components/PreTransactionModal";
import AlertToast from "@/components/AlertToast";
import IdentityBadge from "@/components/IdentityBadge";
import ThemeToggle from "@/components/ThemeToggle";
import { useRiskSocket } from "@/hooks/useRiskSocket";
import { useMicrophone } from "@/hooks/useMicrophone";
import { MOCK_PROSODY_DRIFT_ENABLED, getMockIdentityDrift } from "@/lib/mockSignals";

interface Contact {
  id: string;
  name: string;
  role: string;
}

const DEFAULT_MOCK_CONTACTS: Contact[] = [
  { id: "unknown", name: "Unknown Caller", role: "Unverified Contact" },
  { id: "rahul_sharma", name: "Rahul Sharma", role: "Regional Manager" },
  { id: "priya_patel", name: "Priya Patel", role: "Chief Financial Officer" },
  { id: "amit_kumar", name: "Amit Kumar", role: "Vendor Account Lead" },
  { id: "neha_singh", name: "Neha Singh", role: "HR Operations" },
];

// Day 5: pointed at Shreyas's real backend (falls back to the Day 3 mock
// server if the env vars aren't set, so local dev without the backend
// running still works).
const BASE_WS_URL = process.env.NEXT_PUBLIC_RISK_WS_URL ?? "ws://localhost:8080";
const WS_TOKEN = process.env.NEXT_PUBLIC_VOXGUARD_WS_TOKEN ?? "";
const WS_URL = WS_TOKEN ? `${BASE_WS_URL}?token=${WS_TOKEN}` : BASE_WS_URL;

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
  const { latest, history, status: socketStatus, warning, clear, clearWarning, sendBytes } = useRiskSocket(WS_URL);
  const hasReceivedData = latest !== null;

  const handleAudioChunk = useCallback((pcmBytes: Int16Array) => {
    sendBytes(pcmBytes.buffer as ArrayBuffer);
  }, [sendBytes]);

  const { start: startMic, stop: stopMic } = useMicrophone(handleAudioChunk);

  const [simStatus, setSimStatus] = useState<
    "idle" | "starting" | "running" | "error"
  >("idle");

  const [contacts, setContacts] = useState<Contact[]>(DEFAULT_MOCK_CONTACTS);
  const [selectedCaller, setSelectedCaller] = useState<string>("unknown");
  const [selectedContext, setSelectedContext] = useState<string>("routine");
  const [selectedScenario, setSelectedScenario] = useState<string>("gradual_escalation");
  const audioRef = useRef<HTMLAudioElement>(null);

  const [showModalOverride, setShowModalOverride] = useState(false);
  const [modalHandled, setModalHandled] = useState(false);

  useEffect(() => {
    if (
      (warning !== null ||
        (latest?.alert_level === "high" && selectedContext !== "routine")) &&
      !modalHandled
    ) {
      setShowModalOverride(true);
    }
  }, [latest, warning, selectedContext, modalHandled]);

  useEffect(() => {
    async function fetchContacts() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/contacts`);
        if (res.ok) {
          const data = await res.json();
          // Real backend responds with { total_contacts, contacts: Contact[] }
          // (ContactsResponse), not a bare array.
          const list: Contact[] = Array.isArray(data?.contacts) ? data.contacts : [];
          if (list.length > 0) {
            const hasUnknown = list.some((c) => c.id === "unknown");
            setContacts(
              hasUnknown
                ? list
                : [{ id: "unknown", name: "Unknown Caller", role: "Unverified Contact" }, ...list]
            );
          }
        }
      } catch (err) {
        console.warn("Failed to fetch contacts from API, using fallback mock list", err);
      }
    }
    fetchContacts();
  }, []);

  async function handleStartCall() {
    setSimStatus("starting");
    setModalHandled(false);
    setShowModalOverride(false);
    try {
      if (selectedScenario === "live_mic") {
        // Live streaming from microphone
        await startMic();
      } else {
        // Fallback to simulator for predefined WAVs
        const startUrl = `${API_BASE_URL}/api/v1/session/start`;
        const res = await fetch(startUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            caller_id: selectedCaller,
            transaction_context: selectedContext,
            scenario: selectedScenario,
          }),
        });
        if (!res.ok) {
          const legacyRes = await fetch(`${API_BASE_URL}/start-simulation`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              caller_id: selectedCaller,
              transaction_context: selectedContext,
              scenario: selectedScenario,
            }),
          });
          if (!legacyRes.ok) throw new Error(`start-simulation failed: ${legacyRes.status}`);
        }

        if (audioRef.current) {
          audioRef.current.src = selectedScenario === "suspicious"
            ? "/audio/asvspoof_spoof_demo.wav"
            : "/audio/demo_call.wav";
          audioRef.current.currentTime = 0;
          audioRef.current.play().catch(e => console.error("Audio playback failed:", e));
        }
      }

      setSimStatus("running");
    } catch (err) {
      console.error("Failed to start call", err);
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
            <Link
              href="/transparency"
              className="border border-line px-4 py-2 font-mono text-sm text-muted hover:text-ink transition-colors"
            >
              Transparency 📊
            </Link>
            <Link
              href="/settings"
              className="border border-line px-4 py-2 font-mono text-sm text-muted hover:text-ink transition-colors"
            >
              Settings ⚙️
            </Link>
            <ThemeToggle />
            <button
              onClick={() => signOut()}
              className="border border-line px-4 py-2 font-mono text-sm text-muted hover:text-ink transition-colors"
            >
              Sign out
            </button>
          </div>
        </header>

        <div className="mt-6 flex flex-wrap items-end justify-between gap-4 border border-line bg-surface p-5">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-semibold text-ink md:text-3xl">
              Active call session
            </h1>
            <p className="text-sm text-muted">
              Configure session enrichment parameters before starting call.
            </p>
          </div>

          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="font-mono text-xs text-muted uppercase tracking-wider">
                Known Contact
              </label>
              <select
                value={selectedCaller}
                onChange={(e) => setSelectedCaller(e.target.value)}
                disabled={simStatus === "running" || simStatus === "starting"}
                className="border border-line bg-background px-3 py-2.5 font-mono text-sm text-ink outline-none transition-colors focus:border-ink disabled:opacity-50 min-w-[200px]"
              >
                {contacts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.role})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="font-mono text-xs text-muted uppercase tracking-wider">
                Transaction Context
              </label>
              <select
                value={selectedContext}
                onChange={(e) => setSelectedContext(e.target.value)}
                disabled={simStatus === "running" || simStatus === "starting"}
                className="border border-line bg-background px-3 py-2.5 font-mono text-sm text-ink outline-none transition-colors focus:border-ink disabled:opacity-50 min-w-[190px]"
              >
                <option value="routine">Routine</option>
                <option value="information_request">Information Request</option>
                <option value="fund_transfer">Fund Transfer</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="font-mono text-xs text-muted uppercase tracking-wider">
                Call Scenario
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                disabled={simStatus === "running" || simStatus === "starting"}
                className="border border-line bg-background px-3 py-2.5 font-mono text-sm text-ink outline-none transition-colors focus:border-ink disabled:opacity-50 min-w-[190px]"
              >
                <option value="live_mic">🎙️ Live Microphone</option>
                <option value="clean">🟢 Clean Call (Simulated)</option>
                <option value="gradual_escalation">🟡 Gradual Escalation (Simulated)</option>
                <option value="suspicious">🔴 Suspicious (Simulated)</option>
              </select>
            </div>

            {socketStatus === "open" && (
              <div className="flex gap-3 items-center">
                <button
                  onClick={handleStartCall}
                  disabled={simStatus === "starting" || simStatus === "running"}
                  className="border border-line bg-ink px-6 py-2.5 font-mono text-sm font-bold text-surface transition-opacity hover:opacity-90 disabled:opacity-50"
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
                        if (selectedScenario === "live_mic") {
                          stopMic();
                        } else {
                          await fetch(`${API_BASE_URL}/stop-simulation`, { method: "POST" });
                        }
                        setSimStatus("idle");
                        if (audioRef.current) {
                          audioRef.current.pause();
                          audioRef.current.currentTime = 0;
                        }
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    className="border border-risk-high text-risk-high hover:bg-risk-high hover:text-surface px-6 py-2.5 font-mono text-sm font-bold transition-colors"
                  >
                    Stop call
                  </button>
                )}
                
                {(hasReceivedData || history.length > 0) && simStatus === "idle" && (
                  <button
                    onClick={clear}
                    className="border border-line px-6 py-2.5 font-mono text-sm font-bold text-muted transition-colors hover:text-ink hover:border-ink"
                  >
                    Clear data
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {simStatus === "running" && (
          <div className="mt-3 flex flex-wrap gap-6 border border-line bg-surface/40 px-4 py-2.5 font-mono text-xs text-muted">
            <span>
              Active Caller:{" "}
              <strong className="text-ink font-semibold">
                {contacts.find((c) => c.id === selectedCaller)?.name || selectedCaller}
              </strong>
            </span>
            <span>
              Context:{" "}
              <strong className="text-ink font-semibold uppercase">
                {selectedContext.replace("_", " ")}
              </strong>
            </span>
          </div>
        )}

        <div className="mt-6 grid gap-5 lg:grid-cols-12">
          <section className="flex flex-col gap-5 lg:col-span-7">
            <RiskGauge
              score={latest?.rolling_risk_score ?? 0}
              confidence={latest?.confidence ?? 0}
              alertLevel={latest?.alert_level ?? "low"}
            />
            <LiveWaveform active={socketStatus === "open" && hasReceivedData} />
            <LiveTranscript active={socketStatus === "open" && selectedScenario === "live_mic" && simStatus === "running"} />
          </section>

          <section className="flex flex-col gap-5 lg:col-span-5">
            <IdentityBadge
              drift={
                latest
                  ? latest.identity_drift ??
                    (MOCK_PROSODY_DRIFT_ENABLED ? getMockIdentityDrift(latest.chunk_id) : 0)
                  : 0
              }
              active={hasReceivedData}
            />
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

      <AlertToast
        alertLevel={latest?.alert_level ?? "low"}
        chunkId={latest?.chunk_id}
        flags={latest?.flags ?? []}
      />

      <PreTransactionModal
        isOpen={showModalOverride || warning !== null}
        reason={warning?.reason}
        recommendedActions={warning?.recommended_actions}
        onActionSelect={() => {
          // User triggered secondary verification action
          setShowModalOverride(false);
          setModalHandled(true);
          clearWarning();
        }}
      />
      <audio ref={audioRef} className="hidden" />
    </main>
  );
}
