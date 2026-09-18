"use client";

import { useState, useEffect } from "react";

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

interface FileLists {
  original: string[];
  clone: string[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function IdentityCloneLab() {
  const [fileLists, setFileLists] = useState<FileLists>({ original: [], clone: [] });
  const [selectedOriginal, setSelectedOriginal] = useState<string>("");
  const [selectedClone, setSelectedClone] = useState<string>("");
  const [result, setResult] = useState<IdentityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(true);

  // Fetch available file lists on mount
  useEffect(() => {
    async function fetchFiles() {
      try {
        const response = await fetch(`${API_BASE_URL}/identity-demo/files`);
        const data: FileLists = await response.json();
        setFileLists(data);
        if (data.original.length > 0) setSelectedOriginal(data.original[0]);
        if (data.clone.length > 0) setSelectedClone(data.clone[0]);
      } catch {
        // Files endpoint unavailable; dropdowns will show placeholder
      } finally {
        setFilesLoading(false);
      }
    }
    fetchFiles();
  }, []);

  async function compareVoices() {
    setLoading(true);
    try {
      // Pass selected filenames as query params so backend picks them
      const params = new URLSearchParams();
      if (selectedOriginal) params.set("original_file", selectedOriginal);
      if (selectedClone) params.set("clone_file", selectedClone);
      const response = await fetch(`${API_BASE_URL}/identity-demo/compare?${params.toString()}`);
      const payload = await response.json();
      setResult(payload);
    } catch {
      setResult({ status: "identity_unavailable", message: "Identity comparison endpoint unavailable" });
    } finally {
      setLoading(false);
    }
  }

  const mismatch = result?.identity_mismatch;
  const hasFiles = fileLists.original.length > 0 && fileLists.clone.length > 0;

  return (
    <section className="identity-lab rounded-card border border-border bg-surface p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">Clone identity lab</p>
          <h2 className="mt-2 text-xl font-semibold text-foreground">Original voice vs consented AI clone</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">ECAPA speaker embeddings compare identity drift separately from synthetic-artifact risk.</p>
        </div>
      </div>

      {/* Voice file selectors */}
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="original-voice-selector" className="mb-1 block text-xs font-medium text-muted">
            Original (reference) voice
          </label>
          <select
            id="original-voice-selector"
            value={selectedOriginal}
            onChange={(e) => { setSelectedOriginal(e.target.value); setResult(null); }}
            disabled={filesLoading || loading || !hasFiles}
            className="w-full rounded-control border border-border bg-background px-3 py-2.5 text-sm text-foreground transition-colors hover:border-border-strong focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent disabled:opacity-50"
          >
            {filesLoading && <option>Loading files…</option>}
            {!filesLoading && !hasFiles && <option>No original files found</option>}
            {fileLists.original.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="clone-voice-selector" className="mb-1 block text-xs font-medium text-muted">
            AI clone voice (to compare)
          </label>
          <select
            id="clone-voice-selector"
            value={selectedClone}
            onChange={(e) => { setSelectedClone(e.target.value); setResult(null); }}
            disabled={filesLoading || loading || !hasFiles}
            className="w-full rounded-control border border-border bg-background px-3 py-2.5 text-sm text-foreground transition-colors hover:border-border-strong focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent disabled:opacity-50"
          >
            {filesLoading && <option>Loading files…</option>}
            {!filesLoading && !hasFiles && <option>No clone files found</option>}
            {fileLists.clone.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="button"
        onClick={compareVoices}
        disabled={loading || !hasFiles || !selectedOriginal || !selectedClone}
        className="mt-4 w-full rounded-control bg-accent px-4 py-3 text-base font-semibold text-accent-contrast disabled:opacity-60"
      >
        {loading ? "Comparing…" : "Compare selected voice pair"}
      </button>

      {result && (
        <div className={`mt-5 rounded-control border p-4 ${mismatch ? "border-risk-highBorder bg-risk-highBg" : "border-border bg-background"}`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-lg font-semibold text-foreground">
              {result.status === "ok" ? (mismatch ? "⚠ Identity mismatch detected" : "✓ Identity match") : "Identity comparison unavailable"}
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
