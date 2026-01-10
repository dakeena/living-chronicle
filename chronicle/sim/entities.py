"""Entity classes for Living Chronicle."""

from dataclasses import dataclass, field
from typing import Optional
import random

from ..data.models import DOMAINS, CitizenRow, FactionRow, MythRow, GodRow


# Name generation pools
CITIZEN_PREFIXES = [
    "Ash", "Brin", "Cal", "Dara", "Eld", "Fenn", "Gael", "Haran", "Isen", "Jora",
    "Kael", "Lira", "Morn", "Neth", "Oren", "Pira", "Quell", "Rath", "Sev", "Tarn",
    "Ula", "Vorn", "Wren", "Xan", "Yara", "Zeph"
]
CITIZEN_SUFFIXES = [
    "an", "el", "is", "on", "us", "a", "en", "or", "ia", "yn",
    "ax", "ix", "eth", "oth", "ara", "ira", "ona", "ius", "eon", "wyn"
]

FACTION_ADJECTIVES = [
    "Crimson", "Azure", "Golden", "Ashen", "Verdant", "Obsidian", "Silver", "Amber"
]
FACTION_NOUNS = [
    "Covenant", "Circle", "Order", "Pact", "Brotherhood", "Sisterhood", "Assembly", "Conclave"
]

GOD_PREFIXES = {
    "river": ["Aqua", "Thal", "Riv", "Und", "Mare"],
    "flame": ["Pyr", "Igna", "Braz", "Cind", "Scor"],
    "sky": ["Ael", "Cael", "Zeph", "Aur", "Nub"],
    "war": ["Bel", "Mort", "Vic", "Mar", "Stri"],
    "harvest": ["Cer", "Fert", "Plen", "Grai", "Boun"],
    "memory": ["Mnem", "Chron", "Eter", "Rem", "Hist"],
}
GOD_SUFFIXES = ["us", "a", "ion", "or", "is", "ax", "oth", "iel", "ara", "eon"]


def generate_citizen_name(rng: random.Random) -> str:
    """Generate a random citizen name."""
    return rng.choice(CITIZEN_PREFIXES) + rng.choice(CITIZEN_SUFFIXES)


def generate_faction_name(rng: random.Random) -> str:
    """Generate a random faction name."""
    return f"The {rng.choice(FACTION_ADJECTIVES)} {rng.choice(FACTION_NOUNS)}"


def generate_god_name(domain: str, rng: random.Random) -> str:
    """Generate a god name based on domain."""
    prefixes = GOD_PREFIXES.get(domain, GOD_PREFIXES["memory"])
    return rng.choice(prefixes) + rng.choice(GOD_SUFFIXES)


@dataclass
class Citizen:
    """A citizen of the world."""
    row: CitizenRow

    @classmethod
    def generate(cls, faction_id: Optional[int], rng: random.Random) -> "Citizen":
        """Generate a new random citizen."""
        belief_vector = {domain: rng.uniform(0, 0.3) for domain in DOMAINS}
        return cls(CitizenRow(
            id=None,
            name=generate_citizen_name(rng),
            faction_id=faction_id,
            belief_vector=belief_vector,
            fear=rng.uniform(0.1, 0.4),
            gratitude=rng.uniform(0.1, 0.4),
            alive=True,
        ))

    def update_belief(self, domain: str, delta: float, faction_bias: float = 1.0) -> None:
        """Update belief in a domain."""
        current = self.row.belief_vector.get(domain, 0.0)
        new_value = max(0.0, min(1.0, current + delta * faction_bias))
        self.row.belief_vector[domain] = new_value

    def update_emotion(self, fear_delta: float, gratitude_delta: float) -> None:
        """Update fear and gratitude levels."""
        self.row.fear = max(0.0, min(1.0, self.row.fear + fear_delta))
        self.row.gratitude = max(0.0, min(1.0, self.row.gratitude + gratitude_delta))


@dataclass
class Faction:
    """A faction with shared beliefs."""
    row: FactionRow
    members: list[Citizen] = field(default_factory=list)

    @classmethod
    def generate(cls, rng: random.Random) -> "Faction":
        """Generate a new random faction."""
        # Create a doctrine bias favoring 1-2 domains
        doctrine = {domain: rng.uniform(0.1, 0.4) for domain in DOMAINS}
        favored = rng.sample(DOMAINS, k=rng.randint(1, 2))
        for domain in favored:
            doctrine[domain] = rng.uniform(0.7, 1.0)

        return cls(FactionRow(
            id=None,
            name=generate_faction_name(rng),
            doctrine_bias=doctrine,
        ))

    def get_bias(self, domain: str) -> float:
        """Get faction's bias toward a domain."""
        return self.row.doctrine_bias.get(domain, 0.5)


@dataclass
class Myth:
    """An interpretation of an event."""
    row: MythRow

    @classmethod
    def create(
        cls,
        text: str,
        domain: str,
        confidence: float,
        faction_id: Optional[int],
        day: int
    ) -> "Myth":
        """Create a new myth."""
        return cls(MythRow(
            id=None,
            text=text,
            faction_id=faction_id,
            domain=domain,
            confidence=confidence,
            day_created=day,
        ))


@dataclass
class God:
    """An emergent deity."""
    row: GodRow

    @classmethod
    def birth(cls, domain: str, belief_strength: float, coherence: float, day: int, rng: random.Random) -> "God":
        """Birth a new god."""
        return cls(GodRow(
            id=None,
            name=generate_god_name(domain, rng),
            domain=domain,
            belief_strength=belief_strength,
            coherence=coherence,
            alive=True,
            birth_day=day,
            death_day=None,
            consecutive_strong_days=0,
            consecutive_weak_days=0,
        ))

    def fade(self, day: int) -> None:
        """Mark god as faded/dead."""
        self.row.alive = False
        self.row.death_day = day

    def update_strength(self, new_strength: float, new_coherence: float) -> None:
        """Update belief strength and coherence."""
        self.row.belief_strength = new_strength
        self.row.coherence = new_coherence
