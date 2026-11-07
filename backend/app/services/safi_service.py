import re
from datetime import date, timedelta
from typing import Any

from app.services.historical_service import (
    add_occupancy_scores,
    calculate_slot_statistics,
    get_historical_occupancy,
    prepare_space_data,
)
from app.services.recommendation_service import recommend
from app.services.validation import WEEKDAYS_CA, validate_date_time

UNKNOWN_MESSAGE = "No ho sé amb les dades disponibles."
SPACE_ALIASES = {"fitness": "sala-fitnes-sala-cardio"}
LEVEL_CA = {
    "low": "baixa",
    "medium": "mitjana",
    "high": "alta",
    "very_high": "molt alta",
}


def quietest_slot(space_id: str, weekday: int) -> tuple[str, int] | None:
    statistics = add_occupancy_scores(
        calculate_slot_statistics(
            prepare_space_data(space_id, weekday)
        )
    )
    if statistics.empty:
        return None

    row = statistics.sort_values(
        ["occupancy_score", "start_time"]
    ).iloc[0]
    return row["start_time"], int(row["occupancy_score"])


def has_better_alternative(
    requested: dict[str, Any],
    alternative: dict[str, Any] | None,
) -> bool:
    return (
        alternative is not None
        and alternative["occupancy_score"] is not None
        and alternative["occupancy_level"] in LEVEL_CA
        and alternative["occupancy_score"] < requested["occupancy_score"]
    )


def occupancy_message(
    space_id: str,
    weekday: int,
    requested: dict[str, Any],
    alternative: dict[str, Any] | None,
) -> str:
    requested_score = requested["occupancy_score"]
    requested_level = requested["occupancy_level"]
    if requested_score is None or requested_level == "unknown":
        return UNKNOWN_MESSAGE

    start = requested["start"]
    weekday_name = WEEKDAYS_CA[weekday]
    samples = get_historical_occupancy(
        space_id,
        weekday,
        start,
    )["samples"]
    message = (
        f"A les {start} de {weekday_name} l'ocupació acostuma a ser "
        f"{LEVEL_CA[requested_level]}."
    )
    if has_better_alternative(requested, alternative):
        assert alternative is not None
        message += (
            f" Les {alternative['start']} solen estar més tranquil·les "
            f"(ocupació {LEVEL_CA[alternative['occupancy_level']]})."
        )
    else:
        message += " No hi ha cap franja propera més tranquil·la."
    message += f" Basat en {samples} dies amb dades (abril-octubre 2026)."
    return message


def advice(space_id: str, date_value: str, start: str) -> dict[str, Any]:
    parsed_date, start_minutes = validate_date_time(date_value, start)
    end_minutes = min(start_minutes + 120, 23 * 60 + 59)
    end = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
    _, end_minutes = validate_date_time(parsed_date.isoformat(), end)
    if end_minutes <= start_minutes:
        raise ValueError("preferred_end must be later than preferred_start.")

    actual_space_id = SPACE_ALIASES.get(space_id, space_id)
    result = recommend(actual_space_id, parsed_date.isoformat(), start, end)
    requested = result["requested_slot"]
    score = requested["occupancy_score"]
    if score is None or requested["occupancy_level"] == "unknown":
        return {
            "type": "info",
            "message": UNKNOWN_MESSAGE,
            "alternative": None,
            "occupancy_score": None,
        }

    alternative = result["recommended_slot"]
    message = occupancy_message(
        actual_space_id,
        parsed_date.weekday(),
        requested,
        alternative,
    )
    if message == UNKNOWN_MESSAGE:
        return {
            "type": "info",
            "message": UNKNOWN_MESSAGE,
            "alternative": None,
            "occupancy_score": None,
        }

    if requested["occupancy_level"] in ("high", "very_high"):
        advice_type = "warning"
    else:
        advice_type = (
            "recommendation"
            if has_better_alternative(requested, alternative)
            else "info"
        )

    alternative_data = None
    if has_better_alternative(requested, alternative):
        assert alternative is not None
        alternative_data = {
            "start": alternative["start"],
            "message": f"Les {alternative['start']} acostumen a tenir menys ocupació.",
        }
    return {
        "type": advice_type,
        "message": message,
        "alternative": alternative_data,
        "occupancy_score": score,
    }


def chat(message: str) -> dict[str, Any]:
    normalized = message.casefold()
    if "fitness" not in normalized or not any(
        word in normalized
        for word in ("ocup", "gent", "menys", "recoman", "hour", "when", "quan")
    ):
        return {
            "message": UNKNOWN_MESSAGE,
            "sources": [],
            "can_answer": False,
        }

    space_id = SPACE_ALIASES["fitness"]
    date_reference = date.today()
    if "demà" in normalized or "dema" in normalized or "tomorrow" in normalized:
        date_reference += timedelta(days=1)
    elif "avui" not in normalized and "today" not in normalized:
        explicit_date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message)
        if explicit_date is not None:
            try:
                date_reference = date.fromisoformat(explicit_date.group())
            except ValueError:
                return {
                    "message": UNKNOWN_MESSAGE,
                    "sources": [],
                    "can_answer": False,
                }

    requested_time = re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", message)
    if requested_time is not None:
        start = requested_time.group().zfill(5)
        try:
            _, start_minutes = validate_date_time(
                date_reference.isoformat(),
                start,
            )
        except ValueError:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        end_minutes = min(start_minutes + 120, 23 * 60 + 59)
        end = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        if end_minutes <= start_minutes:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        recommendation = recommend(
            space_id,
            date_reference.isoformat(),
            start,
            end,
        )
        if (
            recommendation["requested_slot"]["occupancy_score"] is None
            or recommendation["requested_slot"]["occupancy_level"] == "unknown"
        ):
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        response_message = occupancy_message(
            space_id,
            date_reference.weekday(),
            recommendation["requested_slot"],
            recommendation["recommended_slot"],
        )
        if response_message == UNKNOWN_MESSAGE:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
    else:
        quietest = quietest_slot(space_id, date_reference.weekday())
        if quietest is None:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        quietest_start, _ = quietest
        response_message = (
            f"Les {quietest_start} acostumen a ser una de les franges "
            "amb menys ocupació."
        )

    return {
        "message": response_message,
        "sources": [
            {
                "type": "historical_occupancy",
                "space_id": space_id,
                "date_reference": WEEKDAYS_CA[date_reference.weekday()],
            }
        ],
        "can_answer": True,
    }
