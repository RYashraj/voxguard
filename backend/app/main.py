import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.models.schemas import (
    RiskUpdate,
    HealthResponse,
    SimulationRequest,
    SimulationResponse,
    Contact,
    ContactsResponse,
)
from app.services.websocket_manager import ws_manager
from app.services.simulator import sim_runner, simulate_call
from app.utils.audio_generator import ensure_default_sample_audio
from app.db.session_logger import (
    init_db_async,
    get_session_history_async,
    get_session_stats_async,
    list_all_sessions_async,
    log_chunk_record_async,
)
from app.ml.analyzer import analyze_chunk_raw_dispatch
from app.core.aggregator import RollingRiskAggregator
from datetime import datetime, timezone
import time
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("voxguard-backend")

# Mock enrolled contacts for voice caller identification
MOCK_CONTACTS = [
    Contact(
        id="contact_001",
        name="Rajesh Sharma",
        role="Chief Financial Officer (CFO)",
        phone_number="+91 98765 43210",
        enrolled=True,
        risk_profile="low"
    ),
    Contact(
        id="contact_002",
        name="Priya Patel",
        role="Director of Information Technology",
        phone_number="+91 98123 45678",
        enrolled=True,
        risk_profile="low"
    ),
    Contact(
        id="contact_003",
        name="Vikram Malhotra",
        role="Chief Executive Officer (CEO)",
        phone_number="+91 98989 12345",
        enrolled=True,
        risk_profile="low"
    ),
    Contact(
        id="contact_004",
        name="Ananya Iyer",
        role="Senior Finance Controller",
        phone_number="+91 97654 32109",
        enrolled=True,
        risk_profile="low"
    ),
    Contact(
        id="contact_005",
        name="Sameer Deshmukh",
        role="Head of Treasury Operations",
        phone_number="+91 99887 76655",
        enrolled=True,
        risk_profile="low"
    ),
    Contact(
        id="unknown",
        name="Unknown / External Caller",
        role="Unenrolled External Line",
        phone_number="+91 91234 56789",
        enrolled=False,
        risk_profile="high"
    ),
]


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
        db_ok = await init_db_async()
        if db_ok:
            logger.info("SQLite session database ready.")
        else:
            logger.warning("SQLite DB startup initialization failed. Session history logging may be unavailable.")
    except Exception as e:
        logger.error(f"SQLite DB startup initialization error: {e}")

    try:
        from app.ml.ml_model import get_detector
        logger.info("Pre-loading SpectraAASISTDetector ML model weights...")
        get_detector()
        logger.info("ML model weights pre-loaded successfully.")
    except Exception as e:
        logger.error(f"ML model preload failed: {e}")

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

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning(f"Malformed input (ValueError): {exc}")
    return JSONResponse(status_code=400, content={"detail": "Invalid Input", "message": str(exc)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "message": str(exc)})


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
@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """Health check endpoint. Returns 200 with status ok."""
    return HealthResponse(status="ok")


@app.get("/api/v1/contacts", response_model=ContactsResponse, tags=["Contacts"])
@app.get("/contacts", response_model=ContactsResponse, tags=["Contacts"])
async def get_contacts_endpoint():
    """
    Returns list of enrolled executive and staff contacts for caller identification dropdown.
    """
    return ContactsResponse(
        total_contacts=len(MOCK_CONTACTS),
        contacts=MOCK_CONTACTS
    )


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


@app.get("/sessions", tags=["History"])
@app.get("/api/sessions", tags=["History"])
@app.get("/api/v1/sessions", tags=["History"])
async def list_sessions_endpoint():
    """
    Lists all past call sessions stored in the SQLite database with high-level summaries and metrics.
    """
    sessions = await list_all_sessions_async()
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@app.get("/sessions/{session_id}", tags=["History"])
@app.get("/sessions/{session_id}/history", tags=["History"])
@app.get("/api/sessions/{session_id}/history", tags=["History"])
@app.get("/api/v1/session/{session_id}/history", tags=["History"])
@app.get("/api/v1/sessions/{session_id}/history", tags=["History"])
async def get_session_history_endpoint(session_id: str):
    """
    Returns the full chronological chunk history and summary statistics for a specific call session.
    """
    history = await get_session_history_async(session_id)
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for session '{session_id}'"
        )
    stats = await get_session_stats_async(session_id)
    return {
        "session_id": session_id,
        "total_chunks": len(history),
        "stats": stats,
        "history": history
    }


@app.websocket("/ws/session")
@app.websocket("/ws/session/{session_id}")
@app.websocket("/api/v1/ws/session")
async def websocket_session_endpoint(websocket: WebSocket, session_id: Optional[str] = None, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time live streaming of audio chunk risk updates.
    Accepts raw binary PCM audio frames from browser MediaRecorder.
    """
    expected_token = os.getenv("VOXGUARD_WS_TOKEN")
    if expected_token and token != expected_token:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await ws_manager.connect(websocket)
    session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    # Initialize a new Risk Aggregator specifically for this live session
    aggregator = RollingRiskAggregator(window_size=5, low_threshold=0.4, high_threshold=0.7)
    step_counter = 0

    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to VoxGuard real-time stream",
            "session_id": session_id
        })
        while True:
            message = await websocket.receive()
            if "text" in message:
                data = message["text"]
                logger.debug(f"Received client message: {data}")
            elif "bytes" in message:
                pcm_bytes = message["bytes"]
                step_counter += 1
                
                t0 = time.perf_counter()
                analysis = await analyze_chunk_raw_dispatch(
                    pcm_bytes=pcm_bytes,
                    step=step_counter,
                    scenario="live_mic"
                )
                t1 = time.perf_counter()
                inference_latency_ms = round((t1 - t0) * 1000.0, 2)
                
                update = aggregator.create_risk_update(
                    chunk_id=f"chunk_{step_counter:03d}",
                    chunk_score=analysis.get("chunk_score", 0.5),
                    confidence=analysis.get("confidence", 0.0),
                    flags=analysis.get("flags", []),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    prosody_score=analysis.get("prosody_score"),
                    identity_drift=analysis.get("identity_drift")
                )
                
                try:
                    await log_chunk_record_async(
                        session_id=session_id,
                        chunk_id=update.chunk_id,
                        timestamp=update.timestamp,
                        chunk_score=update.chunk_score,
                        rolling_risk_score=update.rolling_risk_score,
                        confidence=update.confidence,
                        flags=update.flags,
                        alert_level=update.alert_level,
                        inference_latency_ms=inference_latency_ms
                    )
                except Exception as e:
                    logger.error(f"Database log error (continuing stream): {e}")

                # Broadcast risk update back to the sender
                await websocket.send_json(update.model_dump())

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket session.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)



@app.post("/start-simulation", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/simulation/start", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/v1/session/start", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/v1/simulation/start", response_model=SimulationResponse, tags=["Simulator"])
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
            message=f"Simulation running for scenario '{req.scenario}' at {req.delay_sec}s interval (Caller: {req.caller_id}, Context: {req.transaction_context})",
            session_id=session_id,
            caller_id=req.caller_id,
            transaction_context=req.transaction_context
        )
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-simulation", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/simulation/stop", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/v1/session/stop", response_model=SimulationResponse, tags=["Simulator"])
@app.post("/api/v1/simulation/stop", response_model=SimulationResponse, tags=["Simulator"])
async def stop_simulation_endpoint():
    """Stops any currently active call simulation."""
    session_id = sim_runner.session_id or "none"
    sim_runner.stop()
    return SimulationResponse(
        status="stopped",
        message="Simulation stopped successfully",
        session_id=session_id
    )

