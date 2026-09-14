/**
 * VoxGuard Frontend TypeScript Definitions
 * Shared types for WebSocket messages, REST API requests, and SQLite audit history.
 */

export type AlertLevel = "low" | "medium" | "high";

export type SimulationScenario = "gradual_escalation" | "clean" | "suspicious";

/**
 * Real-time message streamed over WebSocket (ws://localhost:8000/ws/session)
 * for every processed audio chunk.
 */
export interface RiskUpdate {
  chunk_id: string;             // e.g. "chunk_001"
  timestamp: string;            // ISO-8601 UTC timestamp
  chunk_score: number;          // 0.00 to 1.00 (Risk score of current 3s slice)
  rolling_risk_score: number;   // 0.00 to 1.00 (5-chunk weighted rolling average)
  confidence: number;           // 0.00 to 1.00 (Detection confidence)
  flags: string[];              // e.g. ["synthetic_artifact", "prosody_flatness"]
  alert_level: AlertLevel;      // "low" (<0.4), "medium" (0.4-0.7), "high" (>0.7)
}

/**
 * WebSocket initial connection handshake event payload
 */
export interface WebSocketHandshake {
  event: "connected";
  message: string;
  session_id: string;
}

/**
 * Request payload for POST /start-simulation (or /api/simulation/start)
 */
export interface SimulationRequest {
  file_path?: string;
  chunk_duration_sec?: number;  // Default: 3.0
  delay_sec?: number;           // Default: 3.0
  scenario?: SimulationScenario;// Default: "gradual_escalation"
}

/**
 * Response payload for POST /start-simulation and POST /stop-simulation
 */
export interface SimulationResponse {
  status: "started" | "stopped" | "error";
  message: string;
  session_id?: string;
}

/**
 * Summary metrics for a call session
 */
export interface SessionStats {
  session_id: string;
  total_chunks: number;
  avg_latency_ms: number;
  peak_risk_score: number;
  final_alert_level: AlertLevel | "none";
  flags_triggered: string[];
  start_time: string;
  end_time: string;
}

/**
 * Individual chunk record retrieved from SQLite audit logs
 */
export interface PersistedChunkRecord {
  id?: number;
  session_id: string;
  chunk_id: string;
  timestamp: string;
  chunk_score: number;
  rolling_risk_score: number;
  confidence: number;
  flags: string[];
  alert_level: AlertLevel;
  inference_latency_ms: number;
}

/**
 * Response payload for GET /sessions/{session_id}/history
 */
export interface SessionHistoryResponse {
  session_id: string;
  total_chunks: number;
  stats: SessionStats;
  history: PersistedChunkRecord[];
}

/**
 * Response payload for GET /sessions
 */
export interface SessionsListResponse {
  total_sessions: number;
  sessions: SessionStats[];
}

/**
 * Health check response for GET /health
 */
export interface HealthResponse {
  status: "ok";
}
