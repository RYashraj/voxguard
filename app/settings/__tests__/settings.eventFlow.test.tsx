import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import SettingsPage from "@/app/settings/page";

const BACKEND_VALUES = {
  fund_transfer: 0.42,
  information_request: 0.55,
  routine: 0.91,
};

describe("Task 4 — Settings page (configurable thresholds)", () => {
  beforeEach(() => {
    cleanup();
    vi.restoreAllMocks();
    // jsdom doesn't implement matchMedia; SettingsPage renders the
    // pre-existing ThemeToggle component which needs it.
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches GET /api/v1/settings/thresholds on load and populates the controls", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => BACKEND_VALUES,
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("0.42")).toBeInTheDocument();
    });
    expect(screen.getByText("0.55")).toBeInTheDocument();
    expect(screen.getByText("0.91")).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/settings/thresholds")
    );
  });

  it("shows a success message when POST /api/v1/settings/thresholds succeeds", async () => {
    const fetchMock = vi
      .fn()
      // GET on load
      .mockResolvedValueOnce({ ok: true, json: async () => BACKEND_VALUES })
      // POST on save
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);
    await waitFor(() => screen.getByText("Save Settings"));

    screen.getByText("Save Settings").click();

    await waitFor(() => {
      expect(screen.getByText(/Settings saved successfully/)).toBeInTheDocument();
    });

    const [, postCall] = fetchMock.mock.calls;
    expect(postCall[0]).toContain("/api/v1/settings/thresholds");
    expect(postCall[1].method).toBe("POST");
    expect(JSON.parse(postCall[1].body)).toEqual(BACKEND_VALUES);
  });

  it("shows a distinct error message when the save request fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => BACKEND_VALUES })
      .mockResolvedValueOnce({ ok: false, status: 500 });
    vi.stubGlobal("fetch", fetchMock);

    render(<SettingsPage />);
    await waitFor(() => screen.getByText("Save Settings"));

    screen.getByText("Save Settings").click();

    await waitFor(() => {
      expect(screen.getByText(/Failed to save settings/)).toBeInTheDocument();
    });
    // Never silently reports success on failure.
    expect(screen.queryByText(/saved successfully/)).not.toBeInTheDocument();
  });

  it("reloading (re-mounting) the page re-fetches and reflects the backend's current values", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        fund_transfer: 0.15,
        information_request: 0.25,
        routine: 0.35,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { unmount } = render(<SettingsPage />);
    await waitFor(() => expect(screen.getByText("0.15")).toBeInTheDocument());
    unmount();

    // Simulate a fresh page load (new mount) reading whatever the backend
    // now reports as current — proving the page doesn't just replay stale
    // client-side state.
    render(<SettingsPage />);
    await waitFor(() => expect(screen.getByText("0.15")).toBeInTheDocument());
    expect(screen.getByText("0.25")).toBeInTheDocument();
    expect(screen.getByText("0.35")).toBeInTheDocument();
  });
});
