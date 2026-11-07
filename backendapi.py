import os
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from recommendation_service import recommend
from safi_service import advice, chat


DATABASE_PATH = Path(
    os.environ.get(
        "SAFHACK_DB_PATH",
        str(
            Path(__file__).resolve().parent
            / "backend"
            / "app"
            / "database"
            / "safhack.db"
        ),
    )
)
API_PREFIX = "/api/v1"
SPACE_NAMES = {
    "fitness": "Sala Fitness",
    "pool": "Piscina",
    "piscina": "Piscina",
}

app = FastAPI(title="SAF Hack API")


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


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


def success(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data, "error": None}


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                user_id TEXT,
                space_id TEXT NOT NULL,
                date TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed'
            )
            """
        )
        connection.commit()


def get_reservations(
    date_from: str | None = None,
    date_to: str | None = None,
    space_id: str | None = None,
) -> list[sqlite3.Row]:
    conditions = ["status != 'cancelled'"]
    parameters: list[str] = []
    if date_from is not None:
        conditions.append("date >= ?")
        parameters.append(date_from)
    if date_to is not None:
        conditions.append("date <= ?")
        parameters.append(date_to)
    if space_id is not None:
        conditions.append("space_id = ?")
        parameters.append(space_id)

    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            f"""
            SELECT reservation_id, space_id, date, start, end, status
            FROM reservations
            WHERE {" AND ".join(conditions)}
            ORDER BY date, start, reservation_id
            """,
            parameters,
        ).fetchall()


def parse_date(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise APIError(400, "INVALID_DATE", f"{field} must use YYYY-MM-DD.") from exc
    if parsed_date.isoformat() != value:
        raise APIError(400, "INVALID_DATE", f"{field} must use YYYY-MM-DD.")
    return parsed_date.isoformat()


@app.exception_handler(APIError)
async def handle_api_error(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": exc.code, "message": exc.message},
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "The request does not match the required format.",
            },
        },
    )


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.post(f"{API_PREFIX}/recommendations")
def create_recommendation(payload: RecommendationRequest) -> dict[str, Any]:
    try:
        result = recommend(
            payload.space_id,
            payload.date,
            payload.preferred_start,
            payload.preferred_end,
        )
    except ValueError as exc:
        raise APIError(400, "INVALID_TIME", str(exc)) from exc
    if result is None:
        raise APIError(
            404,
            "OCCUPANCY_DATA_UNAVAILABLE",
            "No hi ha dades d'ocupació disponibles per a aquesta consulta.",
        )
    return success(result)


@app.post(f"{API_PREFIX}/safi/advice")
def get_safi_advice(payload: SAFiAdviceRequest) -> dict[str, Any]:
    try:
        result = advice(payload.space_id, payload.date, payload.start)
    except ValueError as exc:
        raise APIError(400, "INVALID_TIME", str(exc)) from exc
    return success(result)


@app.post(f"{API_PREFIX}/safi/chat")
def chat_with_safi(payload: SAFiChatRequest) -> dict[str, Any]:
    return success(chat(payload.message))


@app.get(f"{API_PREFIX}/admin/summary")
def get_admin_summary() -> dict[str, Any]:
    reservations = get_reservations()
    space_counts: dict[str, int] = {}
    hour_counts: dict[str, int] = {}
    for reservation in reservations:
        space_id = reservation["space_id"]
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
                    "name": SPACE_NAMES.get(busiest_space_id, busiest_space_id),
                }
                if busiest_space_id is not None
                else None
            ),
            "busiest_hour": busiest_hour,
        }
    )


@app.get(f"{API_PREFIX}/admin/stats")
def get_admin_stats() -> dict[str, Any]:
    reservations = get_reservations()
    space_counts: dict[str, int] = {}
    for reservation in reservations:
        space_id = reservation["space_id"]
        space_counts[space_id] = space_counts.get(space_id, 0) + 1

    most_used_spaces = [
        {
            "space_id": space_id,
            "name": SPACE_NAMES.get(space_id, space_id),
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


@app.get(f"{API_PREFIX}/admin/reservations")
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


@app.get(f"{API_PREFIX}/admin/occupancy")
def get_admin_occupancy(
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    space_id: str | None = None,
) -> dict[str, Any]:
    start = parse_date(date_from, "from")
    end = parse_date(date_to, "to")
    if start is not None and end is not None and start > end:
        raise APIError(400, "INVALID_DATE_RANGE", "'from' must be on or before 'to'.")

    return success(
        {
            "period": {"from": start, "to": end},
            "spaces": [],
        }
    )