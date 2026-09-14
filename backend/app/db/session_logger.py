import os
import json
import sqlite3
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("voxguard.db")


def get_db_path() -> str:
    """
    Resolves local SQLite database path.
    Defaults to source-relative backend/data/voxguard.db regardless of execution CWD,
    or uses VOXGUARD_DB_PATH environment variable if set.
    """
    env_path = os.getenv("VOXGUARD_DB_PATH")
    if env_path:
        path = Path(env_path)
    else:
        # Resolve relative to session_logger.py -> backend/data/voxguard.db
        path = Path(__file__).parent.parent / "data" / "voxguard.db"

    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())


def init_db(db_path: Optional[str] = None) -> bool:
    """
    Initializes SQLite database schema synchronously.
    Creates chunk_history table and sessions view/alias for Day 5 contract compatibility.
    Returns True if successful, False if an error occurs.
    """
    target_path = db_path or get_db_path()
    try:
        with sqlite3.connect(target_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunk_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    chunk_score REAL NOT NULL,
                    rolling_risk_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    flags TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    inference_latency_ms REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON chunk_history(session_id)")
            # Day 5 requirement: Ensure 'sessions' table/view is queryable
            cursor.execute("CREATE VIEW IF NOT EXISTS sessions AS SELECT * FROM chunk_history")
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database at '{target_path}': {e}")
        return False


async def init_db_async(db_path: Optional[str] = None) -> bool:
    """Async wrapper offloading init_db to a worker thread."""
    return await asyncio.to_thread(init_db, db_path)


def log_chunk_record(
    session_id: str,
    chunk_id: str,
    timestamp: str,
    chunk_score: float,
    rolling_risk_score: float,
    confidence: float,
    flags: List[str],
    alert_level: str,
    inference_latency_ms: float,
    db_path: Optional[str] = None
) -> bool:
    """
    Synchronously persists a chunk record.
    Catches own SQLite errors, logs server-side warning, and returns False on error (True on success).
    """
    target_path = db_path or get_db_path()
    try:
        # Lazy schema check / initialization
        init_db(target_path)

        flags_json = json.dumps(flags or [])
        with sqlite3.connect(target_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chunk_history (
                    session_id, chunk_id, timestamp, chunk_score,
                    rolling_risk_score, confidence, flags, alert_level, inference_latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, chunk_id, timestamp, float(chunk_score),
                float(rolling_risk_score), float(confidence), flags_json,
                str(alert_level), float(inference_latency_ms)
            ))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to persist chunk record for session='{session_id}', chunk='{chunk_id}': {e}")
        return False


async def log_chunk_record_async(
    session_id: str,
    chunk_id: str,
    timestamp: str,
    chunk_score: float,
    rolling_risk_score: float,
    confidence: float,
    flags: List[str],
    alert_level: str,
    inference_latency_ms: float,
    db_path: Optional[str] = None
) -> bool:
    """Async wrapper offloading log_chunk_record to a worker thread."""
    return await asyncio.to_thread(
        log_chunk_record,
        session_id,
        chunk_id,
        timestamp,
        chunk_score,
        rolling_risk_score,
        confidence,
        flags,
        alert_level,
        inference_latency_ms,
        db_path
    )


def get_session_history(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves chronological chunk history records for a given session_id.
    Orders deterministically by: ORDER BY timestamp ASC, id ASC.
    """
    target_path = db_path or get_db_path()
    try:
        init_db(target_path)
        with sqlite3.connect(target_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, chunk_id, timestamp, chunk_score,
                       rolling_risk_score, confidence, flags, alert_level, inference_latency_ms
                FROM chunk_history
                WHERE session_id = ?
                ORDER BY timestamp ASC, id ASC
            """, (session_id,))
            rows = cursor.fetchall()

            history = []
            for row in rows:
                item = dict(row)
                try:
                    item["flags"] = json.loads(item["flags"])
                except Exception:
                    item["flags"] = []
                history.append(item)
            return history
    except Exception as e:
        logger.error(f"Failed to retrieve session history for '{session_id}': {e}")
        return []


async def get_session_history_async(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Async wrapper offloading get_session_history to a worker thread."""
    return await asyncio.to_thread(get_session_history, session_id, db_path)


def get_session_stats(session_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes summary metrics for a call session:
    - total_chunks
    - avg_latency_ms
    - peak_risk_score
    - final_alert_level
    - flags_triggered
    """
    history = get_session_history(session_id, db_path)
    if not history:
        return {
            "session_id": session_id,
            "total_chunks": 0,
            "avg_latency_ms": 0.0,
            "peak_risk_score": 0.0,
            "final_alert_level": "none",
            "flags_triggered": []
        }

    total_chunks = len(history)
    latencies = [item.get("inference_latency_ms", 0.0) for item in history]
    avg_latency = round(sum(latencies) / total_chunks, 2) if total_chunks > 0 else 0.0
    peak_risk = max((item.get("rolling_risk_score", 0.0) for item in history), default=0.0)
    final_alert = history[-1].get("alert_level", "low")
    
    all_flags = set()
    for item in history:
        all_flags.update(item.get("flags", []))

    return {
        "session_id": session_id,
        "total_chunks": total_chunks,
        "avg_latency_ms": avg_latency,
        "peak_risk_score": round(peak_risk, 4),
        "final_alert_level": final_alert,
        "flags_triggered": sorted(list(all_flags)),
        "start_time": history[0]["timestamp"],
        "end_time": history[-1]["timestamp"]
    }


async def get_session_stats_async(session_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Async wrapper offloading get_session_stats to a worker thread."""
    return await asyncio.to_thread(get_session_stats, session_id, db_path)


def list_all_sessions(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists all distinct call sessions stored in the SQLite database with high-level summaries.
    """
    target_path = db_path or get_db_path()
    try:
        init_db(target_path)
        with sqlite3.connect(target_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT session_id FROM chunk_history ORDER BY id DESC")
            session_ids = [row[0] for row in cursor.fetchall()]

        return [get_session_stats(sid, target_path) for sid in session_ids]
    except Exception as e:
        logger.error(f"Failed to list sessions from SQLite: {e}")
        return []


async def list_all_sessions_async(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Async wrapper offloading list_all_sessions to a worker thread."""
    return await asyncio.to_thread(list_all_sessions, db_path)

