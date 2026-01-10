"""Tests for emergent god system."""

import os
import tempfile
import pytest

from chronicle.data import Database
from chronicle.sim import SimulationEngine
from chronicle.sim.gods import (
    GodSystem,
    BELIEF_THRESHOLD,
    COHERENCE_THRESHOLD,
    CONSECUTIVE_DAYS_BIRTH,
    CONSECUTIVE_DAYS_FADE,
    FADE_THRESHOLD,
)


def test_god_birth_with_forced_beliefs():
    """Verify a god can be created when beliefs are forced above threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_god_birth.db")
        db = Database(db_path)

        engine = SimulationEngine(db, seed=99999)
        engine.initialize(fresh=True)

        citizens = engine.get_citizens()

        # Force all citizens to have high belief in "flame" domain
        # This should trigger god birth after CONSECUTIVE_DAYS_BIRTH days
        belief_level = BELIEF_THRESHOLD + 0.1

        for citizen in citizens:
            citizen.row.belief_vector["flame"] = belief_level

        # Save the forced beliefs
        for citizen in citizens:
            db.save_citizen(citizen.row)

        # Run for enough days to birth a god
        born_gods = []
        for _ in range(CONSECUTIVE_DAYS_BIRTH + 2):
            # Re-force beliefs each tick (events might change them)
            for citizen in citizens:
                citizen.row.belief_vector["flame"] = belief_level
            result = engine.tick()
            born_gods.extend(result.born_gods)

        # Verify a flame god was born
        assert len(born_gods) > 0
        flame_gods = [g for g in born_gods if g.row.domain == "flame"]
        assert len(flame_gods) > 0

        # Verify the god is in the database
        db_gods = db.get_all_gods(alive_only=True)
        assert any(g.domain == "flame" for g in db_gods)

        engine.shutdown()


def test_god_fade_with_low_beliefs():
    """Verify a god fades when beliefs drop below threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_god_fade.db")
        db = Database(db_path)

        engine = SimulationEngine(db, seed=88888)
        engine.initialize(fresh=True)

        citizens = engine.get_citizens()

        # First, birth a god by forcing high beliefs
        high_belief = BELIEF_THRESHOLD + 0.2
        for citizen in citizens:
            citizen.row.belief_vector["sky"] = high_belief
            db.save_citizen(citizen.row)

        # Run until god is born
        sky_god = None
        for _ in range(CONSECUTIVE_DAYS_BIRTH + 5):
            for citizen in citizens:
                citizen.row.belief_vector["sky"] = high_belief
            result = engine.tick()
            for god in result.born_gods:
                if god.row.domain == "sky":
                    sky_god = god
                    break
            if sky_god:
                break

        assert sky_god is not None, "Sky god should have been born"
        assert sky_god.row.alive

        # Now drop ALL beliefs to 0 to ensure events can't push sky back over threshold
        # Events can add significant belief, so we need beliefs very low
        for citizen in citizens:
            for domain in citizen.row.belief_vector:
                citizen.row.belief_vector[domain] = 0.0
            db.save_citizen(citizen.row)

        # Run until god fades - need enough days for counter to reach threshold
        # even if some days have events that temporarily boost beliefs
        faded_gods = []
        for _ in range(CONSECUTIVE_DAYS_FADE + 10):
            # Force all beliefs to 0 before each tick
            for citizen in citizens:
                for domain in citizen.row.belief_vector:
                    citizen.row.belief_vector[domain] = 0.0
            result = engine.tick()
            faded_gods.extend(result.faded_gods)
            if any(g.row.domain == "sky" for g in faded_gods):
                break

        # Verify the sky god faded
        assert len(faded_gods) > 0
        assert any(g.row.domain == "sky" for g in faded_gods)

        engine.shutdown()


def test_no_duplicate_gods_same_domain():
    """Verify only one god per domain can exist at a time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_no_dup.db")
        db = Database(db_path)

        engine = SimulationEngine(db, seed=77777)
        engine.initialize(fresh=True)

        citizens = engine.get_citizens()

        # Force high beliefs in river domain
        high_belief = BELIEF_THRESHOLD + 0.2
        for citizen in citizens:
            citizen.row.belief_vector["river"] = high_belief

        # Run for many days
        river_gods_born = []
        for _ in range(CONSECUTIVE_DAYS_BIRTH * 3):
            for citizen in citizens:
                citizen.row.belief_vector["river"] = high_belief
            result = engine.tick()
            river_gods_born.extend([g for g in result.born_gods if g.row.domain == "river"])

        # Should only have one river god
        assert len(river_gods_born) == 1

        engine.shutdown()
