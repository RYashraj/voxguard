"use client";

import { useState } from "react";

interface PreTransactionModalProps {
  isOpen: boolean;
  reason?: string;
  recommendedActions?: string[];
  onActionSelect: (action: string) => void;
}

export default function PreTransactionModal({
  isOpen,
  reason = "High impersonation risk score detected before processing sensitive transaction.",
  recommendedActions = [
    "Call-back Verification",
    "Multi-Factor Authentication (MFA)",
    "Escalate to Supervisor",
  ],
  onActionSelect,
}: PreTransactionModalProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);

  if (!isOpen) return null;

  function handleChoice(action: string) {
    setSelectedAction(action);
    // Secondary verification action handler
    setTimeout(() => {
      onActionSelect(action);
      setSelectedAction(null);
    }, 250);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg border-2 border-red-500 bg-surface p-6 shadow-[0_0_30px_rgba(239,68,68,0.35)] font-mono text-ink">
        <div className="flex items-center gap-3 border-b border-line pb-4 text-red-500">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-500/10 border border-red-500/30 text-xl font-bold animate-pulse">
            ⚠️
          </div>
          <div>
            <h2 className="text-lg font-bold uppercase tracking-wide text-red-500">
              Pre-Transaction Risk Alert
            </h2>
            <p className="text-xs text-muted">PS Reference 3b — Proactive Safeguard</p>
          </div>
        </div>

        <div className="my-5 space-y-3">
          <div className="border border-red-500/20 bg-red-950/20 p-3 text-sm text-red-400">
            <strong className="block text-xs uppercase text-red-500">System Warning:</strong>
            {reason}
          </div>
          <p className="text-xs text-muted">
            The active call exceeded safety risk thresholds for the selected transaction context.
            Choose a secondary verification protocol to proceed:
          </p>
        </div>

        <div className="space-y-2.5">
          <p className="text-xs uppercase tracking-wider text-muted font-semibold">
            Recommended Actions:
          </p>
          {recommendedActions.map((action) => {
            const isSelected = selectedAction === action;
            return (
              <button
                key={action}
                onClick={() => handleChoice(action)}
                className={`w-full flex items-center justify-between border px-4 py-3 text-sm font-bold transition-all text-left ${
                  isSelected
                    ? "border-red-500 bg-red-500 text-white"
                    : "border-line bg-background text-ink hover:border-red-500 hover:bg-surface"
                }`}
              >
                <span>{action}</span>
                <span className="text-xs font-normal text-muted">
                  {isSelected ? "Selected ✓" : "Trigger Protocol →"}
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-5 text-center text-xs text-muted border-t border-line pt-3">
          Mandatory safety gate — action selection logged to session history.
        </div>
      </div>
    </div>
  );
}
