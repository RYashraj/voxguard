import os
import io
import uuid
import wave
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime, timezone

from app.models.schemas import RiskUpdate
from app.core.aggregator import RollingRiskAggregator
from app.ml.stub import analyze_chunk_stub
from app.services.websocket_manager import ws_manager
from app.utils.audio_generator import ensure_default_sample_audio

logger = logging.getLogger("voxguard.simulator")

# Try importing pydub; fallback to standard wave module if needed
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


def slice_wav_file(file_path: str, chunk_duration_sec: float = 3.0) -> list[dict[str, Any]]:
    """
    Slices a WAV file into chunks of `chunk_duration_sec` seconds.
    Uses pydub if available, with built-in standard wave module fallback.
    Returns a list of chunk dicts containing chunk_id, index, raw_bytes, and duration.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at: {file_path}")

    chunks = []
    chunk_ms = int(chunk_duration_sec * 1000)

    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)
            total_len_ms = len(audio)
            
            for i, start_ms in enumerate(range(0, total_len_ms, chunk_ms)):
                end_ms = min(start_ms + chunk_ms, total_len_ms)
                # Ignore very tiny leftover trailing chunks < 0.5s unless it's the only one
                if (end_ms - start_ms < 500) and len(chunks) > 0:
                    continue

                chunk_segment = audio[start_ms:end_ms]
                buffer = io.BytesIO()
                chunk_segment.export(buffer, format="wav")
                chunk_bytes = buffer.getvalue()

                chunks.append({
                    "chunk_id": f"chunk_{i+1:03d}",
                    "index": i + 1,
                    "audio_bytes": chunk_bytes,
                    "duration_sec": (end_ms - start_ms) / 1000.0,
                    "start_time_sec": start_ms / 1000.0
                })
            return chunks
        except Exception as e:
            logger.warning(f"pydub slicing encountered an issue: {e}. Falling back to standard wave module.")

    # Fallback to standard Python wave module (for PCM WAV files)
    with wave.open(file_path, 'rb') as wav_file:
        n_channels = wav_file.getnchannels()
        sampwidth = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        frames_per_chunk = int(framerate * chunk_duration_sec)
        total_chunks = (n_frames + frames_per_chunk - 1) // frames_per_chunk
        
        for i in range(total_chunks):
            wav_file.setpos(i * frames_per_chunk)
            frames_to_read = min(frames_per_chunk, n_frames - (i * frames_per_chunk))
            if frames_to_read < int(framerate * 0.5) and i > 0:
                continue
                
            raw_frames = wav_file.readframes(frames_to_read)
            
            # Package as valid WAV
            chunk_buffer = io.BytesIO()
            with wave.open(chunk_buffer, 'wb') as chunk_wav:
                chunk_wav.setnchannels(n_channels)
                chunk_wav.setsampwidth(sampwidth)
                chunk_wav.setframerate(framerate)
                chunk_wav.writeframes(raw_frames)
            
            chunks.append({
                "chunk_id": f"chunk_{i+1:03d}",
                "index": i + 1,
                "audio_bytes": chunk_buffer.getvalue(),
                "duration_sec": frames_to_read / framerate,
                "start_time_sec": (i * frames_per_chunk) / framerate
            })

    return chunks


async def simulate_call(
    file_path: Optional[str] = None,
    chunk_duration_sec: float = 3.0,
    delay_sec: float = 3.0,
    scenario: str = "gradual_escalation"
) -> AsyncGenerator[RiskUpdate, None]:
    """
    Day 4 Pipeline:
    Simulates a live phone call by streaming sliced chunks over time.
    For each chunk:
    1. Slices audio bytes
    2. Calls ML analysis stub (analyze_chunk_stub)
    3. Feeds score into RollingRiskAggregator
    4. Yields strict RiskUpdate model
    """
    if not file_path or not os.path.exists(file_path):
        file_path = ensure_default_sample_audio()

    chunks = slice_wav_file(file_path, chunk_duration_sec=chunk_duration_sec)
    total_chunks = len(chunks)
    logger.info(f"Starting call simulation for '{file_path}': {total_chunks} chunks of {chunk_duration_sec}s each.")

    # Initialize rolling risk aggregator (5-chunk weighted window)
    aggregator = RollingRiskAggregator(window_size=5, low_threshold=0.4, high_threshold=0.7)

    for idx, chunk in enumerate(chunks):
        # 1. Call ML stub analysis on chunk audio bytes
        analysis = analyze_chunk_stub(
            audio_bytes=chunk["audio_bytes"],
            step=idx + 1,
            scenario=scenario
        )

        # 2. Feed score into RollingRiskAggregator & create RiskUpdate
        update = aggregator.create_risk_update(
            chunk_id=chunk["chunk_id"],
            chunk_score=analysis["chunk_score"],
            confidence=analysis["confidence"],
            flags=analysis["flags"],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        yield update

        # 3. Yield each chunk with real-time delay (unless this is the last chunk)
        if idx < total_chunks - 1:
            await asyncio.sleep(delay_sec)


class SimulationRunner:
    """
    Manages running call simulation background tasks and broadcasts to WebSockets.
    """
    def __init__(self):
        self._current_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._session_id: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    async def start(
        self,
        file_path: Optional[str] = None,
        chunk_duration_sec: float = 3.0,
        delay_sec: float = 3.0,
        scenario: str = "gradual_escalation"
    ) -> str:
        if self._is_running and self._current_task and not self._current_task.done():
            self.stop()

        self._session_id = f"session_{uuid.uuid4().hex[:8]}"
        self._is_running = True

        async def _run_stream():
            try:
                logger.info(f"Simulation task started: session={self._session_id}")
                async for risk_update in simulate_call(
                    file_path=file_path,
                    chunk_duration_sec=chunk_duration_sec,
                    delay_sec=delay_sec,
                    scenario=scenario
                ):
                    if not self._is_running:
                        break
                    # Broadcast to all connected WebSockets
                    await ws_manager.broadcast(risk_update.model_dump())
                    logger.info(
                        f"[{self._session_id}] Streamed {risk_update.chunk_id}: "
                        f"chunk_score={risk_update.chunk_score:.4f}, "
                        f"rolling={risk_update.rolling_risk_score:.4f}, "
                        f"alert={risk_update.alert_level}, "
                        f"flags={risk_update.flags}"
                    )
            except asyncio.CancelledError:
                logger.info(f"Simulation task {self._session_id} cancelled.")
            except Exception as e:
                logger.error(f"Error in simulation stream: {e}", exc_info=True)
            finally:
                self._is_running = False
                logger.info(f"Simulation task {self._session_id} finished.")

        self._current_task = asyncio.create_task(_run_stream())
        return self._session_id

    def stop(self):
        if self._current_task and not self._current_task.done():
            self._is_running = False
            self._current_task.cancel()
        self._is_running = False


sim_runner = SimulationRunner()
