"use client";

import { RiskAdvisory } from "@/types/risk";

interface ResponsePlanProps {
  advisory?: RiskAdvisory | null;
}

const ACTIONS = [
  ["1", "End call", "Stop the conversation and do not share the OTP or PIN."],
  ["2", "Call back independently", "Use a trusted number or official banking app, never the caller's number."],
  ["3", "Escalate to a senior", "Route the incident to a supervisor or fraud-response team."],
];

export default function ResponsePlan({ advisory }: ResponsePlanProps) {
  if (advisory?.recommendation !== "block_and_report") return null;

  return (
    <section className="response-plan rounded-card border border-risk-highBorder bg-risk-highBg p-5 shadow-card" aria-label="Recommended response plan">
      <div>
        <h2 className="text-lg font-semibold text-risk-high">Recommended response</h2>
        <p className="mt-1 text-sm text-foreground">Protect the user first. Do not approve, disclose, or continue the sensitive request.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {ACTIONS.map(([step, title, description]) => (
          <div key={step} className="rounded-control border border-risk-highBorder bg-surface p-4">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-risk-high text-sm font-bold text-accent-contrast">{step}</span>
            <h3 className="mt-3 text-base font-semibold text-foreground">{title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-muted">{description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}