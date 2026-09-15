"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import { ThresholdSettings } from "@/types/risk";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const DEFAULT_THRESHOLDS: ThresholdSettings = {
  fund_transfer: 0.6,
  information_request: 0.7,
  routine: 0.8,
};

export default function SettingsPage() {
  const [thresholds, setThresholds] =
    useState<ThresholdSettings>(DEFAULT_THRESHOLDS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<
    { type: "success" | "error"; message: string } | null
  >(null);

  useEffect(() => {
    async function loadThresholds() {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/settings/thresholds`);
        if (res.ok) {
          const data = await res.json();
          if (
            data &&
            typeof data.fund_transfer === "number" &&
            typeof data.information_request === "number" &&
            typeof data.routine === "number"
          ) {
            setThresholds(data);
          }
        }
      } catch (err) {
        console.warn("Could not fetch thresholds from backend, using defaults", err);
      } finally {
        setLoading(false);
      }
    }
    loadThresholds();
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaveResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/settings/thresholds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(thresholds),
      });

      if (!res.ok) throw new Error(`Save failed with status ${res.status}`);
      setSaveResult({ type: "success", message: "Settings saved successfully." });
    } catch (err) {
      console.error("Failed to save threshold settings", err);
      setSaveResult({
        type: "error",
        message: "Failed to save settings. Please try again.",
      });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveResult(null), 4000);
    }
  }

  return (
    <main className="min-h-screen bg-background">
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
              <p className="text-sm text-muted">Workflow Configuration</p>
            </div>
          </div>

          <div className="flex items-center gap-4 font-mono text-sm">
            <Link
              href="/"
              className="border border-line px-4 py-2 text-muted hover:text-ink hover:border-ink transition-colors"
            >
              ← Back to Dashboard
            </Link>
            <Link
              href="/transparency"
              className="border border-line px-4 py-2 text-muted hover:text-ink hover:border-ink transition-colors"
            >
              Transparency 📊
            </Link>
            <ThemeToggle />
          </div>
        </header>

        <div className="mt-8 max-w-2xl">
          <div className="border border-line bg-surface p-6">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <h1 className="text-2xl font-semibold text-ink">
                  Configurable Workflows
                </h1>
                <p className="mt-1 text-sm text-muted">
                  Configure risk score escalation thresholds (0.0 to 1.0) per transaction type.
                </p>
              </div>
              <span className="font-mono text-xs border border-line px-2.5 py-1 text-muted">
                PS Ref: 3d
              </span>
            </div>

            {loading ? (
              <div className="py-12 text-center font-mono text-sm text-muted">
                Loading threshold settings…
              </div>
            ) : (
              <div className="mt-6 space-y-6 font-mono text-ink">
                {/* Row 1: Fund Transfer */}
                <div className="space-y-2 border border-line bg-background p-4">
                  <div className="flex items-center justify-between text-sm">
                    <label className="font-bold uppercase tracking-wider">
                      Fund Transfer Threshold
                    </label>
                    <span className="font-bold text-red-500">
                      {thresholds.fund_transfer.toFixed(2)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={thresholds.fund_transfer}
                    onChange={(e) =>
                      setThresholds({
                        ...thresholds,
                        fund_transfer: parseFloat(e.target.value),
                      })
                    }
                    className="w-full accent-ink cursor-pointer"
                  />
                  <p className="text-xs text-muted">
                    Triggers pre-transaction verification when risk score crosses this level during fund transfers.
                  </p>
                </div>

                {/* Row 2: Information Request */}
                <div className="space-y-2 border border-line bg-background p-4">
                  <div className="flex items-center justify-between text-sm">
                    <label className="font-bold uppercase tracking-wider">
                      Information Request Threshold
                    </label>
                    <span className="font-bold text-amber-500">
                      {thresholds.information_request.toFixed(2)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={thresholds.information_request}
                    onChange={(e) =>
                      setThresholds({
                        ...thresholds,
                        information_request: parseFloat(e.target.value),
                      })
                    }
                    className="w-full accent-ink cursor-pointer"
                  />
                  <p className="text-xs text-muted">
                    Triggers secondary verification during sensitive info / credential requests.
                  </p>
                </div>

                {/* Row 3: Routine */}
                <div className="space-y-2 border border-line bg-background p-4">
                  <div className="flex items-center justify-between text-sm">
                    <label className="font-bold uppercase tracking-wider">
                      Routine Call Threshold
                    </label>
                    <span className="font-bold text-emerald-500">
                      {thresholds.routine.toFixed(2)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={thresholds.routine}
                    onChange={(e) =>
                      setThresholds({
                        ...thresholds,
                        routine: parseFloat(e.target.value),
                      })
                    }
                    className="w-full accent-ink cursor-pointer"
                  />
                  <p className="text-xs text-muted">
                    Baseline risk threshold for general routine inquiries.
                  </p>
                </div>

                {/* Save Button */}
                <div className="flex items-center justify-between border-t border-line pt-5">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="border border-line bg-ink px-8 py-3 font-mono text-sm font-bold text-surface transition-opacity hover:opacity-90 disabled:opacity-50"
                  >
                    {saving ? "Saving…" : "Save Settings"}
                  </button>

                  {saveResult && (
                    <span
                      className={`font-mono text-xs font-semibold animate-fade-in ${
                        saveResult.type === "success" ? "text-emerald-500" : "text-red-500"
                      }`}
                    >
                      {saveResult.type === "success" ? "✓" : "✕"} {saveResult.message}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
