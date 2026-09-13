import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import AlertBanner from "@/components/AlertBanner";

describe("AlertBanner — Day 4 spec", () => {
  beforeEach(() => cleanup());

  it("shows the amber 'monitor closely' strip on medium", () => {
    render(<AlertBanner alertLevel="medium" flags={["prosody_anomaly"]} />);
    expect(
      screen.getByText("Elevated risk — monitor closely")
    ).toBeInTheDocument();
    expect(screen.getByText(/prosody_anomaly/)).toBeInTheDocument();
    // No verification CTA at medium.
    expect(
      screen.queryByText("Trigger secondary verification")
    ).not.toBeInTheDocument();
  });

  it("shows the red strip + CTA on high, and CTA logs to console", () => {
    const logSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    render(<AlertBanner alertLevel="high" flags={["synthetic_artifact"]} />);

    expect(
      screen.getByText("High risk detected — recommend secondary verification")
    ).toBeInTheDocument();

    const button = screen.getByText("Trigger secondary verification");
    fireEvent.click(button);
    expect(logSpy).toHaveBeenCalledWith("Secondary verification triggered");

    logSpy.mockRestore();
  });

  it("applies the fade-in animation class when a medium/high banner appears", () => {
    const { container } = render(<AlertBanner alertLevel="medium" />);
    const banner = container.querySelector(".animate-banner-in");
    expect(banner).not.toBeNull();
  });

  it("shows the neutral 'no irregularities' state at low with no animation/CTA", () => {
    const { container } = render(<AlertBanner alertLevel="low" />);
    expect(
      screen.getByText("No irregularities detected in this call.")
    ).toBeInTheDocument();
    expect(container.querySelector(".animate-banner-in")).toBeNull();
  });
});
