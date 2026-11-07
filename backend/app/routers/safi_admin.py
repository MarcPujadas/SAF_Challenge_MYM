from contextlib import closing
from datetime import date
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.common import ApiError, success
from app.database.database import get_connection
from app.services.recommendation_service import recommend
from app.services.safi_service import advice, chat
from app.services.validation import validate_date_time


router = APIRouter(prefix="/api/v1")


class RecommendationRequest(BaseModel):
    space_id: str
    date: str
    preferred_start: str
    preferred_end: str


class SAFiAdviceRequest(BaseModel):
    space_id: str
    date: str
    start: str


class SAFiChatRequest(BaseModel):
    user_id: str
    message: str


def get_reservations() -> list[Any]:
    with closing(get_connection()) as connection:
        return connection.execute(
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


def parse_date(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise ApiError("INVALID_DATE", f"{field} must use YYYY-MM-DD.", 400) from exc
    if parsed_date.isoformat() != value:
        raise ApiError("INVALID_DATE", f"{field} must use YYYY-MM-DD.", 400)
    return parsed_date.isoformat()


@router.post("/recommendations")
def create_recommendation(payload: RecommendationRequest) -> dict[str, Any]:
    try:
        parsed_date, start_minutes = validate_date_time(
            payload.date,
            payload.preferred_start,
        )
        _, end_minutes = validate_date_time(
            payload.date,
            payload.preferred_end,
        )
        if end_minutes <= start_minutes:
            raise ValueError("preferred_end must be later than preferred_start.")
        result = recommend(
            payload.space_id,
            parsed_date.isoformat(),
            payload.preferred_start,
            payload.preferred_end,
        )
    except ValueError as exc:
        raise ApiError("INVALID_TIME", str(exc), 400) from exc
    if result["requested_slot"]["occupancy_score"] is None:
        raise ApiError(
            "OCCUPANCY_DATA_UNAVAILABLE",
            "No hi ha dades d'ocupació disponibles per a aquesta consulta.",
            404,
        )
    return success(result)


@router.post("/safi/advice")
def get_safi_advice(payload: SAFiAdviceRequest) -> dict[str, Any]:
    try:
        result = advice(payload.space_id, payload.date, payload.start)
    except ValueError as exc:
        raise ApiError("INVALID_TIME", str(exc), 400) from exc
    return success(result)


@router.post("/safi/chat")
def chat_with_safi(payload: SAFiChatRequest) -> dict[str, Any]:
    return success(chat(payload.message))


@router.get("/admin/summary")
def get_admin_summary() -> dict[str, Any]:
    reservations = get_reservations()
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
        key=lambda space_id: (-space_counts[space_id], space_id),
        default=None,
    )
    busiest_hour = min(
        hour_counts,
        key=lambda hour: (-hour_counts[hour], hour),
        default=None,
    )
    today = date.today().isoformat()
    today_count = sum(reservation["date"] == today for reservation in reservations)

    return success(
        {
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
    )


@router.get("/admin/stats")
def get_admin_stats() -> dict[str, Any]:
    reservations = get_reservations()
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
    return success(
        {
            "total_reservations": len(reservations),
            "reservations_created_by_app": len(reservations),
            "most_used_spaces": most_used_spaces,
            "busiest_hour": None,
            "quietest_hour": None,
        }
    )


@router.get("/admin/reservations")
def get_admin_reservations() -> dict[str, Any]:
    return success(
        [
            {
                "reservation_id": reservation["reservation_id"],
                "space_id": reservation["space_id"],
                "date": reservation["date"],
                "start": reservation["start"],
                "status": reservation["status"],
            }
            for reservation in get_reservations()
        ]
    )


@router.get("/admin/occupancy")
def get_admin_occupancy(
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    space_id: str | None = None,
) -> dict[str, Any]:
    start = parse_date(date_from, "from")
    end = parse_date(date_to, "to")
    if start is not None and end is not None and start > end:
        raise ApiError("INVALID_DATE_RANGE", "'from' must be on or before 'to'.", 400)

    return success(
        {
            "period": {"from": start, "to": end},
            "spaces": [],
        }
    )