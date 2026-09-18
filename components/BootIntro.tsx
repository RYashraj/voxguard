"use client";

import { useEffect, useState } from "react";
import Logo from "@/components/Logo";

// Purely visual first-load intro. Renders on top of the app for a beat,
// then fades itself out. It never gates, delays, or depends on any data
// fetching, websocket connection, auth, or routing underneath it — those
// all start immediately and run exactly as before; this component only
// controls its own opacity/visibility.
export default function BootIntro() {
  const [phase, setPhase] = useState<"in" | "out" | "done">("in");

  useEffect(() => {
    const toOut = setTimeout(() => setPhase("out"), 900);
    const toDone = setTimeout(() => setPhase("done"), 1300);
    return () => {
      clearTimeout(toOut);
      clearTimeout(toDone);
    };
  }, []);

  if (phase === "done") return null;

  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 z-50 flex items-center justify-center bg-background transition-opacity duration-300 ease-out ${
        phase === "out" ? "pointer-events-none opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex flex-col items-center gap-3 animate-boot-in">
        <div className="scale-[1.7]">
          <Logo withWordmark={false} />
        </div>
        <span className="mt-2 text-base font-semibold tracking-tight text-foreground">
          VoxGuard
        </span>
      </div>
    </div>
  );
}
