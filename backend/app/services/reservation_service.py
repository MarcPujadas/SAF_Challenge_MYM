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
    space_id: str,
    date_value: str,
    start: str,
    end: str,
) -> dict[str, str]:
    reservation_date = parse_date(date_value)
    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)

    with closing(get_connection()) as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            space = connection.execute(
                """
                SELECT id, type, capacity, reservable
                FROM spaces
                WHERE id = ?
                """,
                (space_id,),
            ).fetchone()
            if space is None or not bool(space["reservable"]):
                raise ApiError(
                    "INVALID_SPACE",
                    "The requested space does not exist or is not reservable.",
                    404 if space is None else 400,
                )
            validate_reservation_slot(
                space["id"],
                space["type"],
                reservation_date,
                start,
                end,
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

            concurrent = count_confirmed_reservations_for_slot(
                space_id,
                reservation_date.isoformat(),
                start_minutes,
                end_minutes,
                connection=connection,
            )
            if concurrent >= int(space["capacity"]):
                raise ApiError(
                    "SLOT_NOT_AVAILABLE",
                    "The requested time slot has no remaining capacity.",
                    409,
                )

            reservation_id = f"res_{uuid4().hex[:12]}"
            connection.execute(
                """
                INSERT INTO reservations (
                    id, user_id, space_id, date, start, end, status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
                """,
                (
                    reservation_id,
                    user_id,
                    space_id,
                    reservation_date.isoformat(),
                    start,
                    end,
                ),
            )

    return {
        "reservation_id": reservation_id,
        "status": "confirmed",
        "user_id": user_id,
        "space_id": space_id,
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
            LEFT JOIN services sv ON sv.space_id = r.space_id
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
