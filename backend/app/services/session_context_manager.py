"""
VoxGuard In-Memory Session Context Manager

Manages active demo call/transaction contexts in process memory.
Contexts are stored ONLY in memory for active sessions and are NEVER written to SQLite or disk logs.
"""

import threading
from typing import Dict, Optional
from app.models.schemas import SimulationContext


class SessionContextManager:
    """
    Thread-safe in-memory store for active session context objects.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._contexts: Dict[str, SimulationContext] = {}
        self._active_sessions: set[str] = set()

    def register_session(self, session_id: str, initial_context: Optional[SimulationContext] = None):
        """Registers a newly started active session."""
        with self._lock:
            self._active_sessions.add(session_id)
            if initial_context:
                self._contexts[session_id] = initial_context
            else:
                self._contexts[session_id] = SimulationContext()

    def is_active_session(self, session_id: str) -> bool:
        """Checks if a session is currently active/registered."""
        with self._lock:
            return session_id in self._active_sessions

    def set_context(self, session_id: str, context: SimulationContext) -> bool:
        """
        Updates the in-memory context for an active session.
        Returns False if the session_id is not active or registered.
        """
        with self._lock:
            if session_id not in self._active_sessions:
                return False
            self._contexts[session_id] = context
            return True

    def get_context(self, session_id: str) -> Optional[SimulationContext]:
        """
        Retrieves the stored in-memory context for a session.
        Returns None if session is unknown or inactive.
        """
        with self._lock:
            if session_id not in self._active_sessions:
                return None
            return self._contexts.get(session_id)

    def remove_session(self, session_id: str):
        """Clears in-memory context when a session ends or stops."""
        with self._lock:
            self._active_sessions.discard(session_id)
            self._contexts.pop(session_id, None)


# Global singleton instance
session_context_mgr = SessionContextManager()
