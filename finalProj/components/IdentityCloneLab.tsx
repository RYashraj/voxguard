"use client";

import { useState } from "react";

interface IdentityResult {
  status: string;
  message?: string;
  original_file?: string;
  clone_file?: string;
  speaker_similarity?: number;
  identity_drift?: number;
  confidence?: number;
  flags?: string[];
  identity_mismatch?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function IdentityCloneLab() {
  const [result, setResult] = useState<IdentityResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function compareVoices() {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/identity-demo/compare`);
      const payload = await response.json();
      setResult(payload);
    } catch {
      setResult({ status: "identity_unavailable", message: "Identity comparison endpoint unavailable" });
    } finally {
      setLoading(false);
    }
  }

  const mismatch = result?.identity_mismatch;

  return (
    <section className="identity-lab rounded-card border border-border bg-surface p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">Clone identity lab</p>
          <h2 className="mt-2 text-xl font-semibold text-foreground">Original voice vs consented AI clone</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">ECAPA speaker embeddings compare identity drift separately from synthetic-artifact risk.</p>
        </div>
        <button type="button" onClick={compareVoices} disabled={loading} className="rounded-control bg-accent px-4 py-3 text-base font-semibold text-accent-contrast disabled:opacity-60">
          {loading ? "Comparing…" : "Compare consented pair"}
        </button>
      </div>
      {result && (
        <div className={`mt-5 rounded-control border p-4 ${mismatch ? "border-risk-highBorder bg-risk-highBg" : "border-border bg-background"}`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-lg font-semibold text-foreground">
              {result.status === "ok" ? (mismatch ? "Identity mismatch detected" : "Identity match") : "Identity comparison unavailable"}
            </span>
            {result.identity_drift !== undefined && <span className="font-mono text-base text-foreground">drift {Math.round(result.identity_drift * 100)}%</span>}
          </div>
          <p className="mt-2 text-sm text-muted">Reference: {result.original_file ?? "not loaded"} · Compared: {result.clone_file ?? "not loaded"}</p>
          {result.speaker_similarity !== undefined && <p className="mt-1 text-sm text-muted">Speaker similarity: {Math.round(result.speaker_similarity * 100)}% · confidence: {Math.round((result.confidence ?? 0) * 100)}%</p>}
          {result.message && <p className="mt-2 text-sm text-muted">{result.message}</p>}
          <p className="mt-3 text-sm font-medium text-foreground">This is a consented identity comparison; it is not a claim that every AI clone can be detected without calibration.</p>
        </div>
      )}
    </section>
  );
}
