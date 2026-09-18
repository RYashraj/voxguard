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
