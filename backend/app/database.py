"""SQLite setup and connection helpers for the local VoyageIQ backend."""

from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
from typing import Iterator


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "voyageiq.db"
DATABASE_PATH = Path(os.getenv("VOYAGEIQ_DB_PATH", str(DEFAULT_DATABASE_PATH)))


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open one SQLite connection and reliably commit, roll back, and close it."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create tables and add columns needed by databases from the first tutorial."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                destination TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Preserve trips created before accounts were introduced.
        trip_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(trips)")
        }
        if "user_id" not in trip_columns:
            connection.execute(
                "ALTER TABLE trips ADD COLUMN user_id TEXT REFERENCES users(id) ON DELETE CASCADE"
            )
        if "created_at" not in trip_columns:
            # SQLite cannot add a non-constant DEFAULT to a populated table.
            connection.execute("ALTER TABLE trips ADD COLUMN created_at TEXT")
        connection.execute(
            "UPDATE trips SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_plans (
                id TEXT PRIMARY KEY,
                trip_id TEXT NOT NULL UNIQUE REFERENCES trips(id) ON DELETE CASCADE,
                total_budget REAL NOT NULL,
                currency TEXT NOT NULL,
                breakdown TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS trips_user_id_idx ON trips(user_id)")
