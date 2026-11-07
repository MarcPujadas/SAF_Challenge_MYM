from datetime import date, datetime


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
        parsed_date = date.fromisoformat(date_value)
    except ValueError as exc:
        raise ValueError("date must use YYYY-MM-DD.") from exc
    if parsed_date.isoformat() != date_value:
        raise ValueError("date must use YYYY-MM-DD.")
    try:
        parsed_time = datetime.strptime(time_value, "%H:%M")
    except ValueError as exc:
        raise ValueError("Time values must use HH:MM.") from exc
    if parsed_time.strftime("%H:%M") != time_value:
        raise ValueError("Time values must use HH:MM.")
    return parsed_date, parsed_time.hour * 60 + parsed_time.minute
