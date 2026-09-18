import json
import logging
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.models.schemas import (
    RiskUpdate,
    HealthResponse,
    SimulationRequest,
    SimulationResponse,
    SimulationContext,
)
from app.core.aggregator import RollingRiskAggregator
from app.ml.analyzer import analyze_chunk_dispatch
from app.services.context_policy import evaluate_advisory_policy
from app.ml.speaker_verification import SessionIdentityTracker
from app.services.websocket_manager import ws_manager
from app.services.simulator import sim_runner, simulate_call
from app.services.session_context_manager import session_context_mgr
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
        db_ok = await init_db_async()
        if db_ok:
            logger.info("SQLite session database ready.")
        else:
            logger.warning("SQLite DB startup initialization failed. Session history logging may be unavailable.")
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
CLONE_DEMO_HTML_PATH = Path(__file__).parent / "templates" / "clone_demo.html"
BACKEND_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEMO_AUDIO_FILES = {
    "gradual": BACKEND_DATA_DIR / "sample_calls" / "gradual_escalation.wav",
    "otp": BACKEND_DATA_DIR / "sample_calls" / "demo_call.wav",
    "deepfake": BACKEND_DATA_DIR / "test_audio" / "asvspoof_spoof_clips" / "LA_E_5932896.wav",
    "genuine": BACKEND_DATA_DIR / "sample_calls" / "demo_call.wav",
}
IDENTITY_DEMO_DIR = BACKEND_DATA_DIR / "consented_reference_audio" / "identity_demo"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo", response_class=HTMLResponse, tags=["Demo"])
async def get_demo_dashboard():
    """
    Serves the live interactive VoxGuard real-time streaming dashboard for video recordings and team demos.
    """
    if DEMO_HTML_PATH.exists():
        return HTMLResponse(content=DEMO_HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>VoxGuard Backend Live</h1><p>Visit /docs for API documentation</p>")


@app.get("/audio/{sample_name}", response_class=FileResponse, tags=["Demo"])
async def get_demo_audio(sample_name: str):
    """Serves only allowlisted demo WAV files to the browser audio player."""
    audio_path = DEMO_AUDIO_FILES.get(sample_name)
    if not audio_path or not audio_path.exists():
        raise HTTPException(status_code=404, detail="Demo audio sample not found")
    return FileResponse(audio_path, media_type="audio/wav", filename=audio_path.name)


@app.get("/clone-demo", response_class=HTMLResponse, tags=["Demo"])
async def get_clone_demo_dashboard():
    """
    Serves the live Voice Clone Detection Demo page for SIH26104 evaluation.
    Shows real-time contrast: live human mic (GREEN) vs ElevenLabs cloned voice (RED).
    """
    if CLONE_DEMO_HTML_PATH.exists():
        return HTMLResponse(content=CLONE_DEMO_HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Clone Demo not found — ensure clone_demo.html exists in templates/</h1>")


@app.get("/identity-demo/audio/{audio_type}/{filename}", tags=["Identity Demo"])
async def serve_identity_demo_audio(audio_type: str, filename: str):
    """
    Serves a WAV file from the identity_demo folder for browser audio playback.
    audio_type must be 'original' or 'clone'.
    """
    if audio_type not in ("original", "clone"):
        raise HTTPException(status_code=400, detail="audio_type must be 'original' or 'clone'")
    audio_path = IDENTITY_DEMO_DIR / audio_type / filename
    if not audio_path.exists() or not audio_path.is_file():
        raise HTTPException(status_code=404, detail=f"Audio file '{filename}' not found in {audio_type}/")
    try:
        audio_path.relative_to(IDENTITY_DEMO_DIR)
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden: path traversal detected")
    return FileResponse(str(audio_path), media_type="audio/wav", filename=filename)


@app.get("/identity-demo/files", tags=["Identity Demo"])
async def list_identity_demo_files():
    """Lists all available original and clone WAV files for the clone demo page."""
    original_files = sorted([f.name for f in (IDENTITY_DEMO_DIR / "original").glob("*.wav")])
    clone_files = sorted([f.name for f in (IDENTITY_DEMO_DIR / "clone").glob("*.wav")])
    return {"original": original_files, "clone": clone_files}


@app.get("/identity-demo/compare", tags=["Identity Demo"])
async def compare_identity_demo():
    """Compare the first consented original reference with the first consented clone sample."""
    original_files = sorted((IDENTITY_DEMO_DIR / "original").glob("*.wav"))
    clone_files = sorted((IDENTITY_DEMO_DIR / "clone").glob("*.wav"))
    if not original_files or not clone_files:
        raise HTTPException(status_code=404, detail="Consented original/clone WAV pair not found")

    tracker = SessionIdentityTracker(session_id="identity_demo")
    try:
        enrolled = tracker.enroll_reference_path(str(original_files[0]))
        if enrolled.get("status") != "ok":
            return {
                "status": enrolled.get("status", "identity_unavailable"),
                "message": enrolled.get("message", "Reference enrollment unavailable"),
                "original_file": original_files[0].name,
                "clone_file": clone_files[0].name,
            }
        with open(clone_files[0], "rb") as clone_audio:
            result = tracker.verify_chunk(clone_audio.read())
        return {
            "status": result["status"],
            "original_file": original_files[0].name,
            "clone_file": clone_files[0].name,
            "speaker_similarity": result["speaker_similarity"],
            "identity_drift": result["identity_drift"],
            "confidence": result["confidence"],
            "flags": result["flags"],
            "identity_mismatch": "identity_mismatch" in result["flags"],
        }
    finally:
        tracker.clear()


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


@app.post("/sessions/{session_id}/context", tags=["Context"])
@app.post("/api/sessions/{session_id}/context", tags=["Context"])
async def update_session_context_endpoint(session_id: str, context: SimulationContext):
    """
    Updates in-memory call/transaction context for an active demo session.
    Context is stored ONLY in memory for the active demo session and is NEVER written to SQLite.
    Returns 404 if session_id is not active or unknown.
    """
    updated = session_context_mgr.set_context(session_id, context)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found or inactive."
        )
    return {
        "session_id": session_id,
        "status": "updated",
        "context": context
    }


@app.get("/sessions/{session_id}/context", tags=["Context"])
@app.get("/api/sessions/{session_id}/context", tags=["Context"])
async def get_session_context_endpoint(session_id: str):
    """
    Retrieves in-memory call/transaction context for an active demo session.
    Returns 404 if session_id is not active or unknown.
    """
    context = session_context_mgr.get_context(session_id)
    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found or inactive."
        )
    return {
        "session_id": session_id,
        "context": context
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


@app.websocket("/ws/live")
async def websocket_live_microphone_endpoint(websocket: WebSocket):
    """Accepts browser microphone PCM WAV chunks and returns live risk updates."""
    await websocket.accept()
    aggregator = RollingRiskAggregator(window_size=5, low_threshold=0.4, high_threshold=0.7)
    context = SimulationContext(caller_context="unknown_contact", transaction_type="otp_or_pin_request")
    chunk_number = 0

    try:
        await websocket.send_json({"event": "connected", "message": "Live microphone stream ready"})
        while True:
            message = await websocket.receive()
            if message.get("text"):
                data = json.loads(message["text"])
                if data.get("type") == "context":
                    context = SimulationContext(**data.get("context", {}))
                continue
            audio_bytes = message.get("bytes")
            if not audio_bytes:
                continue
            chunk_number += 1
            analysis = await analyze_chunk_dispatch(audio_bytes, step=chunk_number, scenario="gradual_escalation")
            update = aggregator.create_risk_update(
                chunk_id=f"mic_{chunk_number:03d}",
                chunk_score=analysis["chunk_score"],
                confidence=analysis["confidence"],
                flags=analysis["flags"],
            )
            payload = update.model_dump()
            payload["advisory"] = evaluate_advisory_policy(
                update.rolling_risk_score, update.alert_level, context
            ).model_dump()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        logger.info("Live microphone client disconnected.")
    except Exception as exc:
        logger.warning("Live microphone stream ended safely: %s", type(exc).__name__)


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
            scenario=req.scenario,
            reference_audio_path=req.reference_audio_path,
            context=req.context
        )
        return SimulationResponse(
            status="started",
            message=f"Simulation running for scenario '{req.scenario}' at {req.delay_sec}s interval",
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start simulation.")


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

