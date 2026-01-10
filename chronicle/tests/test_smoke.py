"""Smoke test for Living Chronicle - runs 10 days with deterministic seed."""

import os
import tempfile
import pytest

from chronicle.data import Database
from chronicle.sim import SimulationEngine


def test_smoke_10_days():
    """Run simulation for 10 days and verify basic functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_smoke.db")
        db = Database(db_path)

        engine = SimulationEngine(db, seed=12345)
        engine.initialize(fresh=True)

        # Run for 10 days
        results = []
        for _ in range(10):
            result = engine.tick()
            results.append(result)

        # Verify basics
        assert engine.current_day == 10
        assert len(results) == 10

        # Verify we have citizens and factions
        citizens = engine.get_citizens()
        factions = engine.get_factions()
        assert len(citizens) > 0
        assert len(factions) > 0

        # Verify age is valid
        assert engine.age_manager.current_age is not None

        # Verify determinism - run again with same seed
        db2_path = os.path.join(tmpdir, "test_smoke2.db")
        db2 = Database(db2_path)
        engine2 = SimulationEngine(db2, seed=12345)
        engine2.initialize(fresh=True)

        results2 = []
        for _ in range(10):
            result = engine2.tick()
            results2.append(result)

        # Same seed should produce same results
        assert engine2.current_day == engine.current_day
        assert engine2.age_manager.current_age == engine.age_manager.current_age

        # Same events should occur
        for r1, r2 in zip(results, results2):
            if r1.event and r2.event:
                assert r1.event.name == r2.event.name
            else:
                assert r1.event is None and r2.event is None

        engine.shutdown()
        engine2.shutdown()


def test_smoke_persistence():
    """Test that simulation state persists across restarts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_persist.db")

        # Run first session
        db1 = Database(db_path)
        engine1 = SimulationEngine(db1, seed=42)
        engine1.initialize(fresh=True)

        for _ in range(5):
            engine1.tick()

        day_after_first = engine1.current_day
        age_after_first = engine1.age_manager.current_age
        engine1.shutdown()

        # Restore and continue
        db2 = Database(db_path)
        engine2 = SimulationEngine(db2, seed=42)
        engine2.initialize(fresh=False)

        assert engine2.current_day == day_after_first
        assert engine2.age_manager.current_age == age_after_first

        for _ in range(5):
            engine2.tick()

        assert engine2.current_day == 10
        engine2.shutdown()
