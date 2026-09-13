"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const stored = window.localStorage.getItem("voxguard-theme");
    const initial: Theme =
      stored === "dark" || stored === "light"
        ? stored
        : window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    setTheme(initial);
  }, []);

  function apply(next: Theme) {
    setTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
    window.localStorage.setItem("voxguard-theme", next);
  }

  return (
    <div className="flex border border-line font-mono text-[11px]">
      <button
        onClick={() => apply("light")}
        aria-pressed={theme === "light"}
        className={`px-2 py-1 transition-colors ${
          theme === "light" ? "bg-ink text-background" : "text-muted"
        }`}
      >
        light
      </button>
      <button
        onClick={() => apply("dark")}
        aria-pressed={theme === "dark"}
        className={`border-l border-line px-2 py-1 transition-colors ${
          theme === "dark" ? "bg-ink text-background" : "text-muted"
        }`}
      >
        dark
      </button>
    </div>
  );
}
