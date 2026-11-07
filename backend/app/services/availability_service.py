from __future__ import annotations

from datetime import datetime
from typing import Any

from app.database.database import get_connection


SEVENTY_FIVE_MINUTE_SERVICES = {
    "fitness",
    "padel",
    "tennis",
    "squash",
}


def time_to_minutes(
    value: str,
) -> int:
    parsed = datetime.strptime(
        value,
        "%H:%M",
    )

    return (
        parsed.hour * 60
        + parsed.minute
    )


def minutes_to_time(
    value: int,
) -> str:
    return (
        f"{value // 60:02d}:"
        f"{value % 60:02d}"
    )


def overlaps(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:
    return (
        start_a < end_b
        and start_b < end_a
    )


def get_slot_duration(
    service_id: str,
) -> int:

    if (
        service_id
        in SEVENTY_FIVE_MINUTE_SERVICES
    ):
        return 75

    return 60


def get_booking_availability(
    service_id: str,
    space_id: str,
    date_value: str,
    start: str,
) -> dict[str, Any]:

    try:
        requested_date = (
            datetime.strptime(
                date_value,
                "%Y-%m-%d",
            )
        )

        start_minutes = (
            time_to_minutes(
                start
            )
        )

    except ValueError:
        return {
            "available": False,
            "reason": (
                "Invalid date or time."
            ),
        }

    duration = get_slot_duration(
        service_id
    )

    end_minutes = (
        start_minutes
        + duration
    )

    if end_minutes >= 24 * 60:
        return {
            "available": False,
            "reason": (
                "Requested slot exceeds "
                "the end of the day."
            ),
        }

    end = minutes_to_time(
        end_minutes
    )

    with get_connection() as connection:

        space = connection.execute(
            """
            SELECT
                id,
                name,
                capacity,
                reservable
            FROM spaces
            WHERE id = ?
            """,
            (
                space_id,
            ),
        ).fetchone()

        if space is None:
            return {
                "available": False,
                "reason": (
                    "Space does not exist."
                ),
            }

        if not bool(
            space["reservable"]
        ):
            return {
                "available": False,
                "reason": (
                    "Space is not reservable."
                ),
            }

        reservations = (
            connection.execute(
                """
                SELECT
                    start,
                    end
                FROM reservations
                WHERE
                    space_id = ?
                    AND date = ?
                    AND status = 'confirmed'
                """,
                (
                    space_id,
                    date_value,
                ),
            ).fetchall()
        )

    confirmed_reservations = 0

    for reservation in reservations:

        reserved_start = (
            time_to_minutes(
                reservation["start"]
            )
        )

        reserved_end = (
            time_to_minutes(
                reservation["end"]
            )
        )

        if overlaps(
            start_minutes,
            end_minutes,
            reserved_start,
            reserved_end,
        ):
            confirmed_reservations += 1

    capacity = int(
        space["capacity"]
    )

    remaining_capacity = max(
        capacity
        - confirmed_reservations,
        0,
    )

    return {
        "available": (
            remaining_capacity > 0
        ),
        "service_id": service_id,
        "space_id": space_id,
        "space_name": (
            space["name"]
        ),
        "date": (
            requested_date
            .date()
            .isoformat()
        ),
        "start": start,
        "end": end,
        "capacity": capacity,
        "confirmed_reservations": (
            confirmed_reservations
        ),
        "remaining_capacity": (
            remaining_capacity
        ),
        "source": (
            "current_reservations_database"
        ),
        "real_time_occupancy": False,
    }