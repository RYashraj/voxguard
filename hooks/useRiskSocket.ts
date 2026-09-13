"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { RiskUpdate } from "@/types/risk";

const RECONNECT_DELAY_MS = 2000;
const MAX_HISTORY = 20;

export type ConnectionStatus = "connecting" | "open" | "closed";

interface UseRiskSocketResult {
  latest: RiskUpdate | null;
  history: RiskUpdate[];
  status: ConnectionStatus;
}

/**
 * Connects to a WebSocket server streaming RiskUpdate JSON messages.
 * Keeps the most recent message plus a rolling history (max 20), and
 * auto-reconnects 2s after any disconnect/error.
 */
export function useRiskSocket(url: string): UseRiskSocketResult {
  const [latest, setLatest] = useState<RiskUpdate | null>(null);
  const [history, setHistory] = useState<RiskUpdate[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Tracks whether the effect has been torn down, so a pending
  // reconnect doesn't fire after unmount.
  const unmounted = useRef(false);

  const connect = useCallback(() => {
    if (unmounted.current) return;

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (unmounted.current) return;
      setStatus("open");
    };

    ws.onmessage = (event) => {
      if (unmounted.current) return;
      try {
        const parsed = JSON.parse(event.data);

        // The backend sends a non-RiskUpdate handshake message right after
        // connecting (e.g. {"event": "connected", "session_id": "..."}).
        // Only treat messages that actually match the RiskUpdate contract
        // as risk data — anything else (handshake/control messages) is
        // ignored rather than shoved into state as malformed data.
        if (
          typeof parsed?.chunk_id !== "string" ||
          typeof parsed?.rolling_risk_score !== "number" ||
          typeof parsed?.alert_level !== "string"
        ) {
          return;
        }

        const riskUpdate = parsed as RiskUpdate;
        setLatest(riskUpdate);
        setHistory((prev) => {
          const next = [...prev, riskUpdate];
          return next.length > MAX_HISTORY
            ? next.slice(next.length - MAX_HISTORY)
            : next;
        });
      } catch (err) {
        console.error("useRiskSocket: failed to parse message", err, event.data);
      }
    };

    const scheduleReconnect = () => {
      if (unmounted.current) return;
      setStatus("closed");
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onclose = scheduleReconnect;
    ws.onerror = () => {
      // onerror is typically followed by onclose, but close explicitly
      // in case the browser doesn't fire close on this kind of failure.
      ws.close();
    };
  }, [url]);

  useEffect(() => {
    unmounted.current = false;
    connect();

    return () => {
      unmounted.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { latest, history, status };
}
