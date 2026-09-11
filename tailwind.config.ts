import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm instrument-panel palette — driven by CSS vars so light/dark
        // both stay in the same warm/ink family (no navy dark-mode flip).
        background: "var(--bg)",
        surface: "var(--surface)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        line: "var(--line)",
        risk: {
          low: "var(--risk-low)",
          medium: "var(--risk-medium)",
          high: "var(--risk-high)",
        },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        DEFAULT: "2px",
      },
    },
  },
  plugins: [],
};
export default config;
