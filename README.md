# Living Chronicle

A mythic cyclical civilization simulator with emergent gods.

## Overview

Living Chronicle simulates a world that cycles through six ages: Emergence, Order, Strain, Collapse, Silence, and Rebirth. Citizens form factions, experience events, and develop beliefs. When collective belief in a domain (river, flame, sky, war, harvest, memory) reaches critical mass with sufficient coherence, gods emerge spontaneously. Gods fade when faith wanes.

## Installation

```bash
# Clone and install
cd living-chronicle
pip install -e ".[dev]"
```

## Running the Simulation

```bash
# Run for 200 days with seed 1
python -m chronicle run --days 200 --seed 1

# Run indefinitely (Ctrl+C to stop)
python -m chronicle run --seed 42

# Fresh start (clears existing chronicle.db)
python -m chronicle run --days 100 --seed 1 --fresh

# Verbose mode (shows all events)
python -m chronicle run --days 50 --seed 1 --verbose

# Check status of existing simulation
python -m chronicle status
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--days N`, `-d N` | Run for N days (default: indefinite) |
| `--seed N`, `-s N` | Random seed for deterministic runs (default: 42) |
| `--db PATH` | Database file path (default: chronicle.db) |
| `--fresh`, `-f` | Start fresh, clearing existing data |
| `--verbose`, `-v` | Show all events, not just major ones |
| `--quiet`, `-q` | Suppress narrative output |

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chronicle

# Run specific test file
pytest chronicle/tests/test_smoke.py

# Run specific test
pytest chronicle/tests/test_gods.py::test_god_birth_with_forced_beliefs
```

## Simulation Model

### Ages (Cyclical)
1. **Emergence** - New beginnings, high event rate, belief grows quickly
2. **Order** - Stability, lower event rate, balanced emotions
3. **Strain** - Tensions rise, more events, fear increases
4. **Collapse** - Catastrophe, highest event rate, fear dominates
5. **Silence** - Aftermath, few events, muted emotions
6. **Rebirth** - Hope returns, belief grows fastest

### Entities
- **Citizens**: Have beliefs (domain vectors), emotions (fear/gratitude), faction membership
- **Factions**: Groups with doctrine bias toward specific domains
- **Myths**: Event interpretations recorded by factions
- **Gods**: Emergent deities born from collective belief

### Emergent Gods
Gods do not exist at simulation start. They emerge when:
- Average belief in a domain ≥ 0.6 (threshold)
- Belief coherence (low variance) ≥ 0.5
- Conditions maintained for 5 consecutive days

Gods fade when:
- Average belief falls below 0.3
- Condition persists for 7 consecutive days

### Domains
- **River** - Water, flow, change
- **Flame** - Fire, destruction, transformation
- **Sky** - Weather, omens, the heavens
- **War** - Conflict, victory, defeat
- **Harvest** - Agriculture, abundance, famine
- **Memory** - Knowledge, ancestors, prophecy
