import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import TransparencyPage from "@/app/transparency/page";
import transparencyData from "@/data/transparency.json";

function stubMatchMedia() {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: () => ({
      matches: false,
      media: "",
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

describe("Task 5 — Model Transparency page", () => {
  beforeEach(() => {
    cleanup();
    stubMatchMedia();
  });

  it("renders the three required columns", () => {
    render(<TransparencyPage />);
    expect(screen.getByText("Accent/Language")).toBeInTheDocument();
    expect(screen.getByText("Detection Accuracy (%)")).toBeInTheDocument();
    expect(screen.getByText("Sample Size")).toBeInTheDocument();
  });

  it("renders a row per entry in data/transparency.json, matching that file exactly", () => {
    render(<TransparencyPage />);
    for (const row of transparencyData) {
      expect(screen.getByText(row.accent_language)).toBeInTheDocument();
      expect(screen.getByText(`${row.accuracy}%`)).toBeInTheDocument();
    }
  });

  it("clearly marks the data as placeholder/test data", () => {
    render(<TransparencyPage />);
    expect(screen.getByText(/Placeholder \/ Test Data/)).toBeInTheDocument();
    expect(
      screen.getByText(/have not been produced by a real model evaluation/)
    ).toBeInTheDocument();
  });

  it("does not claim the numbers are a verified/empirical benchmark", () => {
    render(<TransparencyPage />);
    expect(screen.queryByText(/Verified Benchmark/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Empirical evaluation/)).not.toBeInTheDocument();
  });
});
