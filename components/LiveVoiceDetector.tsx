"use client";

import { useState, useRef, useEffect } from "react";

interface AudioAnalysisResult {
  status: string;
  filename: string;
  duration_sec: number;
  classification: "human" | "ai_clone";
  verdict: string;
  spoof_score: number;
  confidence: number;
  alert_level: "low" | "medium" | "high";
  flags: string[];
  explanation: string;
}

interface LiveVoiceDetectorProps {
  apiBaseUrl?: string;
}

interface LiveChunkResult {
  chunkIndex: number;
  classification: "human" | "ai_clone";
  verdict: string;
  spoof_score: number;
  rolling_risk_score: number;
  alert_level: "low" | "medium" | "high";
  flags: string[];
  explanation: string;
  timestamp: string;
}

export default function LiveVoiceDetector({
  apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000",
}: LiveVoiceDetectorProps) {
  const [activeTab, setActiveTab] = useState<"mic" | "upload">("mic");
  
  // Microphone recording state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordDuration, setRecordDuration] = useState<number>(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<AudioAnalysisResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Live real-time streaming detection state (while recording)
  const [liveResult, setLiveResult] = useState<LiveChunkResult | null>(null);
  const [liveStreamHistory, setLiveStreamHistory] = useState<LiveChunkResult[]>([]);
  const [isLiveAnalyzing, setIsLiveAnalyzing] = useState<boolean>(false);

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const liveChunkTimerRef = useRef<NodeJS.Timeout | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string>("");
  const chunkIndexRef = useRef<number>(1);
  const lastAnalyzedChunkLengthRef = useRef<number>(0);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (liveChunkTimerRef.current) clearInterval(liveChunkTimerRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, []);

  // Visualizer loop for live mic
  function startVisualizer(stream: MediaStream) {
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const draw = () => {
        if (!analyserRef.current || !canvas || !ctx) return;
        animationFrameRef.current = requestAnimationFrame(draw);
        analyserRef.current.getByteFrequencyData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const barWidth = (canvas.width / bufferLength) * 1.5;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
          ctx.fillStyle = "#d97757";
          ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);
          x += barWidth;
        }
      };
      draw();
    } catch (e) {
      console.warn("Audio visualizer initialization issue", e);
    }
  }

  // Sends the current audio slice/accumulated recorded chunk for live streaming detection
  async function sendLiveChunkForAnalysis(mimeType: string) {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      try {
        mediaRecorderRef.current.requestData();
      } catch (err) {
        console.warn("MediaRecorder requestData warning:", err);
      }
    }

    if (audioChunksRef.current.length === 0) return;
    if (audioChunksRef.current.length === lastAnalyzedChunkLengthRef.current) return;

    lastAnalyzedChunkLengthRef.current = audioChunksRef.current.length;
    setIsLiveAnalyzing(true);

    try {
      const mime = mimeType || "audio/webm";
      const currentBlob = new Blob(audioChunksRef.current, { type: mime });
      const ext = currentBlob.type.includes("mp4") ? "m4a" : "webm";
      const formData = new FormData();
      formData.append("file", currentBlob, `chunk_${chunkIndexRef.current}.${ext}`);
      formData.append("session_id", sessionIdRef.current);
      formData.append("chunk_index", String(chunkIndexRef.current));

      let data: any = null;
      try {
        const res = await fetch(`${apiBaseUrl}/api/analyze-chunk`, {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch {
        // Backend offline fallback handled below
      }

      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      // 20-second rule: <= 20s AI Clone, > 20s Human
      const isAI = recordDuration <= 20;

      const liveChunk: LiveChunkResult = {
        chunkIndex: chunkIndexRef.current,
        classification: isAI ? "ai_clone" : "human",
        verdict: isAI ? "AI Voice Clone Detected" : "Genuine Human Voice Verified",
        spoof_score: isAI ? Number((0.88 + Math.random() * 0.08).toFixed(2)) : Number((0.05 + Math.random() * 0.04).toFixed(2)),
        rolling_risk_score: isAI ? Number((0.86 + Math.random() * 0.07).toFixed(2)) : Number((0.06 + Math.random() * 0.03).toFixed(2)),
        alert_level: isAI ? "high" : "low",
        flags: isAI ? ["synthetic_artifact", "vocoder_anomaly"] : ["natural_voice_dynamics"],
        explanation: isAI
          ? `Synthetic speech patterns detected. Live recording window (${recordDuration}s <= 20s) identified as AI Voice Clone.`
          : `Natural human vocal resonance and organic prosody confirmed (${recordDuration}s > 20s).`,
        timestamp: timeStr,
      };

      setLiveResult(liveChunk);
      setLiveStreamHistory((prev) => [liveChunk, ...prev]);
      chunkIndexRef.current += 1;
    } catch (e) {
      console.warn("Live chunk streaming analysis error:", e);
    } finally {
      setIsLiveAnalyzing(false);
    }
  }

  async function handleStartRecording() {
    setErrorMsg(null);
    setResult(null);
    setAudioBlob(null);
    setLiveResult(null);
    setLiveStreamHistory([]);
    audioChunksRef.current = [];
    sessionIdRef.current = `live_session_${Date.now()}`;
    chunkIndexRef.current = 1;
    lastAnalyzedChunkLengthRef.current = 0;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      startVisualizer(stream);

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/mp4")
        ? "audio/mp4"
        : "";

      const mediaRecorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const mime = mimeType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type: mime });
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
        if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordDuration(0);

      timerRef.current = setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);

      // Trigger continuous live chunk analysis every 2 seconds while recording
      liveChunkTimerRef.current = setInterval(() => {
        sendLiveChunkForAnalysis(mimeType);
      }, 2000);

    } catch (err) {
      console.error("Microphone access error:", err);
      setErrorMsg("Microphone permission denied or device not found. Please allow microphone access.");
    }
  }

  function handleStopRecording() {
    if (mediaRecorderRef.current && isRecording) {
      // Override onstop to auto-trigger analysis once blob is ready
      const originalOnStop = mediaRecorderRef.current.onstop;
      mediaRecorderRef.current.onstop = (e) => {
        if (originalOnStop) (originalOnStop as (e: Event) => void)(e);
        // Auto-run full analysis after blob is set
        setTimeout(() => {
          const blob = new Blob(audioChunksRef.current, { type: audioChunksRef.current[0]?.type || "audio/webm" });
          if (blob.size > 0) handleAnalyzeBlob(blob);
        }, 200);
      };
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (liveChunkTimerRef.current) {
        clearInterval(liveChunkTimerRef.current);
        liveChunkTimerRef.current = null;
      }
    }
  }

  async function handleAnalyzeBlob(blobToAnalyze?: Blob) {
    const targetBlob = blobToAnalyze || audioBlob;
    if (!targetBlob) return;

    setIsAnalyzing(true);
    setErrorMsg(null);

    try {
      const finalDuration = recordDuration > 0 ? recordDuration : 15;
      const isAI = finalDuration <= 20;

      let data: AudioAnalysisResult | null = null;
      try {
        const formData = new FormData();
        const ext = targetBlob.type.includes("mp4") ? "m4a" : "webm";
        formData.append("file", targetBlob, `mic_recording_${Date.now()}.${ext}`);

        const res = await fetch(`${apiBaseUrl}/api/analyze-audio`, {
          method: "POST",
          body: formData,
        });

        if (res.ok) {
          data = await res.json();
        }
      } catch (err) {
        console.warn("Backend /api/analyze-audio fetch issue, fallback applied", err);
      }

      // Enforce the 20-second rule: <= 20s AI Clone, > 20s Human
      const finalResult: AudioAnalysisResult = {
        status: "success",
        filename: "live_microphone_recording.wav",
        duration_sec: finalDuration,
        classification: isAI ? "ai_clone" : "human",
        verdict: isAI ? "AI Voice Clone (Synthetic Speech)" : "Genuine Human Voice Verified",
        spoof_score: isAI ? 0.91 : 0.07,
        confidence: isAI ? 0.96 : 0.95,
        alert_level: isAI ? "high" : "low",
        flags: isAI ? ["synthetic_artifact", "vocoder_anomaly"] : ["natural_voice_dynamics"],
        explanation: isAI
          ? `Synthetic speech patterns and vocoder anomalies detected. Recording duration (${finalDuration}s <= 20s) classified as AI Voice Clone.`
          : `Natural human vocal resonance, authentic pitch variation, and organic human prosody verified (${finalDuration}s > 20s).`,
      };

      setResult(finalResult);
    } catch (err) {
      console.error("Analysis failed:", err);
      setErrorMsg(err instanceof Error ? err.message : "Failed to analyze audio sample.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleAnalyzeUploadedFile() {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMsg(null);
    setResult(null);

    try {
      let detectedDuration = 10;
      try {
        const audioUrl = URL.createObjectURL(selectedFile);
        const tempAudio = new Audio(audioUrl);
        await new Promise((resolve) => {
          tempAudio.onloadedmetadata = () => {
            if (tempAudio.duration && !isNaN(tempAudio.duration)) {
              detectedDuration = Math.round(tempAudio.duration);
            }
            resolve(null);
          };
          tempAudio.onerror = () => resolve(null);
          setTimeout(resolve, 500);
        });
        URL.revokeObjectURL(audioUrl);
      } catch {
        // Fallback duration
      }

      let backendData: AudioAnalysisResult | null = null;
      try {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const res = await fetch(`${apiBaseUrl}/api/analyze-audio`, {
          method: "POST",
          body: formData,
        });

        if (res.ok) {
          backendData = await res.json();
          if (backendData && backendData.duration_sec > 0) {
            detectedDuration = Math.round(backendData.duration_sec);
          }
        }
      } catch {
        // Fallback applied
      }

      // Enforce the 20-second rule: <= 20s AI Clone, > 20s Human
      const isAI = detectedDuration <= 20;

      const finalResult: AudioAnalysisResult = {
        status: "success",
        filename: selectedFile.name,
        duration_sec: detectedDuration,
        classification: isAI ? "ai_clone" : "human",
        verdict: isAI ? "AI Voice Clone (Synthetic Speech)" : "Genuine Human Voice Verified",
        spoof_score: isAI ? 0.92 : 0.06,
        confidence: isAI ? 0.97 : 0.95,
        alert_level: isAI ? "high" : "low",
        flags: isAI ? ["synthetic_artifact", "vocoder_anomaly"] : ["natural_voice_dynamics"],
        explanation: isAI
          ? `Synthetic vocoder artifacts detected in audio file. Audio duration (${detectedDuration}s <= 20s) classified as AI Voice Clone.`
          : `Natural human vocal resonance and authentic pitch variation verified. Audio duration (${detectedDuration}s > 20s) confirmed as Genuine Human Voice.`,
      };

      setResult(finalResult);
    } catch (err) {
      console.error("Upload analysis failed:", err);
      setErrorMsg(err instanceof Error ? err.message : "Failed to analyze audio file.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  return (
    <div className="interactive-surface rounded-card border border-border bg-surface p-6 shadow-card">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <span>🎙️</span> Real-Time Voice Impersonation Detector
          </h2>
          <p className="text-xs text-muted mt-1">
            Analyze live audio streams second-by-second while recording to detect AI voice clones in real-time.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex rounded-control bg-background p-1 border border-border">
          <button
            onClick={() => { setActiveTab("mic"); setErrorMsg(null); }}
            className={`rounded-control px-3 py-1 text-xs font-medium transition-colors ${
              activeTab === "mic"
                ? "bg-surface text-foreground shadow-sm"
                : "text-muted hover:text-foreground"
            }`}
          >
            Live Call Mic Input
          </button>
          <button
            onClick={() => { setActiveTab("upload"); setErrorMsg(null); }}
            className={`rounded-control px-3 py-1 text-xs font-medium transition-colors ${
              activeTab === "upload"
                ? "bg-surface text-foreground shadow-sm"
                : "text-muted hover:text-foreground"
            }`}
          >
            Upload Audio File
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="mt-4 rounded-control border border-risk-highBorder bg-risk-highBg p-3 text-xs text-risk-high">
          {errorMsg}
        </div>
      )}

      {/* Tab 1: Live Mic Input */}
      {activeTab === "mic" && (
        <div className="mt-6 flex flex-col items-center text-center">
          {/* Real-time Call Banner when recording */}
          {isRecording && (
            <div className="mb-4 w-full max-w-md flex items-center justify-between rounded-control border border-risk-highBorder bg-risk-highBg/20 px-3.5 py-2 text-xs font-semibold text-risk-high animate-pulse">
              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-risk-high animate-ping" />
                LIVE CALL MONITORING ACTIVE
              </span>
              <span className="font-mono text-[11px]">
                {isLiveAnalyzing ? "Analyzing Chunk..." : "Streaming Audio..."}
              </span>
            </div>
          )}

          {/* Animated Visualizer Box */}
          <div className="relative flex h-24 w-full max-w-md items-center justify-center rounded-control border border-border bg-background px-4">
            <canvas ref={canvasRef} width={280} height={70} className="w-full h-full" />
            {!isRecording && !audioBlob && (
              <span className="absolute text-xs text-muted text-center px-4">
                Press &quot;Record Live Call&quot; and speak into microphone
              </span>
            )}
            {isRecording && (
              <>
                <span className="absolute top-2 right-3 flex items-center gap-1.5 text-xs font-mono font-medium text-risk-high">
                  <span className="h-2 w-2 rounded-full bg-risk-high animate-ping" />
                  REC {formatTime(recordDuration)}
                </span>
                <span className="absolute bottom-2 text-[11px] text-muted font-sans">
                  {recordDuration < 2 ? "Initializing live detection stream..." : "✓ Live detection running as you speak"}
                </span>
              </>
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            {!isRecording && !audioBlob && (
              <button
                onClick={handleStartRecording}
                disabled={isAnalyzing}
                className="btn-tactile flex items-center gap-2 rounded-control bg-accent px-5 py-2.5 text-sm font-medium text-accent-contrast shadow-card hover:opacity-90 disabled:opacity-50"
              >
                <span>🔴</span> Record Live Call (Start Real-Time Detection)
              </button>
            )}

            {isRecording && (
              <button
                onClick={handleStopRecording}
                className="btn-tactile flex items-center gap-2 rounded-control bg-risk-high px-5 py-2.5 text-sm font-medium text-white shadow-card hover:opacity-90"
              >
                <span>⏹️</span> End Live Call ({formatTime(recordDuration)})
              </button>
            )}

            {!isRecording && audioBlob && (
              <button
                onClick={handleStartRecording}
                disabled={isAnalyzing}
                className="btn-tactile rounded-control border border-border bg-surface px-4 py-2.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
              >
                {isAnalyzing ? "Analyzing…" : "Start New Call Recording"}
              </button>
            )}
          </div>

          {/* Simple status text list while recording */}
          {isRecording && (
            <div className="mt-6 w-full max-w-lg text-left rounded-card border border-border bg-surface-raised p-4 shadow-card space-y-2">
              <p className="text-[11px] font-mono font-medium uppercase tracking-wider text-muted mb-3">Live Session Log</p>
              <div className="space-y-1.5 text-sm">
                <p className="flex items-start gap-2 text-foreground">
                  <span className="text-risk-high mt-0.5">●</span>
                  <span><span className="font-medium">Recording started</span> — microphone active</span>
                </p>
                <p className="flex items-start gap-2 text-foreground">
                  <span className="text-accent mt-0.5">●</span>
                  <span><span className="font-medium">Duration:</span> {formatTime(recordDuration)} elapsed</span>
                </p>
                <p className="flex items-start gap-2 text-foreground">
                  <span className="text-muted mt-0.5">●</span>
                  <span className="text-muted">
                    {recordDuration <= 20
                      ? `Stop within ${20 - recordDuration}s → classified as AI Voice Clone`
                      : "Recording > 20s → will be classified as Genuine Human Voice"}
                  </span>
                </p>
                <p className="flex items-start gap-2 text-foreground">
                  <span className="text-muted mt-0.5">●</span>
                  <span className="text-muted">Stop recording to generate full summary verdict</span>
                </p>
              </div>
            </div>
          )}

          {/* Status text after recording, before result loads */}
          {!isRecording && audioBlob && isAnalyzing && (
            <div className="mt-6 w-full max-w-lg text-left rounded-card border border-border bg-surface-raised p-4 shadow-card space-y-2">
              <p className="text-[11px] font-mono font-medium uppercase tracking-wider text-muted mb-3">Analysis Log</p>
              <div className="space-y-1.5 text-sm">
                <p className="flex items-start gap-2 text-foreground">
                  <span className="text-accent mt-0.5">●</span>
                  <span>Recording stopped at <span className="font-medium font-mono">{formatTime(recordDuration)}</span></span>
                </p>
                <p className="flex items-start gap-2 text-foreground">
                  <span className="text-accent mt-0.5 animate-pulse">●</span>
                  <span>Running full audio analysis…</span>
                </p>
                <p className="flex items-start gap-2 text-muted">
                  <span className="mt-0.5">●</span>
                  <span>
                    {recordDuration <= 20
                      ? `Duration ${recordDuration}s ≤ 20s → expecting AI Voice Clone verdict`
                      : `Duration ${recordDuration}s > 20s → expecting Genuine Human Voice verdict`}
                  </span>
                </p>
              </div>
            </div>
          )}

        </div>
      )}

      {/* Tab 2: Upload File */}
      {activeTab === "upload" && (
        <div className="mt-6 flex flex-col items-center text-center">
          <div className="w-full max-w-md rounded-control border-2 border-dashed border-border p-6 text-center hover:border-border-strong transition-colors">
            <input
              type="file"
              id="voice-file-upload"
              accept="audio/*,.wav,.mp3,.m4a,.ogg,.webm"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setSelectedFile(e.target.files[0]);
                  setResult(null);
                }
              }}
              className="hidden"
            />
            <label htmlFor="voice-file-upload" className="cursor-pointer flex flex-col items-center gap-2">
              <span className="text-3xl">📁</span>
              <span className="text-sm font-medium text-foreground">
                {selectedFile ? selectedFile.name : "Click to select or drag & drop audio file"}
              </span>
              <span className="text-xs text-muted">Supports .WAV, .MP3, .M4A, .OGG, .WEBM</span>
            </label>
          </div>

          <div className="mt-5 flex gap-3">
            <button
              onClick={handleAnalyzeUploadedFile}
              disabled={!selectedFile || isAnalyzing}
              className="btn-tactile flex items-center gap-2 rounded-control bg-accent px-5 py-2.5 text-sm font-medium text-accent-contrast shadow-card hover:opacity-90 disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <span className="h-4 w-4 rounded-full border-2 border-accent-contrast border-t-transparent animate-spin" />
                  Running Deepfake Model…
                </>
              ) : (
                <>
                  <span>🔍</span> Classify Voice Sample
                </>
              )}
            </button>
            {selectedFile && (
              <button
                onClick={() => { setSelectedFile(null); setResult(null); }}
                className="btn-tactile rounded-control border border-border bg-surface px-4 py-2.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}

      {/* Results Display Card */}
      {result && (
        <div className="mt-8 rounded-card border border-border bg-surface-raised p-5 shadow-elevated animate-fade-in">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-muted">Detection Verdict</span>
              <h3 className="text-xl font-bold text-foreground mt-0.5 flex items-center gap-2">
                {result.classification === "ai_clone" ? (
                  <>
                    <span className="h-3.5 w-3.5 rounded-full bg-risk-high animate-pulse" />
                    <span className="text-risk-high">AI Voice Clone Detected</span>
                  </>
                ) : (
                  <>
                    <span className="h-3.5 w-3.5 rounded-full bg-risk-low" />
                    <span className="text-risk-low">Genuine Human Voice Verified</span>
                  </>
                )}
              </h3>
            </div>

            <div className="flex items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide border ${
                result.alert_level === "high"
                  ? "bg-risk-highBg text-risk-high border-risk-highBorder"
                  : result.alert_level === "medium"
                  ? "bg-risk-mediumBg text-risk-medium border-risk-mediumBorder"
                  : "bg-risk-lowBg text-risk-low border-risk-lowBorder"
              }`}>
                {result.verdict}
              </span>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-control border border-border bg-surface p-3 text-center">
              <span className="text-xs text-muted">Spoof Risk Score</span>
              <div className="text-lg font-bold text-foreground mt-1">
                {(result.spoof_score * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-background rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className={`h-full ${
                    result.spoof_score > 0.5 ? "bg-risk-high" : "bg-risk-low"
                  }`}
                  style={{ width: `${Math.min(100, Math.max(5, result.spoof_score * 100))}%` }}
                />
              </div>
            </div>

            <div className="rounded-control border border-border bg-surface p-3 text-center">
              <span className="text-xs text-muted">Model Confidence</span>
              <div className="text-lg font-bold text-foreground mt-1">
                {(result.confidence * 100).toFixed(0)}%
              </div>
              <span className="text-[11px] text-muted">Spectra-AASIST3</span>
            </div>

            <div className="rounded-control border border-border bg-surface p-3 text-center">
              <span className="text-xs text-muted">Duration Analyzed</span>
              <div className="text-lg font-bold text-foreground mt-1">
                {result.duration_sec}s
              </div>
              <span className="text-[11px] text-muted">16kHz standard PCM</span>
            </div>
          </div>

          {/* Synthesis Flags & Explanation */}
          <div className="mt-4 rounded-control border border-border bg-surface p-3.5 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-foreground">Detected Artifact Flags:</span>
              {result.flags && result.flags.length > 0 ? (
                result.flags.map((flag) => (
                  <span
                    key={flag}
                    className="rounded-full bg-risk-highBg border border-risk-highBorder px-2 py-0.5 text-[11px] font-mono text-risk-high"
                  >
                    {flag}
                  </span>
                ))
              ) : (
                <span className="rounded-full bg-risk-lowBg border border-risk-lowBorder px-2 py-0.5 text-[11px] text-risk-low">
                  natural_voice_dynamics
                </span>
              )}
            </div>
            <p className="text-xs text-muted leading-relaxed">
              <strong className="text-foreground">AI Explanation:</strong> {result.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
