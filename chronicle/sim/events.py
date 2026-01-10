"""Event generation for Living Chronicle."""

from dataclasses import dataclass
from typing import Optional
import random

from ..data.models import DOMAINS
from .ages import Age


@dataclass
class Event:
    """An event that occurs in the simulation."""
    name: str
    description: str
    primary_domain: str
    secondary_domain: Optional[str]
    fear_impact: float  # -1.0 to 1.0
    gratitude_impact: float  # -1.0 to 1.0
    belief_impact: float  # how much belief shifts toward primary domain
    magnitude: float  # 0.0 to 1.0, affects narration


# Event templates by domain
EVENT_TEMPLATES = {
    "river": [
        ("The Great Flooding", "Waters rise beyond their banks", 0.4, -0.2, 0.3),
        ("The Still Waters", "Rivers calm to mirror-glass", -0.2, 0.3, 0.2),
        ("The River's Bounty", "Fish leap willingly into nets", -0.1, 0.5, 0.4),
        ("The Poisoned Springs", "Wells turn bitter and foul", 0.5, -0.3, 0.3),
        ("The Parting Currents", "Waters divide before the faithful", 0.1, 0.4, 0.5),
    ],
    "flame": [
        ("The Consuming Fire", "Flames devour without warning", 0.6, -0.4, 0.4),
        ("The Warming Hearth", "All fires burn steady and true", -0.2, 0.4, 0.3),
        ("The Forge's Blessing", "Metalwork emerges flawless", -0.1, 0.5, 0.4),
        ("The Ember Rain", "Sparks fall from cloudless sky", 0.5, -0.2, 0.5),
        ("The Eternal Flame", "A fire burns without fuel", 0.2, 0.3, 0.6),
    ],
    "sky": [
        ("The Darkened Sun", "Shadow crosses the daylight", 0.5, -0.3, 0.5),
        ("The Gentle Rains", "Clouds bring life-giving water", -0.2, 0.5, 0.3),
        ("The Thunder Voice", "Lightning speaks across valleys", 0.3, 0.1, 0.4),
        ("The Clear Heavens", "Stars align in ancient patterns", 0.1, 0.4, 0.4),
        ("The Howling Winds", "Gales tear at all standing", 0.5, -0.3, 0.3),
    ],
    "war": [
        ("The Border Clash", "Blood spills at the boundaries", 0.4, -0.2, 0.3),
        ("The Victorious Return", "Warriors come home triumphant", 0.1, 0.5, 0.4),
        ("The Broken Peace", "Old alliances shatter", 0.5, -0.4, 0.4),
        ("The Honorable Duel", "Champions settle disputes", 0.2, 0.2, 0.3),
        ("The Siege Lifted", "Enemies retreat in defeat", 0.0, 0.6, 0.5),
    ],
    "harvest": [
        ("The Abundant Yield", "Fields overflow with grain", -0.2, 0.6, 0.4),
        ("The Blighted Crops", "Rot spreads through stores", 0.5, -0.4, 0.3),
        ("The First Fruits", "Early harvest brings hope", -0.1, 0.4, 0.3),
        ("The Locust Swarm", "Insects devour all growth", 0.6, -0.5, 0.4),
        ("The Golden Fields", "Grain grows tall and strong", -0.2, 0.5, 0.4),
    ],
    "memory": [
        ("The Forgotten Name", "Ancient knowledge is lost", 0.3, -0.2, 0.3),
        ("The Recovered Scroll", "Old wisdom resurfaces", 0.1, 0.4, 0.4),
        ("The Prophetic Dream", "Visions reveal hidden truths", 0.2, 0.3, 0.5),
        ("The Ancestral Voice", "The dead speak to the living", 0.3, 0.2, 0.5),
        ("The Chronicle Burns", "Records are destroyed", 0.4, -0.3, 0.3),
    ],
}

# Age-specific event modifiers
AGE_EVENT_MODIFIERS = {
    Age.EMERGENCE: {"magnitude_boost": 0.1, "positive_bias": 0.1},
    Age.ORDER: {"magnitude_boost": -0.1, "positive_bias": 0.2},
    Age.STRAIN: {"magnitude_boost": 0.1, "positive_bias": -0.1},
    Age.COLLAPSE: {"magnitude_boost": 0.3, "positive_bias": -0.3},
    Age.SILENCE: {"magnitude_boost": -0.2, "positive_bias": 0.0},
    Age.REBIRTH: {"magnitude_boost": 0.0, "positive_bias": 0.2},
}


class EventGenerator:
    """Generates events based on world state."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate_event(self, age: Age, event_rate: float) -> Optional[Event]:
        """Generate an event for the current day."""
        if self.rng.random() > event_rate:
            return None

        # Choose primary domain
        primary_domain = self.rng.choice(DOMAINS)
        templates = EVENT_TEMPLATES[primary_domain]
        name, desc, fear, grat, belief = self.rng.choice(templates)

        # Maybe add secondary domain
        secondary_domain = None
        if self.rng.random() < 0.3:
            others = [d for d in DOMAINS if d != primary_domain]
            secondary_domain = self.rng.choice(others)

        # Apply age modifiers
        modifiers = AGE_EVENT_MODIFIERS[age]
        magnitude = 0.5 + self.rng.uniform(-0.2, 0.2) + modifiers["magnitude_boost"]
        magnitude = max(0.1, min(1.0, magnitude))

        # Adjust fear/gratitude based on age bias
        bias = modifiers["positive_bias"]
        fear = fear - bias * 0.2
        grat = grat + bias * 0.2

        return Event(
            name=name,
            description=desc,
            primary_domain=primary_domain,
            secondary_domain=secondary_domain,
            fear_impact=fear * magnitude,
            gratitude_impact=grat * magnitude,
            belief_impact=belief * magnitude,
            magnitude=magnitude,
        )

    def generate_disaster(self, age: Age) -> Event:
        """Generate a major disaster event."""
        disasters = [
            ("The Great Cataclysm", "The world trembles to its foundations", "sky", 0.8, -0.6, 0.7),
            ("The Plague Years", "Sickness spreads without mercy", "memory", 0.7, -0.5, 0.5),
            ("The Endless Winter", "Cold grips the land", "sky", 0.6, -0.4, 0.5),
            ("The Burning Lands", "Fire consumes all", "flame", 0.8, -0.6, 0.6),
            ("The Great Famine", "Hunger stalks every home", "harvest", 0.7, -0.5, 0.5),
            ("The War of All", "Every hand turns against another", "war", 0.8, -0.7, 0.6),
        ]
        name, desc, domain, fear, grat, belief = self.rng.choice(disasters)
        return Event(
            name=name,
            description=desc,
            primary_domain=domain,
            secondary_domain=None,
            fear_impact=fear,
            gratitude_impact=grat,
            belief_impact=belief,
            magnitude=1.0,
        )
