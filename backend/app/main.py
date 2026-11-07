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
from app.services.historical_service import (
    FITNESS_VALID_SLOTS,
    get_historical_occupancy,
)


class ReservationCreate(BaseModel):
    user_id: str
    space_id: str
    date: str
    start: str
    end: str


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400
    ):
        super().__init__(message)

        self.code = code
        self.message = message
        self.status_code = status_code


def success(data):
    return {
        "success": True,
        "data": data,
        "error": None
    }


def error_payload(code: str, message: str):
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message
        }
    }


def parse_date(value: str) -> date_type:
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except ValueError as exc:
        raise ApiError(
            "INVALID_DATE",
            "Date must use YYYY-MM-DD format."
        ) from exc


def time_to_minutes(value: str) -> int:
    try:
        parsed = datetime.strptime(
            value,
            "%H:%M"
        )

    except ValueError as exc:
        raise ApiError(
            "INVALID_TIME",
            "Time must use HH:MM 24-hour format."
        ) from exc

    return parsed.hour * 60 + parsed.minute


def minutes_to_time(value: int) -> str:
    return (
        f"{value // 60:02d}:"
        f"{value % 60:02d}"
    )


def overlaps(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int
) -> bool:
    return (
        start_a < end_b
        and start_b < end_a
    )


def get_space(space_id: str):
    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                id,
                name,
                type,
                capacity,
                reservable
            FROM spaces
            WHERE id = ?
            """,
            (space_id,)
        ).fetchone()

    if row is None:
        raise ApiError(
            "INVALID_SPACE",
            "The requested space does not exist.",
            404
        )

    return row


def build_slots(
    space_type: str,
    weekday: int
) -> list[tuple[int, int]]:

    if space_type == "fitness":

        valid_slots = FITNESS_VALID_SLOTS.get(
            weekday,
            []
        )

        return [
            (
                time_to_minutes(start),
                time_to_minutes(start) + 75
            )
            for start in valid_slots
        ]

    duration = 60

    starts = range(
        8 * 60,
        21 * 60 + 1,
        duration
    )

    return [
        (start, start + duration)
        for start in starts
    ]


def validate_reservation_slot(
    space_type: str,
    reservation_date: date_type,
    start: str,
    end: str
):
    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)

    if end_minutes <= start_minutes:
        raise ApiError(
            "INVALID_TIME",
            "Reservation end must be after start."
        )

    weekday = reservation_date.weekday()

    valid_slots = build_slots(
        space_type,
        weekday
    )

    requested_slot = (
        start_minutes,
        end_minutes
    )

    if requested_slot not in valid_slots:
        raise ApiError(
            "INVALID_TIME",
            "The requested time does not match a valid reservation slot."
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()

    yield


app = FastAPI(
    title="SAF Hack API",
    version="0.1.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.exception_handler(ApiError)
async def api_error_handler(
    _: Request,
    exc: ApiError
):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            exc.code,
            exc.message
        )
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request,
    __: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content=error_payload(
            "INVALID_REQUEST",
            "Invalid request payload."
        )
    )


@app.get("/")
def root():
    return success(
        {
            "name": "SAF Hack API",
            "status": "running"
        }
    )


@app.get("/health")
def health():
    return success(
        {
            "status": "ok"
        }
    )


@app.get("/api/v1/users/me")
def current_user():
    return success(
        {
            "id": "demo-user",
            "name": "Usuari Demo"
        }
    )


@app.get("/api/v1/spaces")
def list_spaces():

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                id,
                name,
                type,
                capacity,
                reservable
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
                "reservable": bool(
                    row["reservable"]
                )
            }
            for row in rows
        ]
    )


@app.get("/api/v1/services")
def list_services():

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                id,
                name,
                description,
                space_id,
                reservable
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
                "reservable": bool(
                    row["reservable"]
                )
            }
            for row in rows
        ]
    )


@app.get("/api/v1/availability")
def availability(
    space_id: str = Query(...),
    date: str = Query(...)
):
    requested_date = parse_date(date)

    weekday = requested_date.weekday()

    space = get_space(space_id)

    if not bool(space["reservable"]):
        raise ApiError(
            "INVALID_SPACE",
            "This space is not reservable."
        )

    with get_connection() as connection:

        reservations = connection.execute(
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
                date
            )
        ).fetchall()

    reservation_intervals = [
        (
            time_to_minutes(
                row["start"]
            ),
            time_to_minutes(
                row["end"]
            )
        )
        for row in reservations
    ]

    slots = []

    for start, end in build_slots(
        space["type"],
        weekday
    ):
        start_string = minutes_to_time(start)
        end_string = minutes_to_time(end)

        reservations_in_slot = sum(
            overlaps(
                start,
                end,
                reserved_start,
                reserved_end
            )
            for (
                reserved_start,
                reserved_end
            ) in reservation_intervals
        )

        remaining_capacity = max(
            space["capacity"]
            - reservations_in_slot,
            0
        )

        historical = (
            get_historical_occupancy(
                space_id=space_id,
                weekday=weekday,
                start_time=start_string
            )
        )

        slots.append(
            {
                "start": start_string,
                "end": end_string,
                "available": (
                    remaining_capacity > 0
                ),
                "remaining_capacity": (
                    remaining_capacity
                ),
                "occupancy_level": (
                    historical[
                        "occupancy_level"
                    ]
                ),
                "occupancy_score": (
                    historical[
                        "occupancy_score"
                    ]
                )
            }
        )

    return success(
        {
            "space_id": space_id,
            "date": date,
            "slots": slots
        }
    )


@app.post("/api/v1/reservations")
def create_reservation(
    payload: ReservationCreate
):
    reservation_date = parse_date(
        payload.date
    )

    space = get_space(
        payload.space_id
    )

    if not bool(space["reservable"]):
        raise ApiError(
            "INVALID_SPACE",
            "This space is not reservable."
        )

    validate_reservation_slot(
        space_type=space["type"],
        reservation_date=reservation_date,
        start=payload.start,
        end=payload.end
    )

    start = time_to_minutes(
        payload.start
    )

    end = time_to_minutes(
        payload.end
    )

    with get_connection() as connection:

        user = connection.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            """,
            (
                payload.user_id,
            )
        ).fetchone()

        if user is None:
            raise ApiError(
                "INVALID_USER",
                "The requested user does not exist.",
                404
            )

        existing_user_reservations = (
            connection.execute(
                """
                SELECT
                    start,
                    end
                FROM reservations
                WHERE
                    user_id = ?
                    AND date = ?
                    AND status = 'confirmed'
                """,
                (
                    payload.user_id,
                    payload.date
                )
            ).fetchall()
        )

        for reservation in (
            existing_user_reservations
        ):
            if overlaps(
                start,
                end,
                time_to_minutes(
                    reservation["start"]
                ),
                time_to_minutes(
                    reservation["end"]
                )
            ):
                raise ApiError(
                    "RESERVATION_CONFLICT",
                    (
                        "The user already has "
                        "a reservation during "
                        "this time."
                    ),
                    409
                )

        existing_space_reservations = (
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
                    payload.space_id,
                    payload.date
                )
            ).fetchall()
        )

        concurrent = sum(
            overlaps(
                start,
                end,
                time_to_minutes(
                    reservation["start"]
                ),
                time_to_minutes(
                    reservation["end"]
                )
            )
            for reservation
            in existing_space_reservations
        )

        if concurrent >= space["capacity"]:
            raise ApiError(
                "SLOT_NOT_AVAILABLE",
                (
                    "The requested time slot "
                    "has no remaining capacity."
                ),
                409
            )

        reservation_id = (
            f"res_{uuid4().hex[:12]}"
        )

        connection.execute(
            """
            INSERT INTO reservations (
                id,
                user_id,
                space_id,
                date,
                start,
                end,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
            """,
            (
                reservation_id,
                payload.user_id,
                payload.space_id,
                payload.date,
                payload.start,
                payload.end
            )
        )

    return success(
        {
            "reservation_id": reservation_id,
            "status": "confirmed",
            "user_id": payload.user_id,
            "space_id": payload.space_id,
            "date": payload.date,
            "start": payload.start,
            "end": payload.end
        }
    )


@app.get("/api/v1/reservations")
def list_reservations(
    user_id: str = Query(...)
):
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
            JOIN spaces s
                ON s.id = r.space_id
            WHERE r.user_id = ?
            ORDER BY
                r.date,
                r.start
            """,
            (
                user_id,
            )
        ).fetchall()

    return success(
        [
            dict(row)
            for row in rows
        ]
    )