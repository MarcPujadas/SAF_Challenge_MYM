from __future__ import annotations

from datetime import date
from typing import Any

from app.database.database import (
    get_connection,
)


WEEKDAY_NAMES_CA = [
    "dilluns",
    "dimarts",
    "dimecres",
    "dijous",
    "divendres",
    "dissabte",
    "diumenge",
]


def get_user_reservations(
    user_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    space_id: str | None = None,
) -> dict[str, Any]:

    if date_from is None:
        date_from = (
            date.today()
            .isoformat()
        )

    try:
        parsed_from = (
            date.fromisoformat(
                date_from
            )
        )

    except ValueError:
        return {
            "available": False,
            "reason": (
                "Invalid date_from."
            ),
            "reservations": [],
        }

    parsed_to = None

    if date_to is not None:

        try:
            parsed_to = (
                date.fromisoformat(
                    date_to
                )
            )

        except ValueError:
            return {
                "available": False,
                "reason": (
                    "Invalid date_to."
                ),
                "reservations": [],
            }

        if parsed_to < parsed_from:
            return {
                "available": False,
                "reason": (
                    "date_to must be on or "
                    "after date_from."
                ),
                "reservations": [],
            }

    query = """
        SELECT
            r.id AS reservation_id,
            r.user_id,
            r.space_id,
            s.name AS space_name,
            sv.id AS service_id,
            sv.name AS service_name,
            r.date,
            r.start,
            r.end,
            r.status
        FROM reservations r

        JOIN spaces s
            ON s.id = r.space_id

        LEFT JOIN services sv
            ON sv.space_id = r.space_id

        WHERE
            r.user_id = ?
            AND r.status = 'confirmed'
            AND r.date >= ?
    """

    params: list[Any] = [
        user_id,
        parsed_from.isoformat(),
    ]

    if parsed_to is not None:

        query += """
            AND r.date <= ?
        """

        params.append(
            parsed_to.isoformat()
        )

    if space_id is not None:

        query += """
            AND r.space_id = ?
        """

        params.append(
            space_id
        )

    query += """
        ORDER BY
            r.date,
            r.start,
            r.id
    """

    with get_connection() as connection:

        user = connection.execute(
            """
            SELECT
                id,
                name
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            ),
        ).fetchone()

        if user is None:
            return {
                "available": False,
                "reason": (
                    "User does not exist."
                ),
                "reservations": [],
            }

        rows = connection.execute(
            query,
            params,
        ).fetchall()

    reservations = []

    for row in rows:

        reservation_date = (
            date.fromisoformat(
                row["date"]
            )
        )

        weekday = (
            WEEKDAY_NAMES_CA[
                reservation_date.weekday()
            ]
        )

        reservations.append(
            {
                "reservation_id": (
                    row["reservation_id"]
                ),
                "service_id": (
                    row["service_id"]
                ),
                "service_name": (
                    row["service_name"]
                ),
                "space_id": (
                    row["space_id"]
                ),
                "space_name": (
                    row["space_name"]
                ),
                "date": (
                    row["date"]
                ),
                "weekday": weekday,
                "start": (
                    row["start"]
                ),
                "end": (
                    row["end"]
                ),
                "status": (
                    row["status"]
                ),
            }
        )

    return {
        "available": True,
        "user_id": user_id,
        "user_name": (
            user["name"]
        ),
        "date_from": (
            parsed_from.isoformat()
        ),
        "date_to": (
            parsed_to.isoformat()
            if parsed_to is not None
            else None
        ),
        "count": len(
            reservations
        ),
        "reservations": (
            reservations
        ),
        "source": (
            "current_reservations_database"
        ),
    }