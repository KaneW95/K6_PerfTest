"""WebSocket connection manager."""
import json
from typing import Dict, Any, List
from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSockets."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_log(self, websocket: WebSocket, log: str, level: str = "info"):
        """Send a log message."""
        await self.send_message(websocket, {
            "type": "log",
            "level": level,
            "message": log
        })
    
    async def send_status(self, websocket: WebSocket, status: str, data: Dict[str, Any] = None):
        """Send a status update."""
        message = {
            "type": "status",
            "status": status
        }
        if data:
            message["data"] = data
        await self.send_message(websocket, message)
    
    async def send_result(self, websocket: WebSocket, result: Dict[str, Any]):
        """Send test result."""
        await self.send_message(websocket, {
            "type": "result",
            "data": result
        })
    
    async def send_error(self, websocket: WebSocket, error: str):
        """Send error message."""
        await self.send_message(websocket, {
            "type": "error",
            "message": error
        })
