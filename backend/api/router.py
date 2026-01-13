"""API routes for Living Chronicle."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..services.simulation_manager import SimulationManager
from ..services.grid_mapper import GridMapper

api_router = APIRouter()
grid_mapper = GridMapper()


# Dependency to get simulation manager
def get_sim_manager() -> SimulationManager:
    """Get the global simulation manager instance."""
    from ..main import sim_manager
    if sim_manager is None:
        raise HTTPException(status_code=500, detail="Simulation manager not initialized")
    return sim_manager


# Request/Response models
class InitRequest(BaseModel):
    """Request model for initializing simulation."""
    fresh: bool = False
    seed: int = 42


class ControlRequest(BaseModel):
    """Request model for controlling simulation."""
    action: str  # "start", "stop", "step"
    speed: float = 1.0


# API Endpoints

@api_router.post("/init")
async def initialize_simulation(
    req: InitRequest,
    sim: SimulationManager = Depends(get_sim_manager)
):
    """Initialize or restore simulation."""
    try:
        sim.initialize(fresh=req.fresh, seed=req.seed)
        return {
            "status": "initialized",
            "day": sim.current_day,
            "seed": req.seed,
            "fresh": req.fresh,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize: {str(e)}")


@api_router.get("/state")
async def get_state(sim: SimulationManager = Depends(get_sim_manager)):
    """Get current simulation state."""
    state = sim.get_current_state()
    if state is None:
        raise HTTPException(
            status_code=400,
            detail="Simulation not initialized. Call /init first."
        )
    return state


@api_router.post("/control")
async def control_simulation(
    req: ControlRequest,
    sim: SimulationManager = Depends(get_sim_manager)
):
    """Control simulation (start/stop/step)."""
    try:
        if req.action == "start":
            sim.start(speed=req.speed)
            return {
                "status": "running",
                "speed": req.speed,
                "day": sim.current_day,
            }
        elif req.action == "stop":
            sim.stop()
            return {
                "status": "stopped",
                "day": sim.current_day,
            }
        elif req.action == "step":
            result = sim.step()
            return {
                "status": "stepped",
                "day": result.day,
                "age": result.age.value,
                "event": {
                    "name": result.event.name,
                    "description": result.event.description,
                    "domain": result.event.primary_domain,
                } if result.event else None,
                "born_gods": [g.row.name for g in result.born_gods],
                "faded_gods": [g.row.name for g in result.faded_gods],
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {req.action}. Use 'start', 'stop', or 'step'."
            )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Control failed: {str(e)}")


@api_router.get("/history/gods")
async def get_god_history(sim: SimulationManager = Depends(get_sim_manager)):
    """Get all gods (alive and dead) for history view."""
    try:
        with sim._lock:
            all_gods = sim.db.get_all_gods(alive_only=False)
            return [
                {
                    "id": g.id,
                    "name": g.name,
                    "domain": g.domain,
                    "birth_day": g.birth_day,
                    "death_day": g.death_day,
                    "alive": g.alive,
                    "belief_strength": g.belief_strength,
                    "coherence": g.coherence,
                }
                for g in all_gods
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get gods: {str(e)}")


@api_router.get("/history/myths")
async def get_myths(sim: SimulationManager = Depends(get_sim_manager)):
    """Get all myths."""
    try:
        with sim._lock:
            myths = sim.db.get_all_myths()
            return [
                {
                    "id": m.id,
                    "text": m.text,
                    "domain": m.domain,
                    "confidence": m.confidence,
                    "day_created": m.day_created,
                    "faction_id": m.faction_id,
                }
                for m in myths
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get myths: {str(e)}")


@api_router.get("/grid")
async def get_grid(sim: SimulationManager = Depends(get_sim_manager)):
    """
    Get current 64x64 LED grid visualization.

    Returns a 64x64 array of cells with color, brightness, and flicker data.
    """
    try:
        state = sim.get_current_state()
        if state is None:
            raise HTTPException(
                status_code=400,
                detail="Simulation not initialized. Call /init first."
            )

        # Import Age enum
        from chronicle.sim.ages import Age

        # Map state to grid
        grid = grid_mapper.map_state_to_grid(
            citizens=state["citizens"],
            gods=state["gods"],
            factions=state["factions"],
            age=Age(state["age"]),
            historical_scars=sim.get_historical_scars()
        )

        # Convert to JSON
        return grid_mapper.grid_to_json(grid)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid state: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate grid: {str(e)}")
