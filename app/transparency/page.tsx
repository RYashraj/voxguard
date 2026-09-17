"use client";

import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import transparencyData from "@/data/transparency.json";
import { TransparencyBenchmark } from "@/types/risk";

export default function TransparencyPage() {
  const benchmarks: TransparencyBenchmark[] = transparencyData;

  return (
    <main className="min-h-screen bg-background font-mono text-ink">
      <div className="mx-auto max-w-[1200px] w-full px-5 py-8 md:px-10 md:py-10">
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
              <p className="text-sm text-muted">Architecture & ML Transparency</p>
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

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Architecture Section */}
          <section className="border border-line bg-surface p-6">
            <div className="border-b border-line pb-4 mb-6">
              <h2 className="text-2xl font-semibold text-ink">System Architecture</h2>
              <p className="mt-2 text-sm text-muted">Dual-Branch Deepfake & Impersonation Detection</p>
            </div>

            <div className="space-y-6 text-sm text-ink">
              <div>
                <h3 className="font-bold border-l-2 border-ink pl-3 uppercase tracking-wider text-xs text-muted mb-2">Layer 1: Audio Ingestion</h3>
                <p>VoxGuard operates passively via SIP/RTP media forking from enterprise PBX systems (e.g., Twilio, Asterisk). It adds zero latency to the live call.</p>
              </div>
              
              <div>
                <h3 className="font-bold border-l-2 border-ink pl-3 uppercase tracking-wider text-xs text-muted mb-2">Layer 2: Dual-Branch ML Pipeline</h3>
                <ul className="list-disc list-inside space-y-2 mt-2">
                  <li><strong>Branch A (Synthesis):</strong> <code className="bg-background px-1">Spectra-AASIST3</code> model detects synthetic acoustic artifacts and vocoder traces. Protects against AI Voice Clones.</li>
                  <li><strong>Branch B (Identity):</strong> <code className="bg-background px-1">ECAPA-TDNN</code> (SpeechBrain) computes cosine similarity against enrolled executive profiles. Protects against human impersonators.</li>
                </ul>
              </div>

              <div>
                <h3 className="font-bold border-l-2 border-ink pl-3 uppercase tracking-wider text-xs text-muted mb-2">Layer 3: Rolling Risk Aggregator</h3>
                <p>To prevent false positives from network packet loss, risk scores are fused and passed through a 5-chunk rolling average window (15 seconds) before raising critical alerts.</p>
              </div>

              <div>
                <h3 className="font-bold border-l-2 border-ink pl-3 uppercase tracking-wider text-xs text-muted mb-2">Layer 4: Tamper-Evident Audit Ledger</h3>
                <p>SHA-256 hashes of detected fraud events are pushed to a Web3 Smart Contract (Ethereum Sepolia), providing immutable cryptographic proof to regulators.</p>
              </div>
            </div>
          </section>

          {/* ML Transparency Section */}
          <section className="border border-line bg-surface p-6 flex flex-col">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-4 mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-ink">ML Evaluation Metrics</h2>
                <p className="mt-2 text-sm text-muted">Rigorous benchmarking on industry-standard datasets.</p>
              </div>
              <span className="font-mono text-xs border border-line px-3 py-1 text-muted whitespace-nowrap">
                PS Ref: 5c
              </span>
            </div>

            <div className="overflow-x-auto border border-line flex-grow">
              <table className="w-full text-left font-mono text-sm">
                <thead className="border-b border-line bg-background text-xs uppercase tracking-wider text-muted">
                  <tr>
                    <th className="px-5 py-3.5">Dataset / Modality</th>
                    <th className="px-5 py-3.5 text-right">EER</th>
                    <th className="px-5 py-3.5 text-right">FPR</th>
                    <th className="px-5 py-3.5 text-right">N</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line bg-surface">
                  {benchmarks.map((item, idx) => (
                    <tr key={idx} className="hover:bg-background/50 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-bold text-ink">{item.dataset}</div>
                        <div className="text-xs text-muted mt-1">{item.description}</div>
                      </td>
                      <td className="px-5 py-4 text-right font-bold text-ink">{item.eer}</td>
                      <td className="px-5 py-4 text-right text-ink">{item.fpr}</td>
                      <td className="px-5 py-4 text-right text-muted">{item.sample_size}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 text-xs text-muted bg-background p-3 border border-line">
              <span className="font-bold uppercase tracking-wider">Metrics Key:</span>
              <ul className="mt-2 space-y-1">
                <li><strong>EER (Equal Error Rate):</strong> The threshold where False Acceptance Rate and False Rejection Rate are equal. Lower is better.</li>
                <li><strong>FPR (False Positive Rate):</strong> Percentage of legitimate (bona-fide) calls incorrectly flagged as fraud.</li>
              </ul>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
