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

            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                space_id TEXT NOT NULL,
                date TEXT NOT NULL,
                requested_start TEXT NOT NULL,
                recommended_start TEXT,
                requested_score INTEGER,
                recommended_score INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (space_id) REFERENCES spaces(id)
            );

            CREATE TABLE IF NOT EXISTS recommendation_actions (
                recommendation_id TEXT PRIMARY KEY,
                action TEXT NOT NULL CHECK (
                    action IN ('accepted', 'ignored')
                ),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id)
                    REFERENCES recommendations(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_recommendations_user
            ON recommendations(user_id);

            CREATE INDEX IF NOT EXISTS idx_recommendations_space_date
            ON recommendations(space_id, date);

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

        

        
        
