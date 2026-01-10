"""Epic narration system for Living Chronicle."""

from typing import Optional
import random

from .ages import Age
from .entities import God
from .events import Event


# Epic phrases for different situations
AGE_TRANSITION_PHRASES = {
    Age.EMERGENCE: [
        "From the void, new light stirs. The Age of Emergence begins.",
        "The world awakens. An Age of Emergence dawns upon the land.",
        "Silence breaks. The Age of Emergence rises from primordial dark.",
    ],
    Age.ORDER: [
        "Laws bind the chaos. The Age of Order commences.",
        "Structure takes hold. The Age of Order begins its reign.",
        "From turbulence, pattern emerges. The Age of Order is upon us.",
    ],
    Age.STRAIN: [
        "Cracks appear in the foundation. The Age of Strain begins.",
        "Old certainties falter. The Age of Strain descends.",
        "The weight of ages bears down. Strain marks this era.",
    ],
    Age.COLLAPSE: [
        "All that was built now crumbles. The Age of Collapse is here.",
        "Pillars shatter. The Age of Collapse consumes the world.",
        "What rose must fall. The Age of Collapse begins its terrible work.",
    ],
    Age.SILENCE: [
        "The tumult fades to nothing. The Age of Silence settles.",
        "Even echoes die. The Age of Silence blankets the land.",
        "In the aftermath, only quiet remains. The Age of Silence.",
    ],
    Age.REBIRTH: [
        "From ashes, green shoots. The Age of Rebirth begins.",
        "Hope stirs in barren soil. The Age of Rebirth awakens.",
        "The cycle turns anew. Rebirth comes to a waiting world.",
    ],
}

GOD_BIRTH_PHRASES = [
    "The faithful's prayers coalesce into divine form. {name}, God of {domain}, is born!",
    "Belief made manifest! {name} rises as deity of {domain}!",
    "From collective dreams and fears, {name} awakens—a new God of {domain}!",
    "The heavens welcome a new power. {name}, Lord of {domain}, takes divine form!",
    "Mortal faith births immortal power. {name}, the {domain} God, emerges!",
]

GOD_FADE_PHRASES = [
    "{name}, God of {domain}, fades from memory. The divine light dims.",
    "Forgotten by mortals, {name} dissolves into myth and shadow.",
    "The prayers cease. {name}, once mighty, becomes mere legend.",
    "{name}'s divine essence scatters. The God of {domain} is no more.",
    "Faith wavers, and with it, {name} descends into eternal silence.",
]

EVENT_MAGNITUDE_WORDS = {
    "low": ["A minor", "A small", "A brief"],
    "medium": ["A significant", "A notable", "An important"],
    "high": ["A great", "A mighty", "A terrible"],
    "extreme": ["A cataclysmic", "An apocalyptic", "A world-shaking"],
}

DOMAIN_EPITHETS = {
    "river": "of the Waters",
    "flame": "of the Eternal Fire",
    "sky": "of the Heavens",
    "war": "of Battle",
    "harvest": "of the Bountiful Earth",
    "memory": "of the Ageless Past",
}


class Narrator:
    """Provides epic narration for simulation events."""

    def __init__(self, rng: random.Random, quiet: bool = False):
        self.rng = rng
        self.quiet = quiet

    def narrate_age_transition(self, new_age: Age) -> str:
        """Narrate an age transition."""
        phrases = AGE_TRANSITION_PHRASES[new_age]
        return self.rng.choice(phrases)

    def narrate_god_birth(self, god: God) -> str:
        """Narrate the birth of a god."""
        phrase = self.rng.choice(GOD_BIRTH_PHRASES)
        domain_title = god.row.domain.title()
        return phrase.format(name=god.row.name, domain=domain_title)

    def narrate_god_fade(self, god: God) -> str:
        """Narrate the fading of a god."""
        phrase = self.rng.choice(GOD_FADE_PHRASES)
        domain_title = god.row.domain.title()
        return phrase.format(name=god.row.name, domain=domain_title)

    def narrate_event(self, event: Event, day: int, age: Age) -> str:
        """Narrate an event."""
        # Determine magnitude description
        if event.magnitude < 0.3:
            mag_words = EVENT_MAGNITUDE_WORDS["low"]
        elif event.magnitude < 0.6:
            mag_words = EVENT_MAGNITUDE_WORDS["medium"]
        elif event.magnitude < 0.85:
            mag_words = EVENT_MAGNITUDE_WORDS["high"]
        else:
            mag_words = EVENT_MAGNITUDE_WORDS["extreme"]

        mag_word = self.rng.choice(mag_words)
        epithet = DOMAIN_EPITHETS.get(event.primary_domain, "of Unknown Power")

        lines = [f"{mag_word} omen {epithet}: {event.name}."]
        lines.append(f"  {event.description}.")

        if event.secondary_domain:
            secondary_epithet = DOMAIN_EPITHETS.get(event.secondary_domain, "")
            lines.append(f"  Echoes stir in the realm {secondary_epithet}.")

        return "\n".join(lines)

    def narrate_day_header(self, day: int, age: Age) -> str:
        """Create a day header."""
        return f"\n═══ Day {day} · Age of {age.value} ═══"

    def print_tick(self, result) -> None:
        """Print narration for a tick result."""
        if self.quiet:
            return

        from .engine import TickResult
        result: TickResult = result

        # Age transition is most important
        if result.age_transition:
            print("\n" + "=" * 60)
            print(self.narrate_age_transition(result.age_transition))
            print("=" * 60)

        # God births
        for god in result.born_gods:
            print("\n" + "★" * 40)
            print(self.narrate_god_birth(god))
            print("★" * 40)

        # God fades
        for god in result.faded_gods:
            print("\n" + "†" * 40)
            print(self.narrate_god_fade(god))
            print("†" * 40)

        # Major events (high magnitude only in normal mode)
        if result.event and result.event.magnitude >= 0.5:
            print(self.narrate_day_header(result.day, result.age))
            print(self.narrate_event(result.event, result.day, result.age))


class VerboseNarrator(Narrator):
    """Narrator that shows all events."""

    def print_tick(self, result) -> None:
        """Print narration for a tick result."""
        if self.quiet:
            return

        from .engine import TickResult
        result: TickResult = result

        print(self.narrate_day_header(result.day, result.age))

        # Age transition
        if result.age_transition:
            print("\n" + "=" * 50)
            print(self.narrate_age_transition(result.age_transition))
            print("=" * 50)

        # Events
        if result.event:
            print(self.narrate_event(result.event, result.day, result.age))
        else:
            print("  The day passes without portent.")

        # God births
        for god in result.born_gods:
            print("\n" + "★" * 40)
            print(self.narrate_god_birth(god))
            print("★" * 40)

        # God fades
        for god in result.faded_gods:
            print("\n" + "†" * 40)
            print(self.narrate_god_fade(god))
            print("†" * 40)

        # Myths created
        for myth in result.new_myths:
            print(f"  A new myth is spoken: \"{myth.row.text}\"")
