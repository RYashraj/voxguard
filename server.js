const http = require("http");
const { WebSocketServer } = require("ws");

const PORT = process.env.PORT || 8000;

const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === "/start-simulation" && req.method === "POST") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", message: "simulation started" }));
    return;
  }

  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "healthy" }));
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Not found" }));
});

const wss = new WebSocketServer({ server });

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

wss.on("connection", (ws, req) => {
  console.log(`[mock-ws] client connected on ${req.url}`);

  // Send handshake message as real backend does
  ws.send(JSON.stringify({ event: "connected", session_id: "mock-session-001" }));

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

    if (ws.readyState === ws.OPEN) {
      ws.send(JSON.stringify(message));
    }

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

server.listen(PORT, () => {
  console.log(`[mock-server] listening on http://localhost:${PORT} and ws://localhost:${PORT}`);
});

