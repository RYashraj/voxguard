"use client";

import { useRef, useState } from "react";
import RiskGauge from "@/components/RiskGauge";
import AlertBanner from "@/components/AlertBanner";
import LiveWaveform from "@/components/LiveWaveform";
import CallContextInput from "@/components/CallContextInput";
import AdvisoryPanel from "@/components/AdvisoryPanel";
import ThemeToggle from "@/components/ThemeToggle";
import Logo from "@/components/Logo";
import AmbientBackground from "@/components/AmbientBackground";
import BootIntro from "@/components/BootIntro";
import RiskTimeline from "@/components/RiskTimeline";
import ResponsePlan from "@/components/ResponsePlan";
import IdentityCloneLab from "@/components/IdentityCloneLab";
import { useRiskSocket } from "@/hooks/useRiskSocket";
import { RiskUpdate, SimulationContext } from "@/types/risk";

const WS_URL = process.env.NEXT_PUBLIC_RISK_WS_URL ?? "ws://127.0.0.1:8000/ws/session";
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const LIVE_WS_URL = WS_URL.replace("/ws/session", "/ws/live");

const STATUS_LABEL: Record<string, string> = {
  connecting: "connecting…",
  open: "live",
  closed: "reconnecting…",
};

export default function Home() {
  const { latest: demoLatest, history: demoHistory, status, clearHistory } = useRiskSocket(WS_URL);

  const [simStatus, setSimStatus] = useState<
    "idle" | "starting" | "running" | "error"
  >("idle");

  const [sampleType, setSampleType] = useState<string>("gradual_escalation");
  const [inputMode, setInputMode] = useState<"demo" | "microphone">("demo");
  const [micStatus, setMicStatus] = useState<"idle" | "requesting" | "live" | "error">("idle");
  const [micLatest, setMicLatest] = useState<RiskUpdate | null>(null);
  const [micHistory, setMicHistory] = useState<RiskUpdate[]>([]);
  const micSocketRef = useRef<WebSocket | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const micContextRef = useRef<AudioContext | null>(null);
  const micProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const micSamplesRef = useRef<Float32Array>(new Float32Array(0));
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [audioTime, setAudioTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [audioPlaying, setAudioPlaying] = useState(false);

  const [simContext, setSimContext] = useState<SimulationContext>({
    caller_context: "unknown_contact",
    transaction_type: "otp_or_pin_request",
    user_confirmation_required: true,
  });

  function handleSampleChange(nextSample: string) {
    setSampleType(nextSample);
    if (nextSample === "otp_scam") {
      setSimContext((current) => ({
        ...current,
        caller_context: "unknown_contact",
        transaction_type: "otp_or_pin_request",
      }));
    }
  }

  function audioSampleName() {
    if (sampleType === "otp_scam") return "otp";
    if (sampleType === "deepfake") return "deepfake";
    if (sampleType === "genuine") return "genuine";
    return "gradual";
  }

  function audioLabel() {
    if (sampleType === "otp_scam") return "Genuine demo audio · OTP context warning";
    if (sampleType === "deepfake") return "ASVspoof synthetic benchmark sample";
    if (sampleType === "genuine") return "Baseline audio sample · human reference needed for identity proof";
    return "Gradual escalation demo audio";
  }

  function encodeWav(samples: Float32Array, sampleRate: number) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    const writeText = (offset: number, value: string) => [...value].forEach((char, index) => view.setUint8(offset + index, char.charCodeAt(0)));
    writeText(0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeText(8, "WAVE");
    writeText(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeText(36, "data");
    view.setUint32(40, samples.length * 2, true);
    samples.forEach((sample, index) => {
      const clamped = Math.max(-1, Math.min(1, sample));
      view.setInt16(44 + index * 2, clamped < 0 ? clamped * 32768 : clamped * 32767, true);
    });
    return buffer;
  }

  function stopMicrophone() {
    micProcessorRef.current?.disconnect();
    micSocketRef.current?.close();
    micStreamRef.current?.getTracks().forEach((track) => track.stop());
    micContextRef.current?.close();
    micProcessorRef.current = null;
    micSocketRef.current = null;
    micStreamRef.current = null;
    micContextRef.current = null;
    micSamplesRef.current = new Float32Array(0);
    setMicStatus("idle");
    setSimStatus("idle");
  }

  async function startMicrophone() {
    setMicStatus("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const socket = new WebSocket(LIVE_WS_URL);
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      micStreamRef.current = stream;
      micSocketRef.current = socket;
      micContextRef.current = audioContext;
      micProcessorRef.current = processor;
      socket.onopen = () => {
        socket.send(JSON.stringify({ type: "context", context: simContext }));
        setMicStatus("live");
        setSimStatus("running");
      };
      socket.onmessage = (event) => {
        const parsed = JSON.parse(event.data) as Partial<RiskUpdate> & { advisory?: RiskUpdate["advisory"] };
        if (!parsed.chunk_id || typeof parsed.rolling_risk_score !== "number" || !parsed.alert_level) return;
        const update = parsed as RiskUpdate;
        setMicLatest(update);
        setMicHistory((previous) => [...previous, update].slice(-12));
      };
      socket.onerror = () => setMicStatus("error");
      processor.onaudioprocess = (event) => {
        if (socket.readyState !== WebSocket.OPEN) return;
        const incoming = event.inputBuffer.getChannelData(0);
        const combined = new Float32Array(micSamplesRef.current.length + incoming.length);
        combined.set(micSamplesRef.current);
        combined.set(incoming, micSamplesRef.current.length);
        const chunkSize = Math.floor(audioContext.sampleRate * 3);
        if (combined.length >= chunkSize) {
          socket.send(encodeWav(combined.slice(0, chunkSize), audioContext.sampleRate));
          micSamplesRef.current = combined.slice(chunkSize);
        } else {
          micSamplesRef.current = combined;
        }
      };
      source.connect(processor);
      processor.connect(audioContext.destination);
    } catch (error) {
      console.error("Microphone unavailable", error);
      setMicStatus("error");
      setSimStatus("error");
    }
  }

  async function handleStartCall() {
    if (inputMode === "microphone") {
      await startMicrophone();
      return;
    }
    setSimStatus("starting");
    try {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        await audioRef.current.play();
        setAudioPlaying(true);
      }
      const payload: {
        context?: SimulationContext;
        file_path?: string;
        scenario?: string;
      } = { context: simContext };

      if (sampleType === "deepfake") {
        payload.file_path = "data/test_audio/asvspoof_spoof_clips/LA_E_5932896.wav";
        payload.scenario = "suspicious";
      } else if (sampleType === "otp_scam") {
        payload.file_path = "data/sample_calls/demo_call.wav";
        payload.scenario = "clean";
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
    if (inputMode === "microphone") {
      stopMicrophone();
      return;
    }
    audioRef.current?.pause();
    setAudioPlaying(false);
    try {
      await fetch(`${API_BASE_URL}/stop-simulation`, { method: "POST" });
      setSimStatus("idle");
    } catch (err) {
      console.error("Failed to stop simulation", err);
    }
  }

  function clearCall() {
    if (micStatus !== "idle") stopMicrophone();
    void fetch(`${API_BASE_URL}/stop-simulation`, { method: "POST" }).catch(() => undefined);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setAudioTime(0);
    setAudioPlaying(false);
    clearHistory();
    setMicLatest(null);
    setMicHistory([]);
    setSimStatus("idle");
  }

  const latest = inputMode === "microphone" ? micLatest : demoLatest;
  const history = inputMode === "microphone" ? micHistory : demoHistory;
  const hasReceivedData = latest !== null;
  const activeStatus = inputMode === "microphone" ? micStatus : status;

  async function toggleDemoPlayback() {
    if (!audioRef.current || inputMode !== "demo") return;
    if (audioPlaying) {
      audioRef.current.pause();
      await handleStopCall();
      setAudioPlaying(false);
      return;
    }
    await handleStartCall();
  }

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
              Call risk monitor
            </h1>
            <p className="mt-1.5 max-w-md text-sm leading-relaxed text-muted">
              Live voice-impersonation risk score for the active call.
            </p>
          </div>
          <ThemeToggle />
        </header>

        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
          {/* Main column */}
          <div className="flex min-w-0 flex-col gap-6">
            <LiveWaveform active={hasReceivedData} />

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-border bg-surface px-5 py-4 shadow-card">
              <div>
                <p className="text-base font-semibold text-foreground">Input source: {inputMode === "microphone" ? "Live microphone" : "Demo audio file"}</p>
                <p className="mt-1 text-sm text-muted">{inputMode === "microphone" ? "Browser microphone, analyzed in 3-second PCM chunks" : "Bundled ASVspoof/sample WAV, streamed as a live-call simulation"}</p>
              </div>
              <span className="rounded-full border border-border px-3 py-1 text-sm font-medium text-muted">{activeStatus === "live" || activeStatus === "open" ? "Ready" : activeStatus}</span>
            </div>

            <RiskGauge
              score={latest?.rolling_risk_score ?? 0}
              confidence={latest?.confidence ?? 0}
              alertLevel={latest?.alert_level ?? "low"}
            />

            <RiskTimeline history={history} />

            <AlertBanner
              alertLevel={latest?.alert_level ?? "low"}
              flags={latest?.flags ?? []}
            />

            <AdvisoryPanel
              advisory={latest?.advisory}
              onStopCall={handleStopCall}
            />
            <ResponsePlan advisory={latest?.advisory} />
            <IdentityCloneLab />
          </div>

          {/* Side column: simulator controls + session detail */}
          <div className="flex min-w-0 flex-col gap-6">
            <div className="interactive-surface rounded-card border border-border bg-surface p-5 shadow-card space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-base font-semibold text-foreground" htmlFor="sample-selector">
                  Call input
                </label>
                <span className="text-sm text-muted">Choose one</span>
              </div>
              <div className="grid grid-cols-2 gap-2 rounded-control bg-background p-1">
                <button type="button" onClick={() => { setInputMode("demo"); stopMicrophone(); }} className={`rounded-control px-3 py-2 text-sm font-medium ${inputMode === "demo" ? "bg-surface text-foreground shadow-card" : "text-muted"}`}>Demo file</button>
                <button type="button" onClick={() => setInputMode("microphone")} className={`rounded-control px-3 py-2 text-sm font-medium ${inputMode === "microphone" ? "bg-surface text-foreground shadow-card" : "text-muted"}`}>Live microphone</button>
              </div>
              {inputMode === "demo" && (
              <>
              <select
                id="sample-selector"
                value={sampleType}
                onChange={(e) => handleSampleChange(e.target.value)}
                disabled={simStatus === "starting" || simStatus === "running"}
                className="w-full rounded-control border border-border bg-background px-3 py-3 text-base text-foreground transition-colors hover:border-border-strong focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent disabled:opacity-50"
              >
                <option value="otp_scam">OTP scam preset (unknown caller + synthetic voice)</option>
                <option value="gradual_escalation">Demo script (gradual escalation: low → high)</option>
                <option value="deepfake">ASVspoof synthetic deepfake (high risk &gt;90%)</option>
                <option value="genuine">Baseline audio sample (identity reference required)</option>
              </select>
              <div className="rounded-control border border-border bg-background p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="min-w-0 truncate text-sm font-medium text-foreground">{audioLabel()}</span>
                  <span className="shrink-0 font-mono text-xs text-muted">{Math.floor(audioTime)}s / {Math.floor(audioDuration || 0)}s</span>
                </div>
                <audio
                  ref={audioRef}
                  className="hidden"
                  preload="metadata"
                  src={`${API_BASE_URL}/audio/${audioSampleName()}`}
                  onLoadedMetadata={(event) => setAudioDuration(event.currentTarget.duration)}
                  onTimeUpdate={(event) => setAudioTime(event.currentTarget.currentTime)}
                  onPlay={() => setAudioPlaying(true)}
                  onPause={() => setAudioPlaying(false)}
                  onEnded={() => { setAudioPlaying(false); void handleStopCall(); }}
                />
                <button type="button" onClick={toggleDemoPlayback} className="mt-3 w-full rounded-control bg-accent px-4 py-3 text-base font-semibold text-accent-contrast">
                  {audioPlaying ? "Pause audio and analysis" : "Play audio and start analysis"}
                </button>
                <p className="mt-2 text-sm leading-relaxed text-muted">Seeking is disabled so audio and risk chunks stay synchronized. Pause stops both.</p>
              </div>
              </>
              )}
              {inputMode === "microphone" && <p className="rounded-control border border-border bg-background p-3 text-sm leading-relaxed text-muted">Your browser will ask for microphone permission. Audio is chunked locally and sent to the live analysis endpoint; no recording is saved by the dashboard.</p>}

              {(inputMode === "microphone" || status === "open") && (
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
              <button type="button" onClick={clearCall} className="w-full rounded-control border border-border bg-background px-4 py-3 text-base font-medium text-muted transition-colors hover:border-border-strong hover:text-foreground">Clear call and reset graph</button>
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
      </main>
    </div>
  );
}
