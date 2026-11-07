from datetime import date, datetime

from app.common import ApiError
from app.services.schedule_service import (
    parse_date,
    time_to_minutes,
)


WEEKDAYS_CA = [
    "dilluns",
    "dimarts",
    "dimecres",
    "dijous",
    "divendres",
    "dissabte",
    "diumenge",
]


def validate_date_time(date_value: str, time_value: str) -> tuple[date, int]:
    try:
        parsed_date = parse_date(date_value)
    except ApiError as exc:
        raise ValueError("date must use YYYY-MM-DD.") from exc
    try:
        minutes = time_to_minutes(time_value)
    except ApiError as exc:
        raise ValueError("Time values must use HH:MM.") from exc
    return parsed_date, minutes
