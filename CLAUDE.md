# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run simulation
python -m chronicle run --days 200 --seed 1
python -m chronicle run --days 50 --seed 1 --fresh --verbose

# Run all tests
pytest

# Run specific test file
pytest chronicle/tests/test_smoke.py

# Run single test
pytest chronicle/tests/test_gods.py::test_god_birth_with_forced_beliefs -v

# Install for development
pip install -e ".[dev]"
```

## Architecture

```
chronicle/
├── __main__.py      # CLI entry point (argparse)
├── data/            # Persistence layer
│   ├── database.py  # SQLite interface (Database class)
│   └── models.py    # Data row classes (CitizenRow, GodRow, etc.)
└── sim/             # Simulation logic
    ├── engine.py    # Main SimulationEngine - orchestrates ticks
    ├── ages.py      # Age enum and AgeManager (cycle: Emergence→Order→Strain→Collapse→Silence→Rebirth)
    ├── entities.py  # Entity classes (Citizen, Faction, Myth, God) wrapping row data
    ├── events.py    # EventGenerator and Event dataclass
    ├── gods.py      # GodSystem - handles emergent god birth/fade logic
    └── narration.py # Narrator classes for epic console output
```

## Key Patterns

**Tick-based simulation**: `SimulationEngine.tick()` advances one in-game day. Each tick: age manager advances → event generated → event applied to citizens → god system processes births/fades → state persisted.

**Entity/Row separation**: Entities (e.g., `Citizen`) wrap row objects (e.g., `CitizenRow`). Rows handle serialization to/from SQLite. Entities provide behavior methods.

**Emergent gods**: Gods are not predefined. `GodSystem.process_gods()` aggregates citizen beliefs per domain. When aggregate belief and coherence exceed thresholds for consecutive days, a god is born. Similar logic for fading.

**Deterministic runs**: Same `--seed` produces identical simulation. RNG passed to all generators. Tests rely on this for reproducibility.

## Domain Constants

Defined in `chronicle/data/models.py`:
```python
DOMAINS = ["river", "flame", "sky", "war", "harvest", "memory"]
```

## God Emergence Thresholds

Defined in `chronicle/sim/gods.py`:
- `BELIEF_THRESHOLD = 0.6` - minimum average belief to birth
- `COHERENCE_THRESHOLD = 0.5` - minimum coherence (1 - variance)
- `CONSECUTIVE_DAYS_BIRTH = 5` - days above threshold to birth
- `CONSECUTIVE_DAYS_FADE = 7` - days below threshold to fade
- `FADE_THRESHOLD = 0.3` - belief below this starts fade counter
