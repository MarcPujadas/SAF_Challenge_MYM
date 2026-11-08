from __future__ import annotations

import sqlite3
from collections.abc import Iterable


def register_data_source(
    connection: sqlite3.Connection,
    *,
    source_id: str,
    source_type: str,
    label: str,
    period_from: str | None,
    period_to: str | None,
    checksum: str,
) -> None:
    connection.execute(
        """
        INSERT INTO data_sources (
            id, source_type, label, period_from, period_to,
            imported_at, checksum
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ON CONFLICT(id) DO UPDATE SET
            source_type = excluded.source_type,
            label = excluded.label,
            period_from = excluded.period_from,
            period_to = excluded.period_to,
            imported_at = CASE
                WHEN data_sources.checksum IS NOT excluded.checksum
                THEN CURRENT_TIMESTAMP
                ELSE data_sources.imported_at
            END,
            checksum = excluded.checksum
        """,
        (
            source_id,
            source_type,
            label,
            period_from,
            period_to,
            checksum,
        ),
    )


def upsert_historical_usage(
    connection: sqlite3.Connection,
    rows: Iterable[dict],
) -> int:
    values = [
        (
            row["source_id"],
            row["source_checksum"],
            row["source_record_key"],
            row.get("service_id"),
            row.get("space_id"),
            row.get("date"),
            row.get("weekday"),
            row.get("start_time"),
            row.get("end_time"),
            row.get("raw_reservation_count"),
            row.get("raw_reservation_value"),
            row.get("people_count"),
            row.get("occupied_units"),
            row.get("capacity_people_snapshot"),
            row.get("capacity_units_snapshot"),
            row.get("occupancy_ratio"),
            row.get("raw_resource_name"),
            row.get("capacity_mode", "unknown"),
            row["mapping_status"],
            row.get("capacity_share", 1.0),
        )
        for row in rows
    ]
    if not values:
        return 0

    connection.executemany(
        """
        INSERT INTO historical_usage (
            source_id, source_checksum, source_record_key, service_id,
            space_id, date, weekday, start_time, end_time,
            raw_reservation_count, raw_reservation_value, people_count,
            occupied_units, capacity_people_snapshot, capacity_units_snapshot,
            occupancy_ratio, raw_resource_name, capacity_mode,
            mapping_status, capacity_share
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id, source_checksum, source_record_key)
        DO UPDATE SET
            service_id = excluded.service_id,
            space_id = excluded.space_id,
            date = excluded.date,
            weekday = excluded.weekday,
            start_time = excluded.start_time,
            end_time = excluded.end_time,
            raw_reservation_count = excluded.raw_reservation_count,
            raw_reservation_value = excluded.raw_reservation_value,
            people_count = excluded.people_count,
            occupied_units = excluded.occupied_units,
            capacity_people_snapshot = excluded.capacity_people_snapshot,
            capacity_units_snapshot = excluded.capacity_units_snapshot,
            occupancy_ratio = excluded.occupancy_ratio,
            raw_resource_name = excluded.raw_resource_name,
            capacity_mode = excluded.capacity_mode,
            mapping_status = excluded.mapping_status,
            capacity_share = excluded.capacity_share
        """,
        values,
    )
    return len(values)
