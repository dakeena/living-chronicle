"""Thread-safe wrapper for SimulationEngine."""

import threading
import time
from typing import Optional, Callable, Any
from dataclasses import asdict

from chronicle.data import Database
from chronicle.sim import SimulationEngine
from chronicle.sim.engine import TickResult
from chronicle.sim.ages import Age


class SimulationManager:
    """
    Manages simulation lifecycle and provides thread-safe access.

    Key responsibilities:
    - Wrap SimulationEngine for concurrent access
    - Manage tick execution in background thread
    - Broadcast tick results to WebSocket subscribers
    - Maintain historical scar positions across cycles
    """

    def __init__(self, db_path: str = "chronicle.db"):
        self.db_path = db_path
        self.db = Database(db_path)
        self.engine: Optional[SimulationEngine] = None

        # Simulation control
        self._lock = threading.Lock()
        self._running = False
        self._tick_thread: Optional[threading.Thread] = None
        self._tick_delay = 1.0  # seconds between ticks

        # WebSocket subscribers
        self._subscribers: list[Callable[[TickResult], None]] = []

        # Historical scars tracking (for LED display)
        self._historical_scars: dict[tuple[int, int], dict[str, Any]] = {}

    def initialize(self, fresh: bool = False, seed: int = 42) -> None:
        """Initialize or restore simulation."""
        with self._lock:
            self.engine = SimulationEngine(self.db, seed=seed)
            self.engine.initialize(fresh=fresh)

            if fresh:
                self._historical_scars.clear()

    def subscribe(self, callback: Callable[[TickResult], None]) -> None:
        """Subscribe to tick updates."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[TickResult], None]) -> None:
        """Unsubscribe from tick updates."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _broadcast_tick(self, result: TickResult) -> None:
        """Broadcast tick result to all subscribers."""
        for callback in self._subscribers[:]:  # Copy list to avoid modification during iteration
            try:
                callback(result)
            except Exception as e:
                print(f"Error broadcasting to subscriber: {e}")

    def start(self, speed: float = 1.0) -> None:
        """Start automatic ticking."""
        if self._running:
            return

        self._running = True
        self._tick_delay = 1.0 / speed
        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()

    def stop(self) -> None:
        """Stop automatic ticking."""
        self._running = False
        if self._tick_thread:
            self._tick_thread.join(timeout=2.0)
            self._tick_thread = None

    def step(self) -> TickResult:
        """Execute single tick and return result."""
        with self._lock:
            if not self.engine:
                raise RuntimeError("Simulation not initialized")

            result = self.engine.tick()
            self._update_historical_scars(result)
            self._broadcast_tick(result)
            return result

    def _tick_loop(self) -> None:
        """Background thread for automatic ticking."""
        while self._running:
            try:
                self.step()
                time.sleep(self._tick_delay)
            except Exception as e:
                print(f"Error in tick loop: {e}")
                self._running = False

    def _update_historical_scars(self, result: TickResult) -> None:
        """Track historical scars for Collapse/Silence ages."""
        # On Collapse, record god death locations
        if result.age == Age.COLLAPSE:
            for god in result.faded_gods:
                # Map god to grid position (deterministic hash)
                x, y = self._god_to_position(god)
                self._historical_scars[(x, y)] = {
                    "god_name": god.row.name,
                    "domain": god.row.domain,
                    "death_day": result.day,
                }

        # Clear scars on new Emergence
        if result.age_transition and result.age_transition == Age.EMERGENCE:
            self._historical_scars.clear()

    def _god_to_position(self, god) -> tuple[int, int]:
        """Map god to deterministic grid position based on name hash."""
        name_hash = hash(god.row.name)
        x = name_hash % 64
        y = (name_hash // 64) % 64
        return (x, y)

    def get_current_state(self) -> Optional[dict[str, Any]]:
        """Get current simulation state snapshot."""
        with self._lock:
            if not self.engine:
                return None

            return {
                "day": self.engine.current_day,
                "age": self.engine.age_manager.current_age.value,
                "age_day": self.engine.age_manager.day_counter,
                "seed": self.engine.seed,
                "citizens": [
                    {
                        "id": c.row.id,
                        "name": c.row.name,
                        "faction_id": c.row.faction_id,
                        "beliefs": c.row.belief_vector,
                        "fear": c.row.fear,
                        "gratitude": c.row.gratitude,
                        "alive": c.row.alive,
                    }
                    for c in self.engine.get_citizens()
                ],
                "factions": [
                    {
                        "id": f.row.id,
                        "name": f.row.name,
                        "doctrine": f.row.doctrine_bias,
                    }
                    for f in self.engine.get_factions()
                ],
                "gods": [
                    {
                        "id": g.id,
                        "name": g.name,
                        "domain": g.domain,
                        "belief_strength": g.belief_strength,
                        "coherence": g.coherence,
                        "alive": g.alive,
                        "birth_day": g.birth_day,
                    }
                    for g in self.db.get_all_gods(alive_only=True)
                ],
            }

    def get_historical_scars(self) -> dict[tuple[int, int], dict[str, Any]]:
        """Get historical scar positions for LED display."""
        return self._historical_scars.copy()

    @property
    def current_day(self) -> int:
        """Get current simulation day."""
        with self._lock:
            return self.engine.current_day if self.engine else 0

    @property
    def is_running(self) -> bool:
        """Check if simulation is auto-running."""
        return self._running

    def shutdown(self) -> None:
        """Clean shutdown."""
        self.stop()
        if self.engine:
            self.engine.shutdown()
