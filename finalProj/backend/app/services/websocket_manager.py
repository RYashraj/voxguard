import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("voxguard.websocket")


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts risk updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any] | str):
        """Broadcasts a JSON object or string to all connected WebSocket clients."""
        if not self.active_connections:
            logger.debug("No active WebSocket clients to broadcast to.")
            return

        text_data = json.dumps(message) if isinstance(message, dict) else message
        disconnected_clients = []

        for connection in self.active_connections:
            try:
                await connection.send_text(text_data)
            except Exception as e:
                logger.warning(f"Error sending message to client: {e}")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)


ws_manager = ConnectionManager()
