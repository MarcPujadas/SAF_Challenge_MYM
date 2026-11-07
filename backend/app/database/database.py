from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "safhack.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS spaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                capacity INTEGER NOT NULL CHECK (capacity > 0),
                reservable INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                space_id TEXT NOT NULL,
                reservable INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (space_id) REFERENCES spaces(id)
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                space_id TEXT NOT NULL,
                date TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (space_id) REFERENCES spaces(id)
            );

            CREATE INDEX IF NOT EXISTS idx_reservations_space_date
            ON reservations(space_id, date);

            CREATE INDEX IF NOT EXISTS idx_reservations_user_date
            ON reservations(user_id, date);
            """
        )

        connection.execute(
            "INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)",
            ("demo-user", "Usuari Demo"),
        )

        spaces = [
            ("fitness", "Sala Fitness", "fitness", 120, 1),
            ("pool", "Piscina", "pool", 40, 1),
            ("padel-1", "Pista de pàdel 1", "court", 1, 1),
        ]
        connection.executemany(
            """
            INSERT OR IGNORE INTO spaces (id, name, type, capacity, reservable)
            VALUES (?, ?, ?, ?, ?)
            """,
            spaces,
        )

        services = [
            (
                "fitness",
                "Fitness",
                "Sala de fitness del SAF",
                "fitness",
                1,
            ),
            (
                "pool",
                "Piscina",
                "Accés a la piscina del SAF",
                "pool",
                1,
            ),
            (
                "padel",
                "Pàdel",
                "Reserva d'una pista de pàdel",
                "padel-1",
                1,
            ),
        ]
        connection.executemany(
            """
            INSERT OR IGNORE INTO services
                (id, name, description, space_id, reservable)
            VALUES (?, ?, ?, ?, ?)
            """,
            services,
        )
