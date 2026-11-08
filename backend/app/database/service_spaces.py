from __future__ import annotations

import sqlite3

from app.config.service_spaces import SERVICE_SPACE_MAPPINGS


def seed_service_spaces(connection: sqlite3.Connection) -> None:
    """Idempotently add known resource links without changing legacy services."""
    for resource in SERVICE_SPACE_MAPPINGS:
        service = connection.execute(
            "SELECT id FROM services WHERE id = ?",
            (resource.service_id,),
        ).fetchone()
        if service is None:
            continue

        space = connection.execute(
            "SELECT capacity FROM spaces WHERE id = ?",
            (resource.space_id,),
        ).fetchone()
        is_virtual = (
            space is None or resource.materialize_as_reservable_space
        )
        if is_virtual and not resource.allow_virtual:
            continue
        if is_virtual and resource.materialize_as_reservable_space:
            connection.execute(
                """
                INSERT OR IGNORE INTO spaces (
                    id, name, type, capacity, reservable
                )
                VALUES (?, ?, 'court', 1, 1)
                """,
                (resource.space_id, resource.label),
            )
            space = connection.execute(
                "SELECT capacity FROM spaces WHERE id = ?",
                (resource.space_id,),
            ).fetchone()

        person_capacity = (
            int(space["capacity"])
            if space is not None and resource.capacity_mode == "people"
            else None
        )
        connection.execute(
            """
            INSERT INTO service_spaces (
                service_id,
                space_id,
                resource_label,
                person_capacity,
                reservation_capacity,
                capacity_mode,
                is_active,
                is_virtual,
                display_order
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(service_id, space_id)
            DO UPDATE SET
                resource_label = excluded.resource_label,
                person_capacity = excluded.person_capacity,
                reservation_capacity = excluded.reservation_capacity,
                capacity_mode = excluded.capacity_mode,
                is_active = excluded.is_active,
                is_virtual = excluded.is_virtual,
                display_order = excluded.display_order
            """,
            (
                resource.service_id,
                resource.space_id,
                resource.label,
                person_capacity,
                resource.reservation_capacity,
                resource.capacity_mode,
                int(is_virtual),
                resource.display_order,
            ),
        )
