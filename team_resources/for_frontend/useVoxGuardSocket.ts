/**
 * React / Next.js Hook for VoxGuard WebSocket Live Streaming
 * Drop this file directly into your frontend `hooks/` directory.
 */
import { useEffect, useState, useCallback, useRef } from "react";
import type { RiskUpdate, AlertLevel, WebSocketHandshake } from "./types";

export interface UseVoxGuardSocketOptions {
  url?: string;
  autoReconnect?: boolean;
  reconnectIntervalMs?: number;
}

export function useVoxGuardSocket(options: UseVoxGuardSocketOptions = {}) {
  const {
    url = "ws://localhost:8000/ws/session",
    autoReconnect = true,
    reconnectIntervalMs = 3000,
  } = options;

  const [latestData, setLatestData] = useState<RiskUpdate | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [history, setHistory] = useState<RiskUpdate[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentAlertLevel, setCurrentAlertLevel] = useState<AlertLevel>("low");

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log("[VoxGuard] WebSocket connected:", url);
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log("[VoxGuard] WebSocket disconnected.");
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(connect, reconnectIntervalMs);
        }
      };

      ws.onerror = (err) => {
        console.error("[VoxGuard] WebSocket error:", err);
        ws.close();
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          // Check for initial handshake message
          if (payload.event === "connected") {
            const handshake = payload as WebSocketHandshake;
            setSessionId(handshake.session_id);
            return;
          }

          // Process real-time RiskUpdate message
          const update = payload as RiskUpdate;
          setLatestData(update);
          setCurrentAlertLevel(update.alert_level);
          setHistory((prev) => [update, ...prev]);
        } catch (parseError) {
          console.error("[VoxGuard] Failed to parse WebSocket message:", parseError);
        }
      };
    } catch (err) {
      console.error("[VoxGuard] Failed to establish WebSocket connection:", err);
    }
  }, [url, autoReconnect, reconnectIntervalMs]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  const clearHistory = useCallback(() => {
    setHistory([]);
    setLatestData(null);
    setCurrentAlertLevel("low");
  }, []);

  return {
    latestData,
    isConnected,
    history,
    sessionId,
    currentAlertLevel,
    isHighRiskLocked: currentAlertLevel === "high",
    clearHistory,
  };
}
