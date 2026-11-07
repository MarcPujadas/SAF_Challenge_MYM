from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date as date_type
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.database.database import get_connection, init_db


class ReservationCreate(BaseModel):
    user_id: str
    space_id: str
    date: str
    start: str
    end: str


class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def success(data):
    return {"success": True, "data": data, "error": None}


def error_payload(code: str, message: str):
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message},
    }


def parse_date(value: str) -> date_type:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ApiError("INVALID_DATE", "Date must use YYYY-MM-DD format.") from exc


def time_to_minutes(value: str) -> int:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ApiError("INVALID_TIME", "Time must use HH:MM 24-hour format.") from exc
    return parsed.hour * 60 + parsed.minute


def minutes_to_time(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def occupancy_level(score: int) -> str:
    if score < 35:
        return "low"
    if score < 65:
        return "medium"
    if score < 85:
        return "high"
    return "very_high"


def get_space(space_id: str):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, type, capacity, reservable FROM spaces WHERE id = ?",
            (space_id,),
        ).fetchone()

    if row is None:
        raise ApiError("INVALID_SPACE", "The requested space does not exist.", 404)
    return row


def build_slots(space_type: str) -> list[tuple[int, int]]:
    if space_type == "fitness":
        duration = 75
        starts = range(8 * 60, 21 * 60 + 1, duration)
    else:
        duration = 60
        starts = range(8 * 60, 21 * 60 + 1, duration)

    return [(start, start + duration) for start in starts]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SAF Hack API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, __: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_payload("INVALID_REQUEST", "Invalid request payload."),
    )


@app.get("/health")
def health():
    return success({"status": "ok"})


@app.get("/api/v1/users/me")
def current_user():
    return success({"id": "demo-user", "name": "Usuari Demo"})


@app.get("/api/v1/spaces")
def list_spaces():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, type, capacity, reservable
            FROM spaces
            ORDER BY name
            """
        ).fetchall()

    return success(
        [
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "capacity": row["capacity"],
                "reservable": bool(row["reservable"]),
            }
            for row in rows
        ]
    )


@app.get("/api/v1/services")
def list_services():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, description, space_id, reservable
            FROM services
            ORDER BY name
            """
        ).fetchall()

    return success(
        [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "space_id": row["space_id"],
                "reservable": bool(row["reservable"]),
            }
            for row in rows
        ]
    )


@app.get("/api/v1/availability")
def availability(
    space_id: str = Query(...),
    date: str = Query(...),
):
    parse_date(date)
    space = get_space(space_id)

    if not bool(space["reservable"]):
        raise ApiError("INVALID_SPACE", "This space is not reservable.")

    slots = []
    with get_connection() as connection:
        reservations = connection.execute(
            """
            SELECT start, end
            FROM reservations
            WHERE space_id = ? AND date = ? AND status = 'confirmed'
            """,
            (space_id, date),
        ).fetchall()

    intervals = [
        (time_to_minutes(row["start"]), time_to_minutes(row["end"]))
        for row in reservations
    ]

    for start, end in build_slots(space["type"]):
        reservations_in_slot = sum(
            overlaps(start, end, reserved_start, reserved_end)
            for reserved_start, reserved_end in intervals
        )
        remaining = max(space["capacity"] - reservations_in_slot, 0)
        score = min(round((reservations_in_slot / space["capacity"]) * 100), 100)

        slots.append(
            {
                "start": minutes_to_time(start),
                "end": minutes_to_time(end),
                "available": remaining > 0,
                "remaining_capacity": remaining,
                "occupancy_level": occupancy_level(score),
                "occupancy_score": score,
            }
        )

    return success({"space_id": space_id, "date": date, "slots": slots})


@app.post("/api/v1/reservations")
def create_reservation(payload: ReservationCreate):
    parse_date(payload.date)
    start = time_to_minutes(payload.start)
    end = time_to_minutes(payload.end)

    if end <= start:
        raise ApiError("INVALID_TIME", "Reservation end must be after start.")

    space = get_space(payload.space_id)
    if not bool(space["reservable"]):
        raise ApiError("INVALID_SPACE", "This space is not reservable.")

    with get_connection() as connection:
        user = connection.execute(
            "SELECT id FROM users WHERE id = ?",
            (payload.user_id,),
        ).fetchone()
        if user is None:
            raise ApiError("INVALID_USER", "The requested user does not exist.", 404)

        existing_user_reservations = connection.execute(
            """
            SELECT start, end
            FROM reservations
            WHERE user_id = ? AND date = ? AND status = 'confirmed'
            """,
            (payload.user_id, payload.date),
        ).fetchall()

        for reservation in existing_user_reservations:
            if overlaps(
                start,
                end,
                time_to_minutes(reservation["start"]),
                time_to_minutes(reservation["end"]),
            ):
                raise ApiError(
                    "RESERVATION_CONFLICT",
                    "The user already has a reservation during this time.",
                    409,
                )

        existing_space_reservations = connection.execute(
            """
            SELECT start, end
            FROM reservations
            WHERE space_id = ? AND date = ? AND status = 'confirmed'
            """,
            (payload.space_id, payload.date),
        ).fetchall()

        concurrent = sum(
            overlaps(
                start,
                end,
                time_to_minutes(reservation["start"]),
                time_to_minutes(reservation["end"]),
            )
            for reservation in existing_space_reservations
        )

        if concurrent >= space["capacity"]:
            raise ApiError(
                "SLOT_NOT_AVAILABLE",
                "The requested time slot has no remaining capacity.",
                409,
            )

        reservation_id = f"res_{uuid4().hex[:12]}"
        connection.execute(
            """
            INSERT INTO reservations
                (id, user_id, space_id, date, start, end, status)
            VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
            """,
            (
                reservation_id,
                payload.user_id,
                payload.space_id,
                payload.date,
                payload.start,
                payload.end,
            ),
        )

    return success(
        {
            "reservation_id": reservation_id,
            "status": "confirmed",
            "user_id": payload.user_id,
            "space_id": payload.space_id,
            "date": payload.date,
            "start": payload.start,
            "end": payload.end,
        }
    )


@app.get("/api/v1/reservations")
def list_reservations(user_id: str = Query(...)):
    with get_connection() as connection:
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
            WHERE r.user_id = ?
            ORDER BY r.date, r.start
            """,
            (user_id,),
        ).fetchall()

    return success([dict(row) for row in rows])
