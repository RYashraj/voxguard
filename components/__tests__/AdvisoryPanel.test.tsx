import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import AdvisoryPanel from "@/components/AdvisoryPanel";
import { RiskAdvisory } from "@/types/risk";

describe("AdvisoryPanel — Contextual Warning Integration", () => {
  beforeEach(() => cleanup());

  it("renders neutral state when advisory is absent / null", () => {
    render(<AdvisoryPanel advisory={null} />);
    expect(screen.getByText("Waiting for live risk assessment…")).toBeInTheDocument();
  });

  it("renders continue_with_caution calm teal state", () => {
    const advisory: RiskAdvisory = {
      recommendation: "continue_with_caution",
      reason_codes: ["normal_call_flow"],
      user_message: "No acoustic voice-cloning artifacts detected.",
      requires_user_confirmation: false,
    };

    render(<AdvisoryPanel advisory={advisory} />);
    expect(screen.getByText("Continue carefully")).toBeInTheDocument();
    expect(
      screen.getByText("No acoustic voice-cloning artifacts detected.")
    ).toBeInTheDocument();
    expect(screen.getByText("No contextual warning")).toBeInTheDocument();
  });

  it("renders pause_and_verify amber state with 'I verified independently' button", () => {
    const advisory: RiskAdvisory = {
      recommendation: "pause_and_verify",
      reason_codes: ["unknown_caller", "sensitive_credential_request"],
      user_message: "Unverified caller requesting OTP/PIN. Do not share credentials over phone.",
      requires_user_confirmation: true,
    };

    render(<AdvisoryPanel advisory={advisory} />);
    expect(screen.getByText("Pause & Verify")).toBeInTheDocument();
    expect(
      screen.getByText("Unverified caller requesting OTP/PIN. Do not share credentials over phone.")
    ).toBeInTheDocument();
    expect(screen.getByText("Caller is not verified")).toBeInTheDocument();
    expect(screen.getByText("Sensitive credential request")).toBeInTheDocument();

    const verifyBtn = screen.getByText("I verified independently");
    expect(verifyBtn).toBeInTheDocument();

    fireEvent.click(verifyBtn);
    expect(
      screen.getByText("✓ Verified independently (demo acknowledgement only)")
    ).toBeInTheDocument();
  });

  it("renders block_and_report red state with disabled approval and working stop call action", () => {
    const stopCallSpy = vi.fn();
    const advisory: RiskAdvisory = {
      recommendation: "block_and_report",
      reason_codes: ["high_acoustic_spoof_risk"],
      user_message:
        "High voice-cloning risk detected. Do not approve this transaction; verify through an official channel.",
      requires_user_confirmation: true,
    };

    render(<AdvisoryPanel advisory={advisory} onStopCall={stopCallSpy} />);

    expect(screen.getByText("Block & Report")).toBeInTheDocument();
    expect(screen.getByText("High voice-cloning risk")).toBeInTheDocument();

    const approveBtn = screen.getByText("Approve Transaction (Blocked)") as HTMLButtonElement;
    expect(approveBtn).toBeDisabled();

    const endCallBtn = screen.getByText("End call / verify through official channel");
    expect(endCallBtn).toBeInTheDocument();

    fireEvent.click(endCallBtn);
    expect(stopCallSpy).toHaveBeenCalledTimes(1);
  });
});
