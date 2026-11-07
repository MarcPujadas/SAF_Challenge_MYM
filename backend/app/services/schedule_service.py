from __future__ import annotations

from datetime import date, datetime

from app.common import ApiError
from app.config.services import SPACE_ID_BY_SERVICE_ID
from app.config.schedules import (
    GENERAL_OPENING_HOURS,
    GENERAL_SLOT_DURATION_MINUTES,
    STANDARD_75_MINUTE_SPACE_PREFIXES,
    STANDARD_75_MINUTE_SLOTS,
    STANDARD_SLOT_DURATION_MINUTES,
)


def parse_date(value: str, field: str = "date") -> date:
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise ApiError(
            "INVALID_DATE",
            f"{field} must use YYYY-MM-DD format.",
        ) from exc
    if parsed_date.isoformat() != value:
        raise ApiError(
            "INVALID_DATE",
            f"{field} must use YYYY-MM-DD format.",
        )
    return parsed_date


def parse_optional_date(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    return parse_date(value, field).isoformat()


def parse_date_range(
    date_from: str | None,
    date_to: str | None,
) -> tuple[str | None, str | None]:
    start = parse_optional_date(date_from, "from")
    end = parse_optional_date(date_to, "to")
    if start is not None and end is not None and start > end:
        raise ApiError(
            "INVALID_DATE_RANGE",
            "'from' must be on or before 'to'.",
        )
    return start, end


def time_to_minutes(value: str) -> int:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ApiError(
            "INVALID_TIME",
            "Time must use HH:MM 24-hour format.",
        ) from exc
    if parsed.strftime("%H:%M") != value:
        raise ApiError(
            "INVALID_TIME",
            "Time must use HH:MM 24-hour format.",
        )
    return parsed.hour * 60 + parsed.minute


def minutes_to_time(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def overlaps(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:
    return start_a < end_b and start_b < end_a


def uses_standard_slots(space_id: str) -> bool:
    return (
        space_id == SPACE_ID_BY_SERVICE_ID["fitness"]
        or space_id.startswith(STANDARD_75_MINUTE_SPACE_PREFIXES)
    )


def build_slots(
    space_id: str,
    space_type: str,
    weekday: int,
) -> list[tuple[int, int]]:
    del space_type
    if uses_standard_slots(space_id):
        return [
            (
                time_to_minutes(start),
                time_to_minutes(start) + STANDARD_SLOT_DURATION_MINUTES,
            )
            for start in STANDARD_75_MINUTE_SLOTS.get(weekday, [])
        ]

    opening_hours = GENERAL_OPENING_HOURS.get(weekday)
    if opening_hours is None:
        return []

    opening_time = time_to_minutes(opening_hours[0])
    closing_time = time_to_minutes(opening_hours[1])
    slots = []
    start = opening_time
    while start + GENERAL_SLOT_DURATION_MINUTES <= closing_time:
        slots.append((start, start + GENERAL_SLOT_DURATION_MINUTES))
        start += GENERAL_SLOT_DURATION_MINUTES
    return slots


def validate_reservation_slot(
    space_id: str,
    space_type: str,
    reservation_date: date,
    start: str,
    end: str,
) -> None:
    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)
    if end_minutes <= start_minutes:
        raise ApiError(
            "INVALID_TIME",
            "Reservation end must be after start.",
        )

    if (start_minutes, end_minutes) not in build_slots(
        space_id,
        space_type,
        reservation_date.weekday(),
    ):
        raise ApiError(
            "INVALID_TIME",
            "The requested time does not match a valid reservation slot.",
        )
