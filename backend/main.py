"""FastAPI application for Living Chronicle web UI."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .services.simulation_manager import SimulationManager
from .api.router import api_router
from .api.websocket import ws_router

# Global simulation manager
sim_manager: SimulationManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global sim_manager
    sim_manager = SimulationManager(db_path="chronicle.db")
    yield
    if sim_manager:
        sim_manager.shutdown()


app = FastAPI(
    title="Living Chronicle API",
    version="0.1.0",
    description="Web API for the Living Chronicle mythic civilization simulator",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "day": sim_manager.current_day if sim_manager else 0,
        "running": sim_manager.is_running if sim_manager else False,
    }
