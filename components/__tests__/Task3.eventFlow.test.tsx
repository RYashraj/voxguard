import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import PreTransactionModal from "@/components/PreTransactionModal";
import AlertToast from "@/components/AlertToast";

describe("Task 3 — Pre-transaction warning modal", () => {
  beforeEach(() => cleanup());

  it("renders recommended_actions dynamically, not a hardcoded set of three", () => {
    const onActionSelect = vi.fn();
    render(
      <PreTransactionModal
        isOpen={true}
        reason="High impersonation risk before fund transfer"
        recommendedActions={["Call-back Verification", "MFA", "Escalate to Supervisor", "Freeze Session"]}
        onActionSelect={onActionSelect}
      />
    );

    expect(screen.getByText("Call-back Verification")).toBeInTheDocument();
    expect(screen.getByText("MFA")).toBeInTheDocument();
    expect(screen.getByText("Escalate to Supervisor")).toBeInTheDocument();
    // A 4th backend-provided action also renders — proves it's dynamic.
    expect(screen.getByText("Freeze Session")).toBeInTheDocument();
  });

  it("logs the selected action and closes via onActionSelect, with no fake API call", async () => {
    vi.useFakeTimers();
    const logSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    const onActionSelect = vi.fn();

    render(
      <PreTransactionModal
        isOpen={true}
        recommendedActions={["Call-back Verification", "MFA", "Escalate to Supervisor"]}
        onActionSelect={onActionSelect}
      />
    );

    fireEvent.click(screen.getByText("MFA"));
    expect(logSpy).toHaveBeenCalledWith(expect.stringContaining("MFA"));

    vi.advanceTimersByTime(300);
    expect(onActionSelect).toHaveBeenCalledWith("MFA");

    logSpy.mockRestore();
    vi.useRealTimers();
  });

  it("is not dismissible without selecting an action (no backdrop-close control)", () => {
    const { container } = render(
      <PreTransactionModal
        isOpen={true}
        recommendedActions={["Call-back Verification", "MFA", "Escalate to Supervisor"]}
        onActionSelect={vi.fn()}
      />
    );
    // No close/dismiss button anywhere in the modal.
    expect(container.querySelector("button[aria-label='close']")).toBeNull();
    expect(screen.queryByText("✕")).not.toBeInTheDocument();
  });
});

describe("Task 3 — In-app high-alert toast", () => {
  beforeEach(() => cleanup());

  it("fires once when alert_level transitions to high", () => {
    const { rerender } = render(
      <AlertToast alertLevel="low" chunkId="chunk_1" flags={[]} />
    );
    expect(
      screen.queryByText("High Threat In-App Toast")
    ).not.toBeInTheDocument();

    rerender(<AlertToast alertLevel="high" chunkId="chunk_2" flags={["synthetic_artifact"]} />);
    expect(screen.getByText("High Threat In-App Toast")).toBeInTheDocument();
  });

  it("does not spam a new toast on every WS update while alert_level stays high", () => {
    const { rerender } = render(
      <AlertToast alertLevel="high" chunkId="chunk_1" flags={[]} />
    );
    expect(screen.getByText(/chunk_1/)).toBeInTheDocument();

    // Simulate several more high-alert WS updates with new chunk ids —
    // the toast should keep showing the original chunk, not retrigger.
    rerender(<AlertToast alertLevel="high" chunkId="chunk_2" flags={[]} />);
    rerender(<AlertToast alertLevel="high" chunkId="chunk_3" flags={[]} />);
    rerender(<AlertToast alertLevel="high" chunkId="chunk_4" flags={[]} />);

    expect(screen.getByText(/chunk_1/)).toBeInTheDocument();
    expect(screen.queryByText(/chunk_4/)).not.toBeInTheDocument();
  });

  it("fires again on a fresh low/medium -> high transition", () => {
    const { rerender } = render(
      <AlertToast alertLevel="high" chunkId="chunk_1" flags={[]} />
    );
    expect(screen.getByText(/chunk_1/)).toBeInTheDocument();

    rerender(<AlertToast alertLevel="medium" chunkId="chunk_2" flags={[]} />);
    rerender(<AlertToast alertLevel="high" chunkId="chunk_3" flags={[]} />);

    expect(screen.getByText(/chunk_3/)).toBeInTheDocument();
  });
});
