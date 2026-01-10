"""SQLite database interface for Living Chronicle."""

import sqlite3
from pathlib import Path
from typing import Optional

from .models import CitizenRow, FactionRow, MythRow, GodRow, WorldStateRow


class Database:
    """SQLite database for simulation persistence."""

    def __init__(self, db_path: str = "chronicle.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to the database and create tables if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS world_state (
                id INTEGER PRIMARY KEY,
                current_day INTEGER NOT NULL,
                current_age TEXT NOT NULL,
                age_day_counter INTEGER NOT NULL,
                seed INTEGER NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                doctrine_bias TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citizens (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                faction_id INTEGER,
                belief_vector TEXT NOT NULL,
                fear REAL NOT NULL,
                gratitude REAL NOT NULL,
                alive INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (faction_id) REFERENCES factions(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS myths (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                faction_id INTEGER,
                domain TEXT NOT NULL,
                confidence REAL NOT NULL,
                day_created INTEGER NOT NULL,
                FOREIGN KEY (faction_id) REFERENCES factions(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gods (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                belief_strength REAL NOT NULL,
                coherence REAL NOT NULL,
                alive INTEGER NOT NULL DEFAULT 1,
                birth_day INTEGER NOT NULL,
                death_day INTEGER,
                consecutive_strong_days INTEGER NOT NULL DEFAULT 0,
                consecutive_weak_days INTEGER NOT NULL DEFAULT 0
            )
        """)

        self.conn.commit()

    # World State operations
    def get_world_state(self) -> Optional[WorldStateRow]:
        """Get the current world state."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM world_state WHERE id = 1")
        row = cursor.fetchone()
        return WorldStateRow.from_db_row(row) if row else None

    def save_world_state(self, state: WorldStateRow) -> None:
        """Save or update the world state."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO world_state
            (id, current_day, current_age, age_day_counter, seed)
            VALUES (1, ?, ?, ?, ?)
        """, (state.current_day, state.current_age, state.age_day_counter, state.seed))
        self.conn.commit()

    # Faction operations
    def save_faction(self, faction: FactionRow) -> int:
        """Save a faction and return its ID."""
        cursor = self.conn.cursor()
        if faction.id is None:
            cursor.execute(
                "INSERT INTO factions (name, doctrine_bias) VALUES (?, ?)",
                (faction.name, faction.to_db_tuple()[2])
            )
            faction.id = cursor.lastrowid
        else:
            cursor.execute(
                "UPDATE factions SET name=?, doctrine_bias=? WHERE id=?",
                (faction.name, faction.to_db_tuple()[2], faction.id)
            )
        self.conn.commit()
        return faction.id

    def get_all_factions(self) -> list[FactionRow]:
        """Get all factions."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM factions")
        return [FactionRow.from_db_row(row) for row in cursor.fetchall()]

    def get_faction(self, faction_id: int) -> Optional[FactionRow]:
        """Get a faction by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM factions WHERE id = ?", (faction_id,))
        row = cursor.fetchone()
        return FactionRow.from_db_row(row) if row else None

    # Citizen operations
    def save_citizen(self, citizen: CitizenRow) -> int:
        """Save a citizen and return their ID."""
        cursor = self.conn.cursor()
        if citizen.id is None:
            t = citizen.to_db_tuple()
            cursor.execute(
                """INSERT INTO citizens
                   (name, faction_id, belief_vector, fear, gratitude, alive)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                t[1:]
            )
            citizen.id = cursor.lastrowid
        else:
            t = citizen.to_db_tuple()
            cursor.execute(
                """UPDATE citizens SET
                   name=?, faction_id=?, belief_vector=?, fear=?, gratitude=?, alive=?
                   WHERE id=?""",
                (*t[1:], t[0])
            )
        self.conn.commit()
        return citizen.id

    def get_all_citizens(self, alive_only: bool = True) -> list[CitizenRow]:
        """Get all citizens."""
        cursor = self.conn.cursor()
        if alive_only:
            cursor.execute("SELECT * FROM citizens WHERE alive = 1")
        else:
            cursor.execute("SELECT * FROM citizens")
        return [CitizenRow.from_db_row(row) for row in cursor.fetchall()]

    def get_citizens_by_faction(self, faction_id: int) -> list[CitizenRow]:
        """Get all citizens in a faction."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM citizens WHERE faction_id = ? AND alive = 1",
            (faction_id,)
        )
        return [CitizenRow.from_db_row(row) for row in cursor.fetchall()]

    # Myth operations
    def save_myth(self, myth: MythRow) -> int:
        """Save a myth and return its ID."""
        cursor = self.conn.cursor()
        if myth.id is None:
            t = myth.to_db_tuple()
            cursor.execute(
                """INSERT INTO myths
                   (text, faction_id, domain, confidence, day_created)
                   VALUES (?, ?, ?, ?, ?)""",
                t[1:]
            )
            myth.id = cursor.lastrowid
        self.conn.commit()
        return myth.id

    def get_all_myths(self) -> list[MythRow]:
        """Get all myths."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM myths ORDER BY day_created DESC")
        return [MythRow.from_db_row(row) for row in cursor.fetchall()]

    # God operations
    def save_god(self, god: GodRow) -> int:
        """Save a god and return their ID."""
        cursor = self.conn.cursor()
        if god.id is None:
            t = god.to_db_tuple()
            cursor.execute(
                """INSERT INTO gods
                   (name, domain, belief_strength, coherence, alive, birth_day,
                    death_day, consecutive_strong_days, consecutive_weak_days)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                t[1:]
            )
            god.id = cursor.lastrowid
        else:
            t = god.to_db_tuple()
            cursor.execute(
                """UPDATE gods SET
                   name=?, domain=?, belief_strength=?, coherence=?, alive=?,
                   birth_day=?, death_day=?, consecutive_strong_days=?,
                   consecutive_weak_days=?
                   WHERE id=?""",
                (*t[1:], t[0])
            )
        self.conn.commit()
        return god.id

    def get_all_gods(self, alive_only: bool = False) -> list[GodRow]:
        """Get all gods."""
        cursor = self.conn.cursor()
        if alive_only:
            cursor.execute("SELECT * FROM gods WHERE alive = 1")
        else:
            cursor.execute("SELECT * FROM gods")
        return [GodRow.from_db_row(row) for row in cursor.fetchall()]

    def get_god_by_domain(self, domain: str, alive_only: bool = True) -> Optional[GodRow]:
        """Get a god by domain."""
        cursor = self.conn.cursor()
        if alive_only:
            cursor.execute(
                "SELECT * FROM gods WHERE domain = ? AND alive = 1",
                (domain,)
            )
        else:
            cursor.execute("SELECT * FROM gods WHERE domain = ?", (domain,))
        row = cursor.fetchone()
        return GodRow.from_db_row(row) if row else None

    def clear_all(self) -> None:
        """Clear all data (for fresh starts)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM myths")
        cursor.execute("DELETE FROM citizens")
        cursor.execute("DELETE FROM gods")
        cursor.execute("DELETE FROM factions")
        cursor.execute("DELETE FROM world_state")
        self.conn.commit()
