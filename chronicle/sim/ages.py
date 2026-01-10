"""Age cycle management for Living Chronicle."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import random


class Age(Enum):
    """The six ages of the cycle."""
    EMERGENCE = "Emergence"
    ORDER = "Order"
    STRAIN = "Strain"
    COLLAPSE = "Collapse"
    SILENCE = "Silence"
    REBIRTH = "Rebirth"

    def next(self) -> "Age":
        """Get the next age in the cycle."""
        cycle = list(Age)
        idx = cycle.index(self)
        return cycle[(idx + 1) % len(cycle)]


# Age characteristics
AGE_TRAITS = {
    Age.EMERGENCE: {
        "min_days": 20,
        "max_days": 40,
        "event_rate": 0.6,
        "belief_growth": 1.2,
        "fear_modifier": 0.3,
        "gratitude_modifier": 0.7,
    },
    Age.ORDER: {
        "min_days": 30,
        "max_days": 60,
        "event_rate": 0.4,
        "belief_growth": 1.0,
        "fear_modifier": 0.2,
        "gratitude_modifier": 0.8,
    },
    Age.STRAIN: {
        "min_days": 25,
        "max_days": 45,
        "event_rate": 0.7,
        "belief_growth": 1.1,
        "fear_modifier": 0.6,
        "gratitude_modifier": 0.4,
    },
    Age.COLLAPSE: {
        "min_days": 15,
        "max_days": 30,
        "event_rate": 0.9,
        "belief_growth": 0.8,
        "fear_modifier": 0.9,
        "gratitude_modifier": 0.1,
    },
    Age.SILENCE: {
        "min_days": 10,
        "max_days": 25,
        "event_rate": 0.2,
        "belief_growth": 0.5,
        "fear_modifier": 0.5,
        "gratitude_modifier": 0.3,
    },
    Age.REBIRTH: {
        "min_days": 15,
        "max_days": 35,
        "event_rate": 0.5,
        "belief_growth": 1.3,
        "fear_modifier": 0.4,
        "gratitude_modifier": 0.6,
    },
}


@dataclass
class AgeManager:
    """Manages age transitions and characteristics."""
    current_age: Age
    day_counter: int  # days in current age
    age_duration: int  # total days this age will last
    rng: random.Random

    @classmethod
    def new(cls, rng: random.Random) -> "AgeManager":
        """Create a new age manager starting at Emergence."""
        age = Age.EMERGENCE
        traits = AGE_TRAITS[age]
        duration = rng.randint(traits["min_days"], traits["max_days"])
        return cls(
            current_age=age,
            day_counter=0,
            age_duration=duration,
            rng=rng,
        )

    @classmethod
    def from_state(cls, age_name: str, day_counter: int, rng: random.Random) -> "AgeManager":
        """Restore an age manager from saved state."""
        age = Age(age_name)
        traits = AGE_TRAITS[age]
        # Estimate remaining duration
        duration = max(day_counter + 1, traits["min_days"])
        return cls(
            current_age=age,
            day_counter=day_counter,
            age_duration=duration,
            rng=rng,
        )

    def tick(self) -> Optional[Age]:
        """
        Advance one day. Returns the new age if a transition occurred, None otherwise.
        """
        self.day_counter += 1

        if self.day_counter >= self.age_duration:
            return self._transition()
        return None

    def _transition(self) -> Age:
        """Transition to the next age."""
        self.current_age = self.current_age.next()
        self.day_counter = 0
        traits = AGE_TRAITS[self.current_age]
        self.age_duration = self.rng.randint(traits["min_days"], traits["max_days"])
        return self.current_age

    @property
    def traits(self) -> dict:
        """Get current age traits."""
        return AGE_TRAITS[self.current_age]
