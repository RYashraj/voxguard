"use client";

import { SimulationContext, CallerContext, TransactionType } from "@/types/risk";

interface CallContextInputProps {
  value: SimulationContext;
  onChange: (context: SimulationContext) => void;
  disabled?: boolean;
}

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
    <div className="rounded-xl border border-border bg-surface p-4 text-xs text-foreground space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-sm text-foreground">Call Context</h2>
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted">
          Simulator advisory input
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="block mb-1 font-medium text-muted" htmlFor="caller-context-select">
            Caller Status
          </label>
          <select
            id="caller-context-select"
            value={value.caller_context}
            onChange={handleCallerChange}
            disabled={disabled}
            className="w-full rounded-lg border border-border bg-background px-3 py-1.5 font-sans text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-signal disabled:opacity-50"
          >
            <option value="not_provided">Not provided</option>
            <option value="known_contact">Known contact</option>
            <option value="unknown_contact">Unknown contact</option>
          </select>
        </div>

        <div>
          <label className="block mb-1 font-medium text-muted" htmlFor="transaction-type-select">
            Transaction Type
          </label>
          <select
            id="transaction-type-select"
            value={value.transaction_type}
            onChange={handleTransactionChange}
            disabled={disabled}
            className="w-full rounded-lg border border-border bg-background px-3 py-1.5 font-sans text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-signal disabled:opacity-50"
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
        <div>
          <label className="block mb-1 font-medium text-muted" htmlFor="transaction-amount-input">
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
            className="w-full rounded-lg border border-border bg-background px-3 py-1.5 font-sans text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-signal disabled:opacity-50"
          />
        </div>
      )}

      <p className="font-mono text-[10px] text-muted text-pretty">
        Demo context only. Do not enter personal or banking details.
      </p>
    </div>
  );
}
