// Tiny local WebSocket mock server for testing useRiskSocket before the
// real backend (Shreyas's endpoint) is ready.
//
// Usage:
//   npm install --save-dev ws
//   node server.js
//
// Sends a fake RiskUpdate every 2s, rolling_risk_score climbing from
// 0.05 up to ~0.95, alert_level flipping to "medium" > 0.4 and "high" > 0.7,
// then loops back to a fresh "call".

const { WebSocketServer } = require("ws");

const PORT = 8080;
const wss = new WebSocketServer({ port: PORT });

function levelFor(score) {
  if (score > 0.7) return "high";
  if (score > 0.4) return "medium";
  return "low";
}

function flagsFor(level) {
  if (level === "high") return ["synthetic_artifact"];
  if (level === "medium") return ["prosody_anomaly"];
  return [];
}

console.log(`[mock-ws] listening on ws://localhost:${PORT}`);

wss.on("connection", (ws) => {
  console.log("[mock-ws] client connected");

  let chunkIndex = 0;
  let rolling = 0.05;

  const interval = setInterval(() => {
    // Random-walk the score upward with a bit of noise, reset after a
    // full "call" so a long-running dev session keeps producing data.
    rolling = Math.min(0.97, rolling + 0.05 + Math.random() * 0.05);
    const chunkScore = Math.min(
      1,
      Math.max(0, rolling + (Math.random() - 0.5) * 0.1)
    );
    const level = levelFor(rolling);

    const message = {
      chunk_id: `chunk_${String(++chunkIndex).padStart(3, "0")}`,
      timestamp: new Date().toISOString(),
      chunk_score: Number(chunkScore.toFixed(2)),
      rolling_risk_score: Number(rolling.toFixed(2)),
      confidence: Number(Math.min(0.98, 0.6 + chunkIndex * 0.02).toFixed(2)),
      flags: flagsFor(level),
      alert_level: level,
    };

    ws.send(JSON.stringify(message));

    if (rolling >= 0.97) {
      // "Call" ended — start a new one after a short pause.
      rolling = 0.05;
      chunkIndex = 0;
    }
  }, 2000);

  ws.on("close", () => {
    console.log("[mock-ws] client disconnected");
    clearInterval(interval);
  });

  ws.on("error", (err) => {
    console.error("[mock-ws] socket error", err);
  });
});
