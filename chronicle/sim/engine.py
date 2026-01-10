"""Main simulation engine for Living Chronicle."""

from dataclasses import dataclass, field
from typing import Optional, Callable
import random

from ..data.database import Database
from ..data.models import WorldStateRow, DOMAINS
from .ages import Age, AgeManager
from .entities import Citizen, Faction, Myth, God
from .events import Event, EventGenerator
from .gods import GodSystem


# World generation parameters
INITIAL_FACTIONS = 3
INITIAL_CITIZENS_PER_FACTION = 8
UNAFFILIATED_CITIZENS = 5


@dataclass
class TickResult:
    """Results of a single simulation tick."""
    day: int
    age: Age
    event: Optional[Event]
    age_transition: Optional[Age]  # new age if transitioned
    born_gods: list[God]
    faded_gods: list[God]
    new_myths: list[Myth]


class SimulationEngine:
    """Main simulation engine."""

    def __init__(
        self,
        db: Database,
        seed: int = 42,
        narrator: Optional[Callable[[TickResult], None]] = None
    ):
        self.db = db
        self.seed = seed
        self.rng = random.Random(seed)
        self.narrator = narrator

        self.age_manager: Optional[AgeManager] = None
        self.event_generator: Optional[EventGenerator] = None
        self.god_system: Optional[GodSystem] = None
        self.current_day = 0

        self._factions: list[Faction] = []
        self._citizens: list[Citizen] = []

    def initialize(self, fresh: bool = False) -> None:
        """Initialize or restore the simulation."""
        self.db.connect()

        if fresh:
            self.db.clear_all()

        world_state = self.db.get_world_state()

        if world_state is None:
            self._create_new_world()
        else:
            self._restore_world(world_state)

        self.event_generator = EventGenerator(self.rng)
        self.god_system = GodSystem(self.db, self.rng)

    def _create_new_world(self) -> None:
        """Create a fresh new world."""
        self.current_day = 0
        self.age_manager = AgeManager.new(self.rng)

        # Create factions
        for _ in range(INITIAL_FACTIONS):
            faction = Faction.generate(self.rng)
            self.db.save_faction(faction.row)
            self._factions.append(faction)

            # Create citizens for faction
            for _ in range(INITIAL_CITIZENS_PER_FACTION):
                citizen = Citizen.generate(faction.row.id, self.rng)
                self.db.save_citizen(citizen.row)
                faction.members.append(citizen)
                self._citizens.append(citizen)

        # Create unaffiliated citizens
        for _ in range(UNAFFILIATED_CITIZENS):
            citizen = Citizen.generate(None, self.rng)
            self.db.save_citizen(citizen.row)
            self._citizens.append(citizen)

        # Save initial world state
        self._save_world_state()

    def _restore_world(self, state: WorldStateRow) -> None:
        """Restore world from saved state."""
        self.current_day = state.current_day
        self.seed = state.seed
        self.rng = random.Random(state.seed)
        # Advance RNG to current state
        for _ in range(state.current_day):
            self.rng.random()

        self.age_manager = AgeManager.from_state(
            state.current_age,
            state.age_day_counter,
            self.rng
        )

        # Load factions and citizens
        for faction_row in self.db.get_all_factions():
            faction = Faction(faction_row)
            self._factions.append(faction)

        for citizen_row in self.db.get_all_citizens():
            citizen = Citizen(citizen_row)
            self._citizens.append(citizen)
            # Associate with faction
            if citizen.row.faction_id:
                for faction in self._factions:
                    if faction.row.id == citizen.row.faction_id:
                        faction.members.append(citizen)
                        break

    def _save_world_state(self) -> None:
        """Save current world state."""
        state = WorldStateRow(
            id=1,
            current_day=self.current_day,
            current_age=self.age_manager.current_age.value,
            age_day_counter=self.age_manager.day_counter,
            seed=self.seed,
        )
        self.db.save_world_state(state)

    def tick(self) -> TickResult:
        """Execute one simulation tick (one day)."""
        self.current_day += 1

        # Check for age transition
        age_transition = self.age_manager.tick()

        # Generate event
        event = self.event_generator.generate_event(
            self.age_manager.current_age,
            self.age_manager.traits["event_rate"]
        )

        new_myths = []
        if event:
            # Apply event effects to citizens
            self._apply_event(event)
            # Create myths from event
            new_myths = self._create_myths(event)

        # Process emergent gods
        born_gods, faded_gods = self.god_system.process_gods(
            self._citizens,
            self.current_day
        )

        # Save all citizen state
        for citizen in self._citizens:
            self.db.save_citizen(citizen.row)

        # Save world state
        self._save_world_state()

        result = TickResult(
            day=self.current_day,
            age=self.age_manager.current_age,
            event=event,
            age_transition=age_transition,
            born_gods=born_gods,
            faded_gods=faded_gods,
            new_myths=new_myths,
        )

        if self.narrator:
            self.narrator(result)

        return result

    def _apply_event(self, event: Event) -> None:
        """Apply event effects to citizens."""
        age_traits = self.age_manager.traits
        belief_growth = age_traits["belief_growth"]
        fear_mod = age_traits["fear_modifier"]
        grat_mod = age_traits["gratitude_modifier"]

        for citizen in self._citizens:
            # Get faction bias if applicable
            faction_bias = 1.0
            if citizen.row.faction_id:
                for faction in self._factions:
                    if faction.row.id == citizen.row.faction_id:
                        faction_bias = faction.get_bias(event.primary_domain)
                        break

            # Update beliefs
            belief_delta = event.belief_impact * belief_growth * (0.8 + self.rng.random() * 0.4)
            citizen.update_belief(event.primary_domain, belief_delta, faction_bias)

            if event.secondary_domain:
                secondary_delta = belief_delta * 0.5
                citizen.update_belief(event.secondary_domain, secondary_delta, faction_bias)

            # Update emotions
            fear_delta = event.fear_impact * fear_mod * (0.8 + self.rng.random() * 0.4)
            grat_delta = event.gratitude_impact * grat_mod * (0.8 + self.rng.random() * 0.4)
            citizen.update_emotion(fear_delta, grat_delta)

    def _create_myths(self, event: Event) -> list[Myth]:
        """Create myths from an event interpretation."""
        myths = []

        # Each faction might create a myth
        for faction in self._factions:
            if self.rng.random() < 0.3:  # 30% chance per faction
                confidence = faction.get_bias(event.primary_domain)
                myth = Myth.create(
                    text=f"The {faction.row.name} witnessed {event.description}",
                    domain=event.primary_domain,
                    confidence=confidence,
                    faction_id=faction.row.id,
                    day=self.current_day,
                )
                self.db.save_myth(myth.row)
                myths.append(myth)

        return myths

    def run(self, days: Optional[int] = None) -> None:
        """Run the simulation for a number of days or indefinitely."""
        if days is None:
            while True:
                self.tick()
        else:
            for _ in range(days):
                self.tick()

    def get_citizens(self) -> list[Citizen]:
        """Get all citizens."""
        return self._citizens

    def get_factions(self) -> list[Faction]:
        """Get all factions."""
        return self._factions

    def shutdown(self) -> None:
        """Clean shutdown of the simulation."""
        self.db.close()
