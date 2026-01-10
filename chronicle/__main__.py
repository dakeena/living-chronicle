"""CLI entry point for Living Chronicle."""

import argparse
import sys
from pathlib import Path

from .data import Database
from .sim import SimulationEngine, Narrator, VerboseNarrator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="chronicle",
        description="Living Chronicle - A mythic cyclical civilization simulator",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the simulation")
    run_parser.add_argument(
        "--days", "-d",
        type=int,
        default=None,
        help="Number of days to simulate (default: run indefinitely)",
    )
    run_parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for deterministic runs (default: 42)",
    )
    run_parser.add_argument(
        "--db",
        type=str,
        default="chronicle.db",
        help="Database file path (default: chronicle.db)",
    )
    run_parser.add_argument(
        "--fresh", "-f",
        action="store_true",
        help="Start a fresh simulation (clears existing data)",
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all events, not just major ones",
    )
    run_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress narrative output",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show simulation status")
    status_parser.add_argument(
        "--db",
        type=str,
        default="chronicle.db",
        help="Database file path (default: chronicle.db)",
    )

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    """Run the simulation."""
    import random

    db = Database(args.db)
    rng = random.Random(args.seed)

    if args.verbose:
        narrator = VerboseNarrator(rng, quiet=args.quiet)
    else:
        narrator = Narrator(rng, quiet=args.quiet)

    engine = SimulationEngine(db, seed=args.seed, narrator=narrator.print_tick)

    try:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║           LIVING CHRONICLE                               ║")
        print("║     A Mythic Cyclical Civilization Simulator             ║")
        print("╚══════════════════════════════════════════════════════════╝")

        engine.initialize(fresh=args.fresh)

        if args.fresh:
            print(f"\nA new world awakens. Seed: {args.seed}")
            factions = engine.get_factions()
            print(f"  {len(factions)} factions emerge from the primordial chaos:")
            for faction in factions:
                print(f"    • {faction.row.name}")
            print(f"  {len(engine.get_citizens())} souls walk the land.")
        else:
            print(f"\nThe chronicle continues from day {engine.current_day}...")

        print("\n" + "─" * 60)

        if args.days:
            print(f"Simulating {args.days} days...")
        else:
            print("Simulating indefinitely (Ctrl+C to stop)...")

        engine.run(days=args.days)

        if args.days:
            print("\n" + "─" * 60)
            print(f"Simulation complete. {args.days} days have passed.")
            _print_summary(engine)

    except KeyboardInterrupt:
        print("\n\nThe chronicle pauses...")
        _print_summary(engine)
    finally:
        engine.shutdown()

    return 0


def _print_summary(engine: SimulationEngine) -> None:
    """Print a summary of the simulation state."""
    print("\n═══ CHRONICLE SUMMARY ═══")
    print(f"Day: {engine.current_day}")
    print(f"Age: {engine.age_manager.current_age.value}")

    gods = engine.db.get_all_gods(alive_only=True)
    if gods:
        print(f"\nLiving Gods ({len(gods)}):")
        for god in gods:
            print(f"  • {god.name}, God of {god.domain.title()}")
            print(f"    (Belief: {god.belief_strength:.2f}, Born day {god.birth_day})")
    else:
        print("\nNo gods walk among mortals.")

    dead_gods = engine.db.get_all_gods(alive_only=False)
    dead_gods = [g for g in dead_gods if not g.alive]
    if dead_gods:
        print(f"\nFallen Gods ({len(dead_gods)}):")
        for god in dead_gods:
            print(f"  • {god.name}, once of {god.domain.title()} (days {god.birth_day}-{god.death_day})")


def cmd_status(args: argparse.Namespace) -> int:
    """Show simulation status."""
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"No chronicle found at {args.db}")
        return 1

    db = Database(args.db)
    db.connect()

    state = db.get_world_state()
    if state is None:
        print("Chronicle exists but contains no world state.")
        db.close()
        return 1

    print("═══ CHRONICLE STATUS ═══")
    print(f"Day: {state.current_day}")
    print(f"Age: {state.current_age}")
    print(f"Seed: {state.seed}")

    citizens = db.get_all_citizens()
    factions = db.get_all_factions()
    gods = db.get_all_gods()
    myths = db.get_all_myths()

    print(f"\nPopulation: {len(citizens)} citizens")
    print(f"Factions: {len(factions)}")
    print(f"Gods (living/total): {len([g for g in gods if g.alive])}/{len(gods)}")
    print(f"Myths recorded: {len(myths)}")

    db.close()
    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "status":
        return cmd_status(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
