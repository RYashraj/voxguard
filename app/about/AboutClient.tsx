"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";
import AmbientBackground from "@/components/AmbientBackground";
import ThemeToggle from "@/components/ThemeToggle";

/* ------------------------------------------------------------------ *
 * Small scroll-reveal hook. Purely presentational: observes an
 * element's visibility and flips a boolean once. No app state, no
 * network calls, no effect on any other page.
 * ------------------------------------------------------------------ */
function useInView<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2, rootMargin: "0px 0px -40px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return { ref, inView };
}

function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ease-out ${
        inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-5"
      } ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Section shell
 * ------------------------------------------------------------------ */
function Section({
  id,
  eyebrow,
  title,
  description,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 sm:py-24">
      <Reveal className="mb-10 max-w-2xl sm:mb-14">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium uppercase tracking-wide text-accent shadow-card">
          {eyebrow}
        </span>
        <h2 className="mt-4 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          {title}
        </h2>
        {description && (
          <p className="mt-3 text-[15px] leading-relaxed text-muted">{description}</p>
        )}
      </Reveal>
      {children}
    </section>
  );
}

/* ------------------------------------------------------------------ *
 * Flash / flip cards for core capabilities
 * ------------------------------------------------------------------ */
interface FlashCardData {
  icon: ReactNode;
  title: string;
  front: string;
  back: string;
}

function FlashCard({ card, delay }: { card: FlashCardData; delay: number }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <Reveal delay={delay}>
      <button
        type="button"
        onClick={() => setFlipped((f) => !f)}
        aria-pressed={flipped}
        className="group block h-56 w-full text-left [perspective:1200px] focus:outline-none"
      >
        <div
          className="relative h-full w-full transition-transform duration-500 [transform-style:preserve-3d]"
          style={{ transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)" }}
        >
          {/* Front */}
          <div
            className="interactive-surface absolute inset-0 flex flex-col justify-between rounded-card border border-border bg-surface p-5 shadow-card group-hover:border-border-strong group-focus-visible:ring-2 group-focus-visible:ring-accent [backface-visibility:hidden]"
          >
            <div className="flex items-center justify-between">
              <span className="flex h-10 w-10 items-center justify-center rounded-control bg-accent-soft text-accent">
                {card.icon}
              </span>
              <span className="text-[10px] uppercase tracking-wide text-muted">
                Tap to expand
              </span>
            </div>
            <div>
              <h3 className="text-base font-semibold text-foreground">{card.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{card.front}</p>
            </div>
          </div>
          {/* Back */}
          <div
            className="absolute inset-0 flex flex-col justify-between rounded-card border border-accent bg-accent-soft p-5 shadow-card [backface-visibility:hidden]"
            style={{ transform: "rotateY(180deg)" }}
          >
            <span className="text-[10px] uppercase tracking-wide text-accent">
              How it works
            </span>
            <p className="text-sm leading-relaxed text-foreground">{card.back}</p>
            <span className="text-[10px] uppercase tracking-wide text-muted">
              Tap to flip back
            </span>
          </div>
        </div>
      </button>
    </Reveal>
  );
}

/* ------------------------------------------------------------------ *
 * Pipeline step (How it works)
 * ------------------------------------------------------------------ */
function PipelineStep({
  index,
  title,
  description,
  icon,
  last = false,
}: {
  index: number;
  title: string;
  description: string;
  icon: ReactNode;
  last?: boolean;
}) {
  return (
    <Reveal delay={index * 90} className="relative flex flex-1 flex-col items-center text-center">
      <div className="relative flex flex-col items-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-full border border-border bg-surface text-accent shadow-card">
          {icon}
        </span>
        {!last && (
          <span
            aria-hidden="true"
            className="absolute left-full top-1/2 hidden h-[2px] w-full -translate-y-1/2 overflow-hidden sm:block"
            style={{ width: "calc(100% + 2.5rem)" }}
          >
            <span className="block h-full w-full bg-gradient-to-r from-accent/50 via-accent/20 to-transparent" />
            <span className="absolute inset-y-0 left-0 h-full w-3 rounded-full bg-accent animate-[pulse-dot_2.4s_ease-in-out_infinite]" />
          </span>
        )}
      </div>
      <p className="mt-4 text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-1 max-w-[10.5rem] text-xs leading-relaxed text-muted">{description}</p>
    </Reveal>
  );
}

/* ------------------------------------------------------------------ *
 * Icons (inline, no external deps)
 * ------------------------------------------------------------------ */
const icons = {
  wave: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M2 12h2M6 8v8M10 5v14M14 3v18M18 8v8M22 12h-2" />
    </svg>
  ),
  brain: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 3a3 3 0 0 0-3 3v.3A3 3 0 0 0 4 9v1a3 3 0 0 0 1 2.2A3 3 0 0 0 4 15v1a3 3 0 0 0 3 3 3 3 0 0 0 3 3h1a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H9Z" />
      <path d="M15 3a3 3 0 0 1 3 3v.3A3 3 0 0 1 20 9v1a3 3 0 0 1-1 2.2 3 3 0 0 1 1 2.8v1a3 3 0 0 1-3 3 3 3 0 0 1-3 3h-1a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h1Z" />
    </svg>
  ),
  shield: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3 20 6.5v5.3c0 4.8-3.2 8.3-8 9.7-4.8-1.4-8-4.9-8-9.7V6.5L12 3Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  ),
  gauge: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 20a8 8 0 1 1 8-8" />
      <path d="M12 12 16 8" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  ),
  eye: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1.5 12S5 5 12 5s10.5 7 10.5 7-3.5 7-10.5 7S1.5 12 1.5 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  fingerprint: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3a7 7 0 0 0-7 7v2a15 15 0 0 0 2 7.5" />
      <path d="M12 3a7 7 0 0 1 7 7v2c0 1.5-.2 3-.6 4.4" />
      <path d="M8 21a13 13 0 0 1-1.5-6v-2a5.5 5.5 0 0 1 11 0v2a12 12 0 0 1-.6 3.8" />
      <path d="M9.5 21a10 10 0 0 1-1-4v-2a3.5 3.5 0 1 1 7 0" />
    </svg>
  ),
  phone: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2h12a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z" />
      <path d="M11 18h2" />
    </svg>
  ),
  layers: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 2 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5" />
      <path d="m3 17 9 5 9-5" />
    </svg>
  ),
  bolt: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" />
    </svg>
  ),
  check: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="m20 6-11 11-5-5" />
    </svg>
  ),
};

/* ------------------------------------------------------------------ *
 * Page
 * ------------------------------------------------------------------ */
export default function AboutClient() {
  return (
    <div className="relative isolate min-h-screen">
      <AmbientBackground />

      {/* Top bar — brand + explicit way back to the running application */}
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-6 sm:px-8">
        <Logo />
        <div className="flex items-center gap-2.5">
          <Link
            href="/"
            className="btn-tactile flex items-center gap-1.5 rounded-control border border-border bg-surface px-3.5 py-2 text-sm font-medium text-foreground shadow-card transition-colors hover:border-border-strong"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 19-7-7 7-7M5 12h14" />
            </svg>
            Back to Monitor
          </Link>
          <ThemeToggle />
        </div>
      </header>

      {/* ---------------------------------------------------------- */}
      {/* 1. Hero                                                     */}
      {/* ---------------------------------------------------------- */}
      <section className="mx-auto flex w-full max-w-6xl flex-col items-center px-5 pb-20 pt-6 text-center sm:px-8 sm:pb-28 sm:pt-10">
        <div className="animate-boot-in inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted shadow-card">
          <span className="h-1.5 w-1.5 rounded-full bg-risk-low" />
          Real-time voice risk intelligence
        </div>

        <h1 className="animate-fade-in-up mt-6 max-w-3xl text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-6xl">
          Know if the voice on the call is <span className="text-accent">who it claims to be</span>.
        </h1>

        <p
          className="animate-fade-in-up mt-5 max-w-xl text-balance text-[15px] leading-relaxed text-muted sm:text-base"
          style={{ animationDelay: "80ms" }}
        >
          VoxGuard is an AI-powered voice security and fraud detection platform. It listens to a
          call as it happens and continuously scores how likely the voice is being cloned or
          impersonated — before a fraudulent transaction goes through.
        </p>

        <div
          className="animate-fade-in-up mt-8 flex flex-col items-center gap-3 sm:flex-row"
          style={{ animationDelay: "150ms" }}
        >
          <Link
            href="/"
            className="btn-tactile rounded-control bg-accent px-5 py-2.5 text-sm font-medium text-accent-contrast shadow-card transition-opacity hover:opacity-90"
          >
            Open VoxGuard Monitor →
          </Link>
          <a
            href="#how-it-works"
            className="btn-tactile rounded-control border border-border bg-surface px-5 py-2.5 text-sm font-medium text-foreground shadow-card transition-colors hover:border-border-strong"
          >
            See how it works
          </a>
        </div>

        {/* Ambient hero visual — live waveform collapsing into a risk read-out */}
        <div
          className="interactive-surface animate-fade-in-up mt-14 flex w-full max-w-2xl flex-col gap-4 rounded-card border border-border bg-surface p-6 shadow-elevated sm:flex-row sm:items-center sm:justify-between"
          style={{ animationDelay: "220ms" }}
        >
          <div className="flex items-end gap-1.5">
            {[0.4, 0.75, 1, 0.5, 0.9, 0.35, 0.7, 0.55, 0.85, 0.45].map((h, i) => (
              <span
                key={i}
                className="w-1.5 rounded-full bg-accent"
                style={{
                  height: `${h * 36}px`,
                  animationName: "waveform-bar",
                  animationDuration: "900ms",
                  animationTimingFunction: "ease-in-out",
                  animationIterationCount: "infinite",
                  animationDelay: `${i * 90}ms`,
                  opacity: 0.85,
                }}
              />
            ))}
          </div>
          <svg width="20" height="20" viewBox="0 0 24 24" className="hidden shrink-0 text-muted sm:block" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
          <div className="flex items-center gap-3 rounded-control border border-risk-lowBorder bg-risk-lowBg px-4 py-2.5">
            <span className="h-2 w-2 rounded-full bg-risk-low" />
            <span className="text-sm font-medium text-risk-low">Low risk — continue with caution</span>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- */}
      {/* 2. What is VoxGuard                                         */}
      {/* ---------------------------------------------------------- */}
      <Section
        id="what"
        eyebrow="What is VoxGuard"
        title="A live risk score for the voice you're talking to"
        description="Rather than judging a call after it ends, VoxGuard breaks incoming audio into short chunks and analyzes each one as it arrives — turning subtle acoustic and behavioral cues into a single, continuously updating impersonation-risk score."
      >
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {[
            {
              icon: icons.phone,
              title: "Built for live calls",
              text: "Audio is processed in rolling 2–4 second windows while the call is still happening, not from a finished recording.",
            },
            {
              icon: icons.layers,
              title: "Multiple signal layers",
              text: "Acoustic/spectral cues, voice prosody, and optional consented speaker verification are combined rather than relied on alone.",
            },
            {
              icon: icons.bolt,
              title: "Actionable, not just informational",
              text: "Risk crossing a threshold surfaces a concrete recommendation — continue, pause and verify, or block — not just a number.",
            },
          ].map((f, i) => (
            <Reveal key={f.title} delay={i * 100}>
              <div className="interactive-surface h-full rounded-card border border-border bg-surface p-6 shadow-card">
                <span className="flex h-10 w-10 items-center justify-center rounded-control bg-accent-soft text-accent">
                  {f.icon}
                </span>
                <h3 className="mt-4 text-[15px] font-semibold text-foreground">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{f.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ---------------------------------------------------------- */}
      {/* 3. Why VoxGuard                                             */}
      {/* ---------------------------------------------------------- */}
      <Section
        id="why"
        eyebrow="Why it matters"
        title="Voice cloning is convincing enough to fool a human, mid-call"
        description="Modern voice-cloning models can reproduce a familiar voice from a short sample. By the time a call ends and something feels off, a transfer may already be approved. VoxGuard is designed to raise the flag while the call — and the decision — is still in progress."
      >
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Reveal className="interactive-surface rounded-card border border-risk-highBorder bg-risk-highBg p-6 shadow-card">
            <span className="text-xs font-semibold uppercase tracking-wide text-risk-high">
              The problem
            </span>
            <p className="mt-3 text-sm leading-relaxed text-foreground">
              Traditional checks — caller ID, &ldquo;I recognize this voice,&rdquo; a callback to
              the same number — no longer reliably catch a well-executed synthetic voice, especially under
              the urgency an attacker manufactures on the call itself.
            </p>
          </Reveal>
          <Reveal delay={100} className="interactive-surface rounded-card border border-risk-lowBorder bg-risk-lowBg p-6 shadow-card">
            <span className="text-xs font-semibold uppercase tracking-wide text-risk-low">
              The VoxGuard approach
            </span>
            <p className="mt-3 text-sm leading-relaxed text-foreground">
              Score the call as audio arrives, smooth that score over time so a single odd moment
              doesn&apos;t cause a false alarm, and pair the result with an explainable, deterministic
              recommendation the person on the call can act on immediately.
            </p>
          </Reveal>
        </div>
      </Section>

      {/* ---------------------------------------------------------- */}
      {/* 4. How it works — pipeline                                  */}
      {/* ---------------------------------------------------------- */}
      <Section
        id="how-it-works"
        eyebrow="How it works"
        title="From raw audio to a security decision"
        description="An explanatory view of the existing detection pipeline — the underlying model logic is unchanged; this is simply a visual walkthrough of the stages a call passes through."
      >
        <style>{`@keyframes pulse-dot { 0%,100% { transform: translateX(0); opacity: .9 } 50% { transform: translateX(calc(100% - 0.75rem)); opacity: .4 } }`}</style>
        <div className="interactive-surface rounded-card border border-border bg-surface p-6 shadow-card sm:p-10">
          <div className="flex flex-col gap-10 sm:flex-row sm:gap-6">
            <PipelineStep index={0} icon={icons.phone} title="Voice / Call" description="Live or simulated call audio enters the stream." />
            <PipelineStep index={1} icon={icons.wave} title="Audio & Context Analysis" description="Audio is chunked; acoustic and spectral patterns are extracted." />
            <PipelineStep index={2} icon={icons.fingerprint} title="Identity / Prosody Analysis" description="Pitch, rhythm, and (with consent) speaker-identity drift are checked." />
            <PipelineStep index={3} icon={icons.gauge} title="Risk Detection" description="Per-chunk scores are smoothed into a rolling risk score and alert level." />
            <PipelineStep index={4} icon={icons.shield} title="Security Decision" description="A deterministic policy turns risk + context into a clear recommendation." last />
          </div>
        </div>
        <p className="mt-4 text-center text-xs text-muted">
          Visualization only — the actual model pipeline and thresholds are unchanged.
        </p>
      </Section>

      {/* ---------------------------------------------------------- */}
      {/* 5. Core capabilities — flash cards                          */}
      {/* ---------------------------------------------------------- */}
      <Section
        id="capabilities"
        eyebrow="Core capabilities"
        title="What VoxGuard actually looks at"
        description="Six concepts behind the platform. Tap a card to see how it's used."
      >
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <FlashCard
            delay={0}
            card={{
              icon: icons.wave,
              title: "Voice Analysis",
              front: "Examines the acoustic and spectral shape of the audio itself.",
              back: "Each audio chunk is screened for synthesis artifacts and spectral signatures characteristic of AI-generated speech, alongside natural prosody such as pitch and voiced-speech ratio.",
            }}
          />
          <FlashCard
            delay={80}
            card={{
              icon: icons.brain,
              title: "AI Risk Detection",
              front: "Turns raw acoustic signals into a per-chunk risk estimate.",
              back: "A spoof-detection model scores each chunk for the likelihood of synthetic or cloned speech, running off the main thread so live streaming isn't blocked.",
            }}
          />
          <FlashCard
            delay={160}
            card={{
              icon: icons.shield,
              title: "Security Monitoring",
              front: "Watches the call continuously, not just at the start.",
              back: "Risk is re-evaluated on every incoming chunk for the life of the call, so a call that starts clean but drifts risky is still caught.",
            }}
          />
          <FlashCard
            delay={0}
            card={{
              icon: icons.gauge,
              title: "Risk Score",
              front: "A single 0–100% number that reflects recent call behavior.",
              back: "Per-chunk scores are combined into a weighted rolling average that favors the most recent chunks, then mapped to a low / medium / high alert level against fixed thresholds.",
            }}
          />
          <FlashCard
            delay={80}
            card={{
              icon: icons.eye,
              title: "Model Transparency",
              front: "Every recommendation comes with reasons, not just a verdict.",
              back: "The policy engine attaches explicit reason codes (e.g. an unknown caller, a sensitive request, a high-value transfer) to each recommendation, and never silently overrides the acoustic score.",
            }}
          />
          <FlashCard
            delay={160}
            card={{
              icon: icons.fingerprint,
              title: "Identity / Prosody",
              front: "Speaking style and, optionally, voice identity itself.",
              back: "Prosody features (pitch variance, pauses, speech rate) are always checked. If a consented reference voice is provided, speaker verification tracks identity drift across the session — separately from the acoustic spoof check.",
            }}
          />
        </div>
      </Section>

      {/* ---------------------------------------------------------- */}
      {/* 6. Risk intelligence                                        */}
      {/* ---------------------------------------------------------- */}
      <Section
        id="risk-intelligence"
        eyebrow="Risk intelligence"
        title="How the risk score becomes a decision"
        description="A conceptual view of the threshold logic behind the live gauge on the monitor — not a snapshot of any real call."
      >
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Reveal className="interactive-surface rounded-card border border-border bg-surface p-6 shadow-card sm:p-8">
            <h3 className="text-sm font-semibold text-foreground">Risk spectrum</h3>
            <div className="mt-6 h-3 w-full overflow-hidden rounded-full bg-gauge-track">
              <div
                className="h-full w-full"
                style={{
                  background:
                    "linear-gradient(to right, var(--risk-low) 0%, var(--risk-low) 40%, var(--risk-medium) 40%, var(--risk-medium) 70%, var(--risk-high) 70%, var(--risk-high) 100%)",
                }}
              />
            </div>
            <div className="mt-3 flex justify-between text-[11px] font-medium text-muted">
              <span className="text-risk-low">Low · &lt; 40%</span>
              <span className="text-risk-medium">Medium · 40–70%</span>
              <span className="text-risk-high">High · &gt; 70%</span>
            </div>
            <p className="mt-6 text-sm leading-relaxed text-muted">
              Rather than reacting to any single noisy chunk, VoxGuard keeps a short rolling
              window of recent scores, weighting the most recent chunks more heavily. That
              smooths out one-off glitches while still letting the score climb quickly if several
              risky chunks arrive in a row.
            </p>
          </Reveal>

          <div className="flex flex-col gap-4">
            {(
              [
                {
                  level: "low",
                  label: "Continue with caution",
                  desc: "No irregular voice patterns in the current window.",
                  wrap: "border-risk-lowBorder bg-risk-lowBg",
                  dot: "bg-risk-low",
                  text: "text-risk-low",
                },
                {
                  level: "medium",
                  label: "Pause and verify",
                  desc: "Signals are drifting from expected patterns — confirm identity before proceeding.",
                  wrap: "border-risk-mediumBorder bg-risk-mediumBg",
                  dot: "bg-risk-medium",
                  text: "text-risk-medium",
                },
                {
                  level: "high",
                  label: "Block and report",
                  desc: "Strong indicators of voice impersonation — do not approve; verify out-of-band.",
                  wrap: "border-risk-highBorder bg-risk-highBg",
                  dot: "bg-risk-high",
                  text: "text-risk-high",
                },
              ] as const
            ).map((row, i) => (
              <Reveal key={row.level} delay={i * 90}>
                <div className={`interactive-surface flex items-start gap-3 rounded-card border p-4 shadow-card ${row.wrap}`}>
                  <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${row.dot}`} />
                  <div>
                    <p className={`text-sm font-semibold ${row.text}`}>{row.label}</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted">{row.desc}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* ---------------------------------------------------------- */}
      {/* 7. Model transparency                                       */}
      {/* ---------------------------------------------------------- */}
      <Section
        id="transparency"
        eyebrow="Model transparency"
        title="Every decision comes with a reason"
        description="Security tools that act like a black box are hard to trust in the middle of a real call. VoxGuard's advisory layer is deliberately simple and explainable, sitting on top of the acoustic model rather than replacing it."
      >
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {[
            {
              icon: icons.eye,
              title: "Reason codes, not just a verdict",
              text: "Recommendations are attached to explicit codes — an unknown caller, a request for an OTP/PIN, a high-value transfer — so it's clear why a call was flagged.",
            },
            {
              icon: icons.layers,
              title: "Deterministic policy",
              text: "The same risk level and context always produce the same recommendation. The advisory layer never silently adjusts the underlying acoustic score.",
            },
            {
              icon: icons.check,
              title: "Signals, not proof",
              text: "Prosody and identity-drift checks are supporting signals with clearly labeled, uncalibrated thresholds — not standalone proof that a voice is cloned.",
            },
          ].map((f, i) => (
            <Reveal key={f.title} delay={i * 100}>
              <div className="interactive-surface h-full rounded-card border border-border bg-surface p-6 shadow-card">
                <span className="flex h-10 w-10 items-center justify-center rounded-control bg-accent-soft text-accent">
                  {f.icon}
                </span>
                <h3 className="mt-4 text-[15px] font-semibold text-foreground">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{f.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ---------------------------------------------------------- */}
      {/* 8. Final CTA                                                */}
      {/* ---------------------------------------------------------- */}
      <section className="mx-auto w-full max-w-4xl px-5 pb-24 sm:px-8">
        <Reveal>
          <div className="interactive-surface relative overflow-hidden rounded-card border border-border bg-surface p-10 text-center shadow-elevated sm:p-14">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0 opacity-70"
              style={{
                background:
                  "radial-gradient(circle at 20% 20%, var(--ambient-a), transparent 45%), radial-gradient(circle at 85% 80%, var(--ambient-b), transparent 40%)",
              }}
            />
            <div className="relative">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft text-accent mx-auto">
                {icons.shield}
              </span>
              <h2 className="mt-5 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                Ready to see it live?
              </h2>
              <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-muted">
                Head back to the monitor to run a simulated call and watch the risk score,
                alerts, and advisory update in real time.
              </p>
              <Link
                href="/"
                className="btn-tactile mt-7 inline-flex items-center gap-2 rounded-control bg-accent px-6 py-3 text-sm font-medium text-accent-contrast shadow-card transition-opacity hover:opacity-90"
              >
                Open VoxGuard Monitor
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </Link>
            </div>
          </div>
        </Reveal>

        <p className="mt-8 text-center text-xs text-muted">
          Built for Smart India Hackathon 2026 — PS SIH26104 (Cyber Security Cell, AICTE).
        </p>
      </section>
    </div>
  );
}
