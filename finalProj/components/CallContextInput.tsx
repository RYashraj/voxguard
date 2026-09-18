"use client";

import { SimulationContext, CallerContext, TransactionType } from "@/types/risk";

interface CallContextInputProps {
  value: SimulationContext;
  onChange: (context: SimulationContext) => void;
  disabled?: boolean;
}

const FIELD_CLASSES =
  "w-full rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground transition-colors hover:border-border-strong focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent disabled:opacity-50";

export default function CallContextInput({
  value,
  onChange,
  disabled = false,
}: CallContextInputProps) {
  const handleCallerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({
      ...value,
      caller_context: e.target.value as CallerContext,
    });
  };

  const handleTransactionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextType = e.target.value as TransactionType;
    onChange({
      ...value,
      transaction_type: nextType,
      transaction_amount:
        nextType === "fund_transfer" ? value.transaction_amount ?? 10000 : undefined,
    });
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const parsed = parseFloat(e.target.value);
    onChange({
      ...value,
      transaction_amount: isNaN(parsed) || parsed < 0 ? undefined : parsed,
    });
  };

  return (
    <div className="interactive-surface rounded-card border border-border bg-surface p-5 shadow-card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-foreground">Call Context</h2>
        <span className="text-xs text-muted">Simulator input</span>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted" htmlFor="caller-context-select">
            Caller Status
          </label>
          <select
            id="caller-context-select"
            value={value.caller_context}
            onChange={handleCallerChange}
            disabled={disabled}
            className={FIELD_CLASSES}
          >
            <option value="not_provided">Not provided</option>
            <option value="known_contact">Known contact</option>
            <option value="unknown_contact">Unknown contact</option>
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted" htmlFor="transaction-type-select">
            Transaction Type
          </label>
          <select
            id="transaction-type-select"
            value={value.transaction_type}
            onChange={handleTransactionChange}
            disabled={disabled}
            className={FIELD_CLASSES}
          >
            <option value="not_provided">Not provided</option>
            <option value="fund_transfer">Fund transfer</option>
            <option value="otp_or_pin_request">OTP or PIN request</option>
            <option value="account_update">Account update</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {value.transaction_type === "fund_transfer" && (
        <div className="animate-fade-in-down">
          <label className="mb-1.5 block text-xs font-medium text-muted" htmlFor="transaction-amount-input">
            Transfer Amount (₹)
          </label>
          <input
            id="transaction-amount-input"
            type="number"
            min="0"
            step="1000"
            placeholder="e.g. 10000"
            value={value.transaction_amount ?? ""}
            onChange={handleAmountChange}
            disabled={disabled}
            className={FIELD_CLASSES}
          />
        </div>
      )}

      <p className="text-xs leading-relaxed text-muted">
        Demo context only. Do not enter personal or banking details.
      </p>
    </div>
  );
}
