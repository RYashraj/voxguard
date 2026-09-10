import type { Config } from "tailwindcss";

const config: Config = {
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
        surface: "#111A2E",
        "surface-raised": "#182444",
        border: "#25324F",
        muted: "#8592AC",
        signal: "#5EEAD4",
        risk: {
          low: "#34D399",
          medium: "#F5B942",
          high: "#F0546B",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
      boxShadow: {
        glow: "0 0 24px -4px rgba(94, 234, 212, 0.35)",
      },
    },
  },
  plugins: [],
};
export default config;
