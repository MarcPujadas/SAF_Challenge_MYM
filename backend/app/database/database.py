from __future__ import annotations

import sqlite3
from pathlib import Path

from app.database.service_spaces import seed_service_spaces


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

            CREATE TABLE IF NOT EXISTS service_spaces (
                service_id TEXT NOT NULL,
                space_id TEXT NOT NULL,
                resource_label TEXT NOT NULL,
                person_capacity INTEGER,
                reservation_capacity INTEGER,
                capacity_mode TEXT NOT NULL CHECK (
                    capacity_mode IN ('people', 'resource_units')
                ),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (
                    is_active IN (0, 1)
                ),
                is_virtual INTEGER NOT NULL DEFAULT 0 CHECK (
                    is_virtual IN (0, 1)
                ),
                display_order INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (service_id, space_id),
                FOREIGN KEY (service_id) REFERENCES services(id),
                CHECK (person_capacity IS NULL OR person_capacity >= 0),
                CHECK (
                    reservation_capacity IS NULL
                    OR reservation_capacity >= 0
                )
            );

            CREATE TABLE IF NOT EXISTS data_sources (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                label TEXT NOT NULL,
                period_from TEXT,
                period_to TEXT,
                imported_at TEXT,
                checksum TEXT
            );

            CREATE TABLE IF NOT EXISTS historical_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                source_checksum TEXT NOT NULL,
                source_record_key TEXT NOT NULL,
                service_id TEXT,
                space_id TEXT,
                date TEXT,
                weekday INTEGER,
                start_time TEXT,
                end_time TEXT,
                raw_reservation_count REAL,
                raw_reservation_value TEXT,
                people_count REAL,
                occupied_units REAL,
                capacity_people_snapshot REAL,
                capacity_units_snapshot REAL,
                occupancy_ratio REAL,
                raw_resource_name TEXT,
                capacity_mode TEXT NOT NULL DEFAULT 'unknown' CHECK (
                    capacity_mode IN ('people', 'resource_units', 'unknown')
                ),
                mapping_status TEXT NOT NULL CHECK (
                    mapping_status IN ('mapped', 'manual_review', 'ignored')
                ),
                capacity_share REAL DEFAULT 1.0 CHECK (
                    capacity_share IS NULL OR capacity_share > 0
                ),
                imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_id, source_checksum, source_record_key),
                FOREIGN KEY (source_id) REFERENCES data_sources(id)
            );

            CREATE TRIGGER IF NOT EXISTS
            service_spaces_require_existing_physical_space_insert
            BEFORE INSERT ON service_spaces
            WHEN NEW.is_virtual = 0
                AND NOT EXISTS (
                    SELECT 1 FROM spaces WHERE id = NEW.space_id
                )
            BEGIN
                SELECT RAISE(ABORT, 'Physical service space does not exist');
            END;

            CREATE TRIGGER IF NOT EXISTS
            service_spaces_require_existing_physical_space_update
            BEFORE UPDATE OF space_id, is_virtual ON service_spaces
            WHEN NEW.is_virtual = 0
                AND NOT EXISTS (
                    SELECT 1 FROM spaces WHERE id = NEW.space_id
                )
            BEGIN
                SELECT RAISE(ABORT, 'Physical service space does not exist');
            END;

            CREATE INDEX IF NOT EXISTS idx_service_spaces_space_active
            ON service_spaces(space_id, is_active);

            CREATE INDEX IF NOT EXISTS idx_historical_usage_current_lookup
            ON historical_usage(source_id, source_checksum, service_id, date);

            CREATE INDEX IF NOT EXISTS idx_historical_usage_resource_date
            ON historical_usage(space_id, date, start_time, mapping_status);

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

            CREATE INDEX IF NOT EXISTS idx_reservations_user_date_status
            ON reservations(user_id, date, status);

            CREATE INDEX IF NOT EXISTS idx_reservations_space_date_status
            ON reservations(space_id, date, status);
            """
        )

        connection.execute(
            "INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)",
            ("demo-user", "Usuari Demo"),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO data_sources (
                id, source_type, label, imported_at
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "saf_reserves_2026",
                    "saf_historical",
                    "SAF reserves 2026",
                    None,
                ),
                (
                    "saf_guided_activities_2026",
                    "saf_historical",
                    "SAF guided activities 2026",
                    None,
                ),
            ],
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO data_sources (
                id, source_type, label, imported_at
            )
            VALUES (
                'app_live',
                'application_operational',
                'SAF Hack app reservations',
                CURRENT_TIMESTAMP
            )
            """
        )
        seed_service_spaces(connection)
