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
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: "var(--surface)",
        "surface-raised": "var(--surface-raised)",
        "surface-sunken": "var(--surface-sunken)",
        border: "var(--border)",
        "border-strong": "var(--border-strong)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        "accent-strong": "var(--accent-strong)",
        "accent-soft": "var(--accent-soft)",
        "accent-contrast": "var(--accent-contrast)",
        // kept as an alias so any existing `signal` usage keeps working
        signal: "var(--accent)",
        risk: {
          low: "var(--risk-low)",
          lowBg: "var(--risk-low-bg)",
          lowBorder: "var(--risk-low-border)",
          medium: "var(--risk-medium)",
          mediumBg: "var(--risk-medium-bg)",
          mediumBorder: "var(--risk-medium-border)",
          high: "var(--risk-high)",
          highBg: "var(--risk-high-bg)",
          highBorder: "var(--risk-high-border)",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-geist-sans)",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "var(--font-geist-mono)",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
      borderRadius: {
        card: "18px",
        control: "10px",
      },
      boxShadow: {
        soft: "var(--shadow-soft)",
        card: "var(--shadow-card)",
        elevated: "var(--shadow-elevated)",
        press: "var(--shadow-press)",
      },
      ringColor: {
        accent: "var(--ring-accent)",
      },
    },
  },
  plugins: [],
};
export default config;
