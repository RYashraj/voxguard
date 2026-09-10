import logging
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.models.schemas import (
    RiskUpdate,
    HealthResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.services.websocket_manager import ws_manager
from app.services.simulator import sim_runner, simulate_call
from app.utils.audio_generator import ensure_default_sample_audio
from app.db.session_logger import init_db_async, get_session_history_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("voxguard-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown events.
    Ensures default sample call WAV exists and initializes SQLite database schema.
    """
    logger.info("Initializing VoxGuard Backend...")
    try:
        sample_path = ensure_default_sample_audio()
        logger.info(f"Default demo audio ready at: {sample_path}")
    except Exception as e:
        logger.warning(f"Could not generate default audio: {e}")

    try:
        await init_db_async()
        logger.info("SQLite session database ready.")
    except Exception as e:
        logger.error(f"SQLite DB startup initialization error: {e}")

    yield
    logger.info("Shutting down VoxGuard Backend...")
    sim_runner.stop()


app = FastAPI(
    title="VoxGuard Backend API",
    description="Real-Time Voice Impersonation & Cloning Detection API (SIH26104 - Team Crackjack)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_HTML_PATH = Path(__file__).parent / "templates" / "demo.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo", response_class=HTMLResponse, tags=["Demo"])
async def get_demo_dashboard():
    """
    Serves the live interactive VoxGuard real-time streaming dashboard for video recordings and team demos.
    """
    if DEMO_HTML_PATH.exists():
        return HTMLResponse(content=DEMO_HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>VoxGuard Backend Live</h1><p>Visit /docs for API documentation</p>")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """Health check endpoint. Returns 200 with status ok."""
    return HealthResponse(status="ok")


@app.get("/contract", response_model=RiskUpdate, tags=["Contract"])
async def get_contract_example():
    """Returns an example of the strict RiskUpdate data contract agreed across ML, Backend, and Frontend."""
    return RiskUpdate(
        chunk_id="chunk_001",
        timestamp="2026-09-10T15:00:00.000000+00:00",
        chunk_score=0.12,
        rolling_risk_score=0.12,
        confidence=0.94,
        flags=["synthetic_artifact"],
        alert_level="low"
    )


@app.get("/sessions/{session_id}/history", tags=["History"])
@app.get("/api/sessions/{session_id}/history", tags=["History"])
async def get_session_history_endpoint(session_id: str):
    """
    Returns the full chronological chunk history for a specific call session.
    """
    history = await get_session_history_async(session_id)
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for session '{session_id}'"
        )
    return {
        "session_id": session_id,
        "total_chunks": len(history),
        "history": history
    }


@app.websocket("/ws/session")
@app.websocket("/ws/session/{session_id}")
async def websocket_session_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time live streaming of audio chunk risk updates.
    """
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to VoxGuard real-time stream",
            "session_id": session_id or "default"
        })
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received client message: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket session.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.post("/start-simulation", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/simulation/start", response_model=SimulationResponse, tags=["Simulator"])
async def start_simulation_endpoint(request: Optional[SimulationRequest] = None):
    """Triggers the Call Simulator to stream audio chunks in real-time over the WebSocket."""
    req = request or SimulationRequest()
    try:
        session_id = await sim_runner.start(
            file_path=req.file_path,
            chunk_duration_sec=req.chunk_duration_sec,
            delay_sec=req.delay_sec,
            scenario=req.scenario
        )
        return SimulationResponse(
            status="started",
            message=f"Simulation running for scenario '{req.scenario}' at {req.delay_sec}s interval",
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-simulation", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/simulation/stop", response_model=SimulationResponse, tags=["Simulator"])
async def stop_simulation_endpoint():
    """Stops any currently active call simulation."""
    session_id = sim_runner.session_id or "none"
    sim_runner.stop()
    return SimulationResponse(
        status="stopped",
        message="Simulation stopped successfully",
        session_id=session_id
    )
