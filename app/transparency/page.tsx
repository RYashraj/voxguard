"use client";

import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import transparencyData from "@/data/transparency.json";
import { TransparencyBenchmark } from "@/types/risk";

// Task 5 (PS ref 5c — multilingual/Indian-accent robustness). This table is
// wired to data/transparency.json so the ML team's real numbers can drop in
// later without touching this page. The values shipped here are PLACEHOLDER
// data only — they have not been produced by an actual model evaluation —
// and must stay clearly labeled as such until the ML team supplies real
// results.
const IS_PLACEHOLDER_DATA = true;

export default function TransparencyPage() {
  const benchmarks: TransparencyBenchmark[] = transparencyData;

  return (
    <main className="min-h-screen bg-background font-mono text-ink">
      <div className="mx-auto max-w-[1000px] w-full px-5 py-8 md:px-10 md:py-10">
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
              <p className="text-sm text-muted">Model Transparency</p>
            </div>
          </div>

          <div className="flex items-center gap-4 font-mono text-sm">
            <Link
              href="/"
              className="border border-line px-4 py-2 text-muted hover:text-ink hover:border-ink transition-colors"
            >
              ← Back to Dashboard
            </Link>
            <ThemeToggle />
          </div>
        </header>

        <div className="mt-8">
          <div className="border border-line bg-surface p-6">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-4">
              <div>
                <h1 className="text-2xl font-semibold text-ink">
                  Model Transparency
                </h1>
                <p className="mt-2 text-sm text-muted max-w-xl">
                  Detection accuracy by accent/language, so judges can see real
                  numbers rather than an unverified claim.
                </p>
              </div>
              <span className="font-mono text-xs border border-line px-3 py-1 text-muted">
                PS Ref: 5c
              </span>
            </div>

            {IS_PLACEHOLDER_DATA && (
              <div className="mt-5 border border-amber-500/40 bg-amber-950/20 px-4 py-3 text-sm text-amber-500">
                <strong className="uppercase tracking-wider text-xs">
                  ⚠ Placeholder / Test Data
                </strong>
                <p className="mt-1 text-amber-400">
                  The figures below have not been produced by a real model
                  evaluation yet. They exist only to hold the table&apos;s shape
                  until the ML team provides actual accuracy numbers.
                </p>
              </div>
            )}

            <div className="mt-5 overflow-x-auto border border-line">
              <table className="w-full text-left font-mono text-sm">
                <thead className="border-b border-line bg-background text-xs uppercase tracking-wider text-muted">
                  <tr>
                    <th className="px-5 py-3.5">Accent/Language</th>
                    <th className="px-5 py-3.5 text-right">
                      Detection Accuracy (%)
                    </th>
                    <th className="px-5 py-3.5 text-right">Sample Size</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line bg-surface">
                  {benchmarks.map((item) => (
                    <tr
                      key={item.accent_language}
                      className="hover:bg-background/50 transition-colors"
                    >
                      <td className="px-5 py-4 font-bold text-ink">
                        {item.accent_language}
                      </td>
                      <td className="px-5 py-4 text-right text-ink">
                        {item.accuracy}%
                      </td>
                      <td className="px-5 py-4 text-right text-muted">
                        {item.sample_size}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mt-4 text-xs text-muted">
              Data source: <code>data/transparency.json</code> — replace with
              the ML team&apos;s real results when available.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
