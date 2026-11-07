from __future__ import annotations

from contextlib import closing
from datetime import date
from typing import Any

import pandas as pd

from app.database.database import get_connection
from app.services.historical_service import (
    get_historical_occupancy_by_date,
    get_historical_occupancy_by_hour,
)


def get_admin_reservations() -> list[dict[str, Any]]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
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
            WHERE r.status != 'cancelled'
            ORDER BY r.date, r.start, r.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_admin_summary() -> dict[str, Any]:
    reservations = get_admin_reservations()
    space_counts: dict[str, int] = {}
    space_names: dict[str, str] = {}
    hour_counts: dict[str, int] = {}
    for reservation in reservations:
        space_id = reservation["space_id"]
        space_names[space_id] = reservation["space_name"]
        hour = reservation["start"][:5]
        space_counts[space_id] = space_counts.get(space_id, 0) + 1
        hour_counts[hour] = hour_counts.get(hour, 0) + 1

    busiest_space_id = min(
        space_counts,
        key=lambda current_id: (-space_counts[current_id], current_id),
        default=None,
    )
    busiest_hour = min(
        hour_counts,
        key=lambda hour: (-hour_counts[hour], hour),
        default=None,
    )
    today_count = sum(
        reservation["date"] == date.today().isoformat()
        for reservation in reservations
    )
    return {
        "total_reservations": len(reservations),
        "reservations_today": today_count,
        "busiest_space": (
            {
                "id": busiest_space_id,
                "name": space_names[busiest_space_id],
            }
            if busiest_space_id is not None
            else None
        ),
        "busiest_hour": busiest_hour,
    }


def get_admin_stats() -> dict[str, Any]:
    reservations = get_admin_reservations()
    historical = get_historical_occupancy_by_hour()
    space_counts: dict[str, int] = {}
    space_names: dict[str, str] = {}
    for reservation in reservations:
        space_id = reservation["space_id"]
        space_counts[space_id] = space_counts.get(space_id, 0) + 1
        space_names[space_id] = reservation["space_name"]

    most_used_spaces = [
        {
            "space_id": space_id,
            "name": space_names[space_id],
            "total_reservations": count,
        }
        for space_id, count in sorted(
            space_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    busiest_hour = None
    quietest_hour = None
    if not historical.empty:
        hourly_scores = historical.groupby("start_time")[
            "occupancy_score"
        ].mean()
        if not hourly_scores.empty:
            busiest_hour = min(
                hourly_scores.index,
                key=lambda hour: (-hourly_scores[hour], hour),
            )
            quietest_hour = min(
                hourly_scores.index,
                key=lambda hour: (hourly_scores[hour], hour),
            )
    return {
        "total_reservations": len(reservations),
        "reservations_created_by_app": len(reservations),
        "most_used_spaces": most_used_spaces,
        "busiest_hour": busiest_hour,
        "quietest_hour": quietest_hour,
    }


def get_admin_occupancy(
    date_from: str | None = None,
    date_to: str | None = None,
    space_id: str | None = None,
) -> dict[str, Any]:
    records = get_historical_occupancy_by_date(
        date_from=date_from,
        date_to=date_to,
        space_id=space_id,
    )
    space_ids = (
        [space_id]
        if space_id is not None
        else sorted(records["space_id"].unique())
    )
    spaces = []
    for current_space_id in space_ids:
        space_records = records[records["space_id"] == current_space_id]
        if space_records.empty:
            average_score = peak_hour = lowest_hour = None
        else:
            average_score = int(round(space_records["occupancy_score"].mean()))
            hourly_scores = space_records.groupby("start_time")[
                "occupancy_score"
            ].mean()
            peak_hour = min(
                hourly_scores.index,
                key=lambda hour: (-hourly_scores[hour], hour),
            )
            lowest_hour = min(
                hourly_scores.index,
                key=lambda hour: (hourly_scores[hour], hour),
            )
        spaces.append(
            {
                "space_id": current_space_id,
                "average_occupancy_score": average_score,
                "peak_hour": peak_hour,
                "lowest_hour": lowest_hour,
            }
        )
    return {"period": {"from": date_from, "to": date_to}, "spaces": spaces}


def get_admin_reservation_rows() -> list[dict[str, Any]]:
    return [
        {
            "reservation_id": row["reservation_id"],
            "space_id": row["space_id"],
            "date": row["date"],
            "start": row["start"],
            "status": row["status"],
        }
        for row in get_admin_reservations()
    ]


def get_empty_historical_records() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "space_id",
            "date",
            "start_time",
            "reservations",
            "occupancy_score",
            "occupancy_level",
        ]
    )
