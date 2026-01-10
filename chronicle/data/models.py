"""Data models for SQLite persistence."""

from dataclasses import dataclass, field
from typing import Optional
import json


# Domain constants
DOMAINS = ["river", "flame", "sky", "war", "harvest", "memory"]


@dataclass
class CitizenRow:
    """Represents a citizen in the database."""
    id: Optional[int]
    name: str
    faction_id: Optional[int]
    belief_vector: dict[str, float]  # domain -> strength
    fear: float  # 0.0 to 1.0
    gratitude: float  # 0.0 to 1.0
    alive: bool = True

    def to_db_tuple(self) -> tuple:
        return (
            self.id,
            self.name,
            self.faction_id,
            json.dumps(self.belief_vector),
            self.fear,
            self.gratitude,
            self.alive,
        )

    @classmethod
    def from_db_row(cls, row: tuple) -> "CitizenRow":
        return cls(
            id=row[0],
            name=row[1],
            faction_id=row[2],
            belief_vector=json.loads(row[3]),
            fear=row[4],
            gratitude=row[5],
            alive=bool(row[6]),
        )


@dataclass
class FactionRow:
    """Represents a faction in the database."""
    id: Optional[int]
    name: str
    doctrine_bias: dict[str, float]  # domain -> weight

    def to_db_tuple(self) -> tuple:
        return (self.id, self.name, json.dumps(self.doctrine_bias))

    @classmethod
    def from_db_row(cls, row: tuple) -> "FactionRow":
        return cls(
            id=row[0],
            name=row[1],
            doctrine_bias=json.loads(row[2]),
        )


@dataclass
class MythRow:
    """Represents a myth (event interpretation) in the database."""
    id: Optional[int]
    text: str
    faction_id: Optional[int]
    domain: str
    confidence: float
    day_created: int

    def to_db_tuple(self) -> tuple:
        return (
            self.id,
            self.text,
            self.faction_id,
            self.domain,
            self.confidence,
            self.day_created,
        )

    @classmethod
    def from_db_row(cls, row: tuple) -> "MythRow":
        return cls(
            id=row[0],
            text=row[1],
            faction_id=row[2],
            domain=row[3],
            confidence=row[4],
            day_created=row[5],
        )


@dataclass
class GodRow:
    """Represents a god in the database."""
    id: Optional[int]
    name: str
    domain: str
    belief_strength: float
    coherence: float
    alive: bool
    birth_day: int
    death_day: Optional[int] = None
    consecutive_strong_days: int = 0
    consecutive_weak_days: int = 0

    def to_db_tuple(self) -> tuple:
        return (
            self.id,
            self.name,
            self.domain,
            self.belief_strength,
            self.coherence,
            self.alive,
            self.birth_day,
            self.death_day,
            self.consecutive_strong_days,
            self.consecutive_weak_days,
        )

    @classmethod
    def from_db_row(cls, row: tuple) -> "GodRow":
        return cls(
            id=row[0],
            name=row[1],
            domain=row[2],
            belief_strength=row[3],
            coherence=row[4],
            alive=bool(row[5]),
            birth_day=row[6],
            death_day=row[7],
            consecutive_strong_days=row[8],
            consecutive_weak_days=row[9],
        )


@dataclass
class WorldStateRow:
    """Represents the world state in the database."""
    id: Optional[int]
    current_day: int
    current_age: str
    age_day_counter: int  # days in current age
    seed: int

    def to_db_tuple(self) -> tuple:
        return (
            self.id,
            self.current_day,
            self.current_age,
            self.age_day_counter,
            self.seed,
        )

    @classmethod
    def from_db_row(cls, row: tuple) -> "WorldStateRow":
        return cls(
            id=row[0],
            current_day=row[1],
            current_age=row[2],
            age_day_counter=row[3],
            seed=row[4],
        )
