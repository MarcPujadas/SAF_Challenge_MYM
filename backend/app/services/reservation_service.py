from __future__ import annotations

from contextlib import closing
from datetime import date
from typing import Any
from uuid import uuid4

from app.common import ApiError
from app.database.database import get_connection
from app.services.validation import WEEKDAYS_CA
from app.services.schedule_service import (
    overlaps,
    parse_date,
    parse_date_range,
    time_to_minutes,
    validate_reservation_slot,
)


def count_confirmed_reservations_for_slot(
    space_id: str,
    date_value: str,
    start: int,
    end: int,
    *,
    connection=None,
) -> int:
    owns_connection = connection is None
    if owns_connection:
        connection = get_connection()
    try:
        reservations = connection.execute(
            """
            SELECT start, end
            FROM reservations
            WHERE space_id = ? AND date = ? AND status = 'confirmed'
            """,
            (space_id, date_value),
        ).fetchall()
    finally:
        if owns_connection:
            connection.close()

    return sum(
        overlaps(
            start,
            end,
            time_to_minutes(reservation["start"]),
            time_to_minutes(reservation["end"]),
        )
        for reservation in reservations
    )


def create_reservation(
    user_id: str,
    space_id: str | None,
    date_value: str,
    start: str,
    end: str,
    *,
    service_id: str | None = None,
    participants_count: int | None = None,
) -> dict[str, Any]:
    reservation_date = parse_date(date_value)
    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)
    if participants_count is not None and participants_count <= 0:
        raise ApiError(
            "INVALID_PARTICIPANTS_COUNT",
            "participants_count must be greater than zero.",
        )

    with closing(get_connection()) as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            service = None
            if service_id is not None:
                service = connection.execute(
                    """
                    SELECT id, name, reservable
                    FROM services
                    WHERE id = ?
                    """,
                    (service_id,),
                ).fetchone()
                if service is None:
                    raise ApiError(
                        "INVALID_SERVICE",
                        "The requested service does not exist.",
                        404,
                    )
                if not bool(service["reservable"]):
                    raise ApiError(
                        "INVALID_SERVICE",
                        "The requested service is not reservable.",
                    )
                if space_id is not None:
                    candidates = connection.execute(
                        """
                        SELECT
                            spaces.id, spaces.name, spaces.type,
                            spaces.capacity, spaces.reservable,
                            link.capacity_mode,
                            link.reservation_capacity,
                            link.person_capacity,
                            link.service_id
                        FROM service_spaces AS link
                        JOIN spaces ON spaces.id = link.space_id
                        WHERE link.service_id = ?
                            AND link.space_id = ?
                            AND link.is_active = 1
                        """,
                        (service_id, space_id),
                    ).fetchall()
                    if not candidates:
                        raise ApiError(
                            "INVALID_SERVICE_SPACE",
                            "The requested space does not belong to the service.",
                        )
                else:
                    candidates = connection.execute(
                        """
                        SELECT
                            spaces.id, spaces.name, spaces.type,
                            spaces.capacity, spaces.reservable,
                            link.capacity_mode,
                            link.reservation_capacity,
                            link.person_capacity,
                            link.service_id
                        FROM service_spaces AS link
                        JOIN spaces ON spaces.id = link.space_id
                        WHERE link.service_id = ?
                            AND link.is_active = 1
                            AND spaces.reservable = 1
                        ORDER BY link.display_order, link.space_id
                        """,
                        (service_id,),
                    ).fetchall()
                    if not candidates:
                        raise ApiError(
                            "INVALID_SERVICE",
                            "The requested service has no reservable spaces.",
                        )
            else:
                if space_id is None:
                    raise ApiError(
                        "INVALID_SPACE",
                        "space_id or service_id is required.",
                    )
                service = connection.execute(
                    """
                    SELECT services.id, services.name, services.reservable
                    FROM services
                    JOIN service_spaces
                        ON service_spaces.service_id = services.id
                    WHERE service_spaces.space_id = ?
                        AND service_spaces.is_active = 1
                    ORDER BY service_spaces.display_order, services.id
                    LIMIT 1
                    """,
                    (space_id,),
                ).fetchone()
                if service is None:
                    service = connection.execute(
                        """
                        SELECT id, name, reservable
                        FROM services
                        WHERE space_id = ?
                        ORDER BY id
                        LIMIT 1
                        """,
                        (space_id,),
                    ).fetchone()
                candidates = connection.execute(
                    """
                    SELECT
                        spaces.id, spaces.name, spaces.type,
                        spaces.capacity, spaces.reservable,
                        link.capacity_mode,
                        link.reservation_capacity,
                        link.person_capacity,
                        link.service_id
                    FROM spaces
                    LEFT JOIN service_spaces AS link
                        ON link.space_id = spaces.id
                        AND link.service_id = ?
                        AND link.is_active = 1
                    WHERE spaces.id = ?
                    """,
                    (service["id"] if service else None, space_id),
                ).fetchall()
            if space_id is not None and not candidates:
                raise ApiError(
                    "INVALID_SPACE",
                    "The requested space does not exist.",
                    404,
                )
            if space_id is not None:
                candidate = candidates[0]
                if not bool(candidate["reservable"]):
                    raise ApiError(
                        "INVALID_SPACE",
                        "The requested space does not exist or is not reservable.",
                    )
                validate_reservation_slot(
                    candidate["id"],
                    candidate["type"],
                    reservation_date,
                    start,
                    end,
                )
                slot_candidates = candidates
            else:
                slot_candidates = []
                for candidate in candidates:
                    try:
                        validate_reservation_slot(
                            candidate["id"],
                            candidate["type"],
                            reservation_date,
                            start,
                            end,
                        )
                    except ApiError as exc:
                        if exc.code != "INVALID_TIME":
                            raise
                        continue
                    slot_candidates.append(candidate)
                if not slot_candidates:
                    raise ApiError(
                        "INVALID_TIME",
                        "The requested time does not match a valid service slot.",
                    )

            user = connection.execute(
                "SELECT id FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if user is None:
                raise ApiError(
                    "INVALID_USER",
                    "The requested user does not exist.",
                    404,
                )

            user_reservations = connection.execute(
                """
                SELECT start, end
                FROM reservations
                WHERE user_id = ? AND date = ? AND status = 'confirmed'
                """,
                (user_id, reservation_date.isoformat()),
            ).fetchall()
            if any(
                overlaps(
                    start_minutes,
                    end_minutes,
                    time_to_minutes(row["start"]),
                    time_to_minutes(row["end"]),
                )
                for row in user_reservations
            ):
                raise ApiError(
                    "RESERVATION_CONFLICT",
                    "The user already has a reservation during this time.",
                    409,
                )

            assigned_space = None
            for candidate in slot_candidates:
                if not bool(candidate["reservable"]):
                    continue

                reservations = connection.execute(
                    """
                    SELECT start, end, participants_count
                    FROM reservations
                    WHERE space_id = ?
                        AND date = ?
                        AND status = 'confirmed'
                    """,
                    (candidate["id"], reservation_date.isoformat()),
                ).fetchall()
                overlapping = [
                    row
                    for row in reservations
                    if overlaps(
                        start_minutes,
                        end_minutes,
                        time_to_minutes(row["start"]),
                        time_to_minutes(row["end"]),
                    )
                ]
                is_unit_capacity = (
                    candidate["capacity_mode"] == "resource_units"
                )
                capacity = int(
                    candidate["reservation_capacity"]
                    if is_unit_capacity
                    and candidate["reservation_capacity"] is not None
                    else candidate["person_capacity"]
                    if not is_unit_capacity
                    and candidate["person_capacity"] is not None
                    else candidate["capacity"]
                )
                occupied = (
                    len(overlapping)
                    if is_unit_capacity
                    else sum(
                        int(row["participants_count"] or 1)
                        for row in overlapping
                    )
                )
                requested_capacity = (
                    1 if is_unit_capacity else participants_count or 1
                )
                if occupied + requested_capacity <= capacity:
                    assigned_space = candidate
                    break

            if assigned_space is None:
                raise ApiError(
                    "SLOT_NOT_AVAILABLE",
                    "The requested time slot has no remaining capacity.",
                    409,
                )

            reservation_id = f"res_{uuid4().hex[:12]}"
            connection.execute(
                """
                INSERT INTO reservations (
                    id, user_id, space_id, service_id, participants_count,
                    date, start, end, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
                """,
                (
                    reservation_id,
                    user_id,
                    assigned_space["id"],
                    service["id"] if service else None,
                    participants_count,
                    reservation_date.isoformat(),
                    start,
                    end,
                ),
            )

    return {
        "reservation_id": reservation_id,
        "status": "confirmed",
        "user_id": user_id,
        "service_id": service["id"] if service else None,
        "space_id": assigned_space["id"],
        "space_name": assigned_space["name"],
        "participants_count": participants_count,
        "date": reservation_date.isoformat(),
        "start": start,
        "end": end,
    }


def list_user_reservations(
    user_id: str,
    include_cancelled: bool = False,
) -> list[dict]:
    conditions = ["r.user_id = ?"]
    if not include_cancelled:
        conditions.append("r.status = 'confirmed'")

    with closing(get_connection()) as connection:
        rows = connection.execute(
            f"""
            SELECT
                r.id AS reservation_id,
                r.space_id,
                s.name AS space_name,
                r.date,
                r.start,
                r.end,
                r.status
            FROM reservations r
            JOIN spaces s ON s.id = r.space_id
            WHERE {" AND ".join(conditions)}
            ORDER BY r.date, r.start, r.id
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_user_reservation_context(
    user_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    space_id: str | None = None,
    service_id: str | None = None,
) -> dict[str, Any]:
    date_from, date_to = parse_date_range(
        date_from if date_from is not None else date.today().isoformat(),
        date_to,
    )
    start = parse_date(date_from, "from")
    end = parse_date(date_to, "to") if date_to is not None else None

    conditions = [
        "r.user_id = ?",
        "r.status = 'confirmed'",
        "r.date >= ?",
    ]
    params: list[Any] = [user_id, start.isoformat()]
    if end is not None:
        conditions.append("r.date <= ?")
        params.append(end.isoformat())
    if space_id is not None:
        conditions.append("r.space_id = ?")
        params.append(space_id)
    if service_id is not None:
        conditions.append("r.service_id = ?")
        params.append(service_id)

    with closing(get_connection()) as connection:
        user = connection.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            raise ApiError(
                "INVALID_USER",
                "The requested user does not exist.",
                404,
            )
        rows = connection.execute(
            f"""
            SELECT
                r.id AS reservation_id,
                r.space_id,
                s.name AS space_name,
                sv.id AS service_id,
                sv.name AS service_name,
                r.date,
                r.start,
                r.end,
                r.status
            FROM reservations r
            JOIN spaces s ON s.id = r.space_id
            LEFT JOIN services sv ON sv.id = r.service_id
            WHERE {" AND ".join(conditions)}
            ORDER BY r.date, r.start, r.id
            """,
            params,
        ).fetchall()

    reservations = [
        {
            "reservation_id": row["reservation_id"],
            "service_id": row["service_id"],
            "service_name": row["service_name"],
            "space_id": row["space_id"],
            "space_name": row["space_name"],
            "date": row["date"],
            "weekday": WEEKDAYS_CA[date.fromisoformat(row["date"]).weekday()],
            "start": row["start"],
            "end": row["end"],
            "status": row["status"],
        }
        for row in rows
    ]
    return {
        "available": True,
        "user_id": user_id,
        "user_name": user["name"],
        "date_from": start.isoformat(),
        "date_to": end.isoformat() if end is not None else None,
        "count": len(reservations),
        "reservations": reservations,
        "source": "current_reservations_database",
    }


def cancel_reservation(reservation_id: str) -> dict[str, str]:
    with closing(get_connection()) as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            reservation = connection.execute(
                "SELECT id, status FROM reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
            if reservation is None:
                raise ApiError(
                    "RESERVATION_NOT_FOUND",
                    "The requested reservation does not exist.",
                    404,
                )
            if reservation["status"] == "cancelled":
                raise ApiError(
                    "RESERVATION_ALREADY_CANCELLED",
                    "The reservation is already cancelled.",
                    409,
                )
            connection.execute(
                "UPDATE reservations SET status = 'cancelled' WHERE id = ?",
                (reservation_id,),
            )
    return {"reservation_id": reservation_id, "status": "cancelled"}
