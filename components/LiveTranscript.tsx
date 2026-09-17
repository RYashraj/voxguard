"use client";

import { useEffect, useState, useRef } from "react";

interface LiveTranscriptProps {
  active: boolean;
}

export default function LiveTranscript({ active }: LiveTranscriptProps) {
  const [history, setHistory] = useState<string>("");
  const [interim, setInterim] = useState<string>("");
  
  const recognitionRef = useRef<any>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<boolean>(active);

  // Sync ref with prop to avoid stale closures in onend
  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;

        recognitionRef.current.onresult = (event: any) => {
          let finalChunk = "";
          let interimChunk = "";

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalChunk += event.results[i][0].transcript + " ";
            } else {
              interimChunk += event.results[i][0].transcript;
            }
          }

          if (finalChunk) {
            setHistory((prev) => prev + finalChunk);
          }
          setInterim(interimChunk);

          if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
          }
        };

        recognitionRef.current.onend = () => {
          // Restart immediately if we are still active (browser paused us due to silence)
          if (activeRef.current) {
            try {
              recognitionRef.current.start();
            } catch (e) {}
          }
        };

        recognitionRef.current.onerror = (event: any) => {
          console.warn("Speech recognition error", event.error);
        };
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        try {
          recognitionRef.current.stop();
        } catch (e) {}
      }
    };
  }, []);

  useEffect(() => {
    if (active && recognitionRef.current) {
      try {
        setHistory("");
        setInterim("");
        recognitionRef.current.start();
      } catch (e) {
        console.warn("Speech recognition start issue:", e);
      }
    } else if (!active && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
  }, [active]);

  return (
    <div className="border border-line bg-surface flex flex-col mt-5 h-48">
      <div className="flex items-center justify-between border-b border-line p-3">
        <p className="font-mono text-[11px] uppercase tracking-wide text-muted flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="22"></line>
          </svg>
          Live Audio Transcript
        </p>
        <span className="font-mono text-[10px] text-muted bg-background px-2 py-0.5 border border-line">
          {active ? "LISTENING" : "IDLE"}
        </span>
      </div>
      <div 
        ref={scrollRef}
        className="flex-grow p-4 overflow-y-auto font-sans text-sm text-ink/90 leading-relaxed bg-background/30"
      >
        {history || interim ? (
          <span>
            {history}
            <span className="text-muted italic">{interim}</span>
          </span>
        ) : active ? (
          <span className="text-muted italic">Waiting for speech...</span>
        ) : (
          <span className="text-muted italic">Start a live microphone call to see transcript here.</span>
        )}
      </div>
    </div>
  );
}
