"""WebSocket handler for real-time tick streaming."""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Any

from ..services.simulation_manager import SimulationManager

ws_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for tick broadcasting."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


@ws_router.websocket("/ws/ticks")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time tick updates.

    Clients connect to this endpoint to receive simulation tick events as they occur.
    Each tick broadcasts: day, age, event, born gods, faded gods, age transitions.
    """
    from ..main import sim_manager

    await manager.connect(websocket)

    # Get the current event loop for this WebSocket connection
    loop = asyncio.get_event_loop()

    # Create async callback to broadcast tick results
    def broadcast_tick(result):
        """Callback to broadcast tick results to all connected clients."""
        try:
            message = {
                "type": "tick",
                "data": {
                    "day": result.day,
                    "age": result.age.value,
                    "event": {
                        "name": result.event.name,
                        "description": result.event.description,
                        "domain": result.event.primary_domain,
                        "magnitude": result.event.magnitude if hasattr(result.event, 'magnitude') else None,
                    } if result.event else None,
                    "born_gods": [
                        {
                            "name": g.row.name,
                            "domain": g.row.domain,
                        }
                        for g in result.born_gods
                    ],
                    "faded_gods": [
                        {
                            "name": g.row.name,
                            "domain": g.row.domain,
                        }
                        for g in result.faded_gods
                    ],
                    "age_transition": result.age_transition.value if result.age_transition else None,
                    "new_myths": [
                        {
                            "text": m.row.text,
                            "domain": m.row.domain,
                            "confidence": m.row.confidence,
                        }
                        for m in result.new_myths
                    ],
                }
            }

            # Schedule the async broadcast in the WebSocket's event loop
            async def do_broadcast():
                await manager.broadcast(message)

            asyncio.run_coroutine_threadsafe(do_broadcast(), loop)

        except Exception as e:
            print(f"Error in broadcast_tick: {e}")

    # Use the synchronous callback
    tick_callback = broadcast_tick

    # Subscribe to simulation tick events
    sim_manager.subscribe(tick_callback)

    try:
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()

            # Handle client messages
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                await websocket.send_json({
                    "type": "status",
                    "data": {
                        "day": sim_manager.current_day,
                        "running": sim_manager.is_running,
                        "connections": manager.connection_count,
                    }
                })
            else:
                # Echo unknown messages
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        sim_manager.unsubscribe(tick_callback)
        print("WebSocket client disconnected normally")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        sim_manager.unsubscribe(tick_callback)


@ws_router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status."""
    return {
        "active_connections": manager.connection_count,
        "endpoint": "/api/ws/ticks",
    }
