from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from app.database.database import get_connection
from app.services.historical_service import (
    get_historical_occupancy_by_date,
    occupancy_level,
)


WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def _historical_records(
    space_id: str | None,
    date_from: str | None,
    date_to: str | None,
) -> pd.DataFrame:
    records = get_historical_occupancy_by_date(
        date_from=date_from,
        date_to=date_to,
        space_id=space_id,
    )
    if records.empty:
        return records
    records = records.copy()
    records["weekday"] = records["date"].map(
        lambda value: date.fromisoformat(value).weekday()
    )
    return records


def _score_fields(score: float) -> tuple[int, str]:
    rounded_score = int(round(score))
    return rounded_score, occupancy_level(rounded_score)


def get_occupancy_by_weekday(
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    records = _historical_records(space_id, date_from, date_to)
    if records.empty:
        return []

    spaces = []
    for current_space_id, space_records in records.groupby("space_id"):
        weekdays = []
        for weekday, weekday_records in space_records.groupby("weekday"):
            mean_score = float(weekday_records["occupancy_score"].mean())
            score, level = _score_fields(mean_score)
            weekdays.append(
                {
                    "day_of_week": WEEKDAY_NAMES[int(weekday)],
                    "average_occupancy_score": score,
                    "occupancy_level": level,
                    "samples": int(weekday_records["occupancy_score"].count()),
                }
            )
        weekdays.sort(
            key=lambda item: WEEKDAY_NAMES.index(item["day_of_week"])
        )
        spaces.append(
            {
                "space_id": current_space_id,
                "weekdays": weekdays,
            }
        )
    return spaces


def get_occupancy_slot_rankings(
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    records = _historical_records(space_id, date_from, date_to)
    if records.empty:
        return []

    records = records[records["occupancy_score"].notna()]
    if records.empty:
        return []

    spaces = []
    for current_space_id, space_records in records.groupby("space_id"):
        slots = []
        for (weekday, hour), slot_records in space_records.groupby(
            ["weekday", "start_time"]
        ):
            mean_score = float(slot_records["occupancy_score"].mean())
            score, level = _score_fields(mean_score)
            slots.append(
                {
                    "day_of_week": WEEKDAY_NAMES[int(weekday)],
                    "hour": hour,
                    "occupancy_score": score,
                    "occupancy_level": level,
                    "samples": int(slot_records["occupancy_score"].count()),
                }
            )
        busiest = sorted(
            slots,
            key=lambda item: (
                -item["occupancy_score"],
                WEEKDAY_NAMES.index(item["day_of_week"]),
                item["hour"],
            ),
        )[:5]
        quietest = sorted(
            slots,
            key=lambda item: (
                item["occupancy_score"],
                WEEKDAY_NAMES.index(item["day_of_week"]),
                item["hour"],
            ),
        )[:5]
        spaces.append(
            {
                "space_id": current_space_id,
                "most_saturated": busiest,
                "quietest": quietest,
            }
        )
    return spaces


def get_space_utilization(
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    records = _historical_records(space_id, date_from, date_to)
    space_ids = (
        [space_id]
        if space_id is not None
        else sorted(records["space_id"].unique())
    )
    return [
        {
            "space_id": current_space_id,
            "utilization_percentage": None,
            "status": "insufficient_data",
            "reason": "historical_capacity_unavailable",
            "samples": (
                int(
                    records.loc[
                        records["space_id"] == current_space_id,
                        "reservations",
                    ].count()
                )
                if not records.empty
                else 0
            ),
        }
        for current_space_id in space_ids
    ]


def get_occupancy_trend(
    group_by: str,
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    records = _historical_records(space_id, date_from, date_to)
    if records.empty:
        return []

    if group_by == "week":
        records["period"] = records["date"].map(
            lambda value: (
                date.fromisoformat(value)
                - timedelta(days=date.fromisoformat(value).weekday())
            ).isoformat()
        )
    else:
        records["period"] = records["date"].str.slice(0, 7)

    trends = []
    for (current_space_id, period), period_records in records.groupby(
        ["space_id", "period"],
        sort=True,
    ):
        mean_score = float(period_records["occupancy_score"].mean())
        score, level = _score_fields(mean_score)
        trends.append(
            {
                "space_id": current_space_id,
                "period": period,
                "average_occupancy_score": score,
                "occupancy_level": level,
                "samples": int(period_records["occupancy_score"].count()),
            }
        )
    return trends


def get_cancellation_analytics(
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    conditions = []
    params = []
    if space_id is not None:
        conditions.append("space_id = ?")
        params.append(space_id)
    if date_from is not None:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("date <= ?")
        params.append(date_to)
    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions
        else ""
    )

    with get_connection() as connection:
        reservations = connection.execute(
            f"""
            SELECT space_id, date, start, status
            FROM reservations
            {where_clause}
            ORDER BY space_id, date, start
            """,
            params,
        ).fetchall()

    grouped: dict[str, list] = {}
    for reservation in reservations:
        grouped.setdefault(reservation["space_id"], []).append(reservation)
    if space_id is not None:
        grouped.setdefault(space_id, [])

    spaces = []
    for current_space_id, space_reservations in sorted(grouped.items()):
        total = len(space_reservations)
        confirmed = sum(
            reservation["status"] == "confirmed"
            for reservation in space_reservations
        )
        cancelled = sum(
            reservation["status"] == "cancelled"
            for reservation in space_reservations
        )
        cancellation_counts: dict[tuple[int, str], int] = {}
        for reservation in space_reservations:
            if reservation["status"] != "cancelled":
                continue
            weekday = date.fromisoformat(reservation["date"]).weekday()
            key = (weekday, reservation["start"])
            cancellation_counts[key] = cancellation_counts.get(key, 0) + 1
        cancellation_slots = [
            {
                "day_of_week": WEEKDAY_NAMES[weekday],
                "hour": hour,
                "cancelled_reservations": count,
            }
            for (weekday, hour), count in sorted(
                cancellation_counts.items(),
                key=lambda item: (
                    -item[1],
                    item[0][0],
                    item[0][1],
                ),
            )[:5]
        ]
        spaces.append(
            {
                "space_id": current_space_id,
                "total_reservations": total,
                "confirmed_reservations": confirmed,
                "cancelled_reservations": cancelled,
                "cancellation_rate": (
                    round(cancelled / total * 100, 1)
                    if total
                    else None
                ),
                "most_cancelled_slots": cancellation_slots,
            }
        )
    return spaces


def get_safi_impact(
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    conditions = []
    params = []
    if space_id is not None:
        conditions.append("r.space_id = ?")
        params.append(space_id)
    if date_from is not None:
        conditions.append("r.date >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("r.date <= ?")
        params.append(date_to)
    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions
        else ""
    )

    with get_connection() as connection:
        recommendations = connection.execute(
            f"""
            SELECT
                r.space_id,
                r.requested_start,
                r.recommended_start,
                r.requested_score,
                r.recommended_score,
                a.action
            FROM recommendations r
            LEFT JOIN recommendation_actions a
                ON a.recommendation_id = r.id
            {where_clause}
            ORDER BY r.space_id, r.created_at, r.id
            """,
            params,
        ).fetchall()

    grouped: dict[str, list] = {}
    for recommendation in recommendations:
        grouped.setdefault(recommendation["space_id"], []).append(
            recommendation
        )
    if space_id is not None:
        grouped.setdefault(space_id, [])

    spaces = []
    for current_space_id, space_recommendations in sorted(grouped.items()):
        total = len(space_recommendations)
        accepted = sum(
            recommendation["action"] == "accepted"
            for recommendation in space_recommendations
        )
        ignored = sum(
            recommendation["action"] == "ignored"
            for recommendation in space_recommendations
        )
        decided = accepted + ignored
        comparable_reductions = []
        for recommendation in space_recommendations:
            requested_score = recommendation["requested_score"]
            recommended_score = recommendation["recommended_score"]
            requested_start = recommendation["requested_start"]
            recommended_start = recommendation["recommended_start"]
            if (
                recommendation["action"] == "accepted"
                and requested_start
                and recommended_start
                and requested_start != recommended_start
                and requested_score is not None
                and recommended_score is not None
                and 0 <= requested_score <= 100
                and 0 <= recommended_score <= 100
                and requested_score > recommended_score
            ):
                comparable_reductions.append(
                    (requested_score, recommended_score)
                )
        spaces.append(
            {
                "space_id": current_space_id,
                "recommendations_generated": total,
                "accepted": accepted,
                "ignored": ignored,
                "without_action": total - decided,
                "decision_rate": (
                    round(decided / total * 100, 1)
                    if total
                    else None
                ),
                "acceptance_rate": (
                    round(accepted / decided * 100, 1)
                    if decided
                    else None
                ),
                "accepted_high_to_lower_recommendations": sum(
                    requested_score >= 65
                    for requested_score, _ in comparable_reductions
                ),
                "accepted_recommendations_with_score_reduction": len(
                    comparable_reductions
                ),
                "average_saturation_reduction": (
                    round(
                        sum(
                            requested_score - recommended_score
                            for requested_score, recommended_score
                            in comparable_reductions
                        )
                        / len(comparable_reductions),
                        1,
                    )
                    if comparable_reductions
                    else None
                ),
            }
        )
    return spaces
