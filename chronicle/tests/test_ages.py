"""Tests for age cycle transitions."""

import random
import pytest

from chronicle.sim.ages import Age, AgeManager, AGE_TRAITS


def test_age_cycle_order():
    """Verify ages cycle in correct order: Emergence -> Order -> Strain -> Collapse -> Silence -> Rebirth -> Emergence."""
    expected_order = [
        Age.EMERGENCE,
        Age.ORDER,
        Age.STRAIN,
        Age.COLLAPSE,
        Age.SILENCE,
        Age.REBIRTH,
        Age.EMERGENCE,  # cycles back
    ]

    # Verify next() method
    for i in range(len(expected_order) - 1):
        assert expected_order[i].next() == expected_order[i + 1]


def test_age_manager_starts_at_emergence():
    """Verify new simulations start at Age of Emergence."""
    rng = random.Random(42)
    manager = AgeManager.new(rng)
    assert manager.current_age == Age.EMERGENCE


def test_age_transition_occurs():
    """Verify age transitions occur after duration is met."""
    rng = random.Random(12345)
    manager = AgeManager.new(rng)

    # Force a short duration
    manager.age_duration = 5

    # Tick until transition
    transitions = []
    for _ in range(100):  # More than enough
        result = manager.tick()
        if result:
            transitions.append(result)
            if len(transitions) >= 2:
                break

    # Should have transitioned at least twice
    assert len(transitions) >= 2
    assert transitions[0] == Age.ORDER
    assert transitions[1] == Age.STRAIN


def test_full_cycle():
    """Verify a full cycle of all ages can complete."""
    rng = random.Random(54321)
    manager = AgeManager.new(rng)

    # Track all ages we pass through
    ages_seen = [manager.current_age]

    # Force short durations and run through a full cycle
    max_ticks = 1000
    for _ in range(max_ticks):
        manager.age_duration = min(manager.age_duration, 3)  # Cap duration
        result = manager.tick()
        if result and result not in ages_seen:
            ages_seen.append(result)
        if len(ages_seen) >= 6:
            break

    # Should have seen all 6 ages
    assert len(ages_seen) >= 6
    assert Age.EMERGENCE in ages_seen
    assert Age.ORDER in ages_seen
    assert Age.STRAIN in ages_seen
    assert Age.COLLAPSE in ages_seen
    assert Age.SILENCE in ages_seen
    assert Age.REBIRTH in ages_seen


def test_age_traits_exist():
    """Verify all ages have defined traits."""
    for age in Age:
        assert age in AGE_TRAITS
        traits = AGE_TRAITS[age]
        assert "min_days" in traits
        assert "max_days" in traits
        assert "event_rate" in traits
        assert "belief_growth" in traits
        assert "fear_modifier" in traits
        assert "gratitude_modifier" in traits
        assert traits["min_days"] <= traits["max_days"]


def test_age_restoration():
    """Verify age manager can be restored from saved state."""
    rng = random.Random(99999)
    manager = AgeManager.new(rng)

    # Advance a few days
    for _ in range(10):
        manager.tick()

    # Save state
    saved_age = manager.current_age.value
    saved_counter = manager.day_counter

    # Restore
    rng2 = random.Random(99999)
    restored = AgeManager.from_state(saved_age, saved_counter, rng2)

    assert restored.current_age == manager.current_age
    assert restored.day_counter == manager.day_counter
