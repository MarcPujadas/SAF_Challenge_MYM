import re
import unicodedata
from datetime import date, timedelta
from typing import Any

from app.config.services import (
    SERVICE_SEARCH_PHRASES,
    SPACE_ID_BY_ALIAS,
    supports_safi_recommendations,
)
from app.services.historical_service import (
    get_historical_occupancy,
)
from app.services.recommendation_service import (
    get_best_day_alternative,
    get_quietest_slot,
    recommend,
)
from app.services.validation import WEEKDAYS_CA, validate_date_time

UNKNOWN_MESSAGE = "No ho sé amb les dades disponibles."
SPACE_ALIASES = {
    **SPACE_ID_BY_ALIAS,
}
SERVICE_PHRASES = SERVICE_SEARCH_PHRASES
LEVEL_CA = {
    "low": "baixa",
    "medium": "mitjana",
    "high": "alta",
    "very_high": "molt alta",
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def detect_space_id(message: str) -> str | None:
    normalized = normalize_text(message)
    for phrase, service_id in SERVICE_PHRASES:
        if phrase in normalized:
            return SPACE_ID_BY_ALIAS[service_id]
    return None


def parse_date_reference(message: str) -> tuple[date, bool] | None:
    normalized = normalize_text(message)
    explicit_date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", normalized)
    if explicit_date is not None:
        try:
            parsed_date = date.fromisoformat(explicit_date.group())
        except ValueError:
            return None
        if parsed_date.isoformat() != explicit_date.group():
            return None
        return parsed_date, True

    today = date.today()
    if any(word in normalized for word in ("demà", "dema", "tomorrow", "manana")):
        return today + timedelta(days=1), True
    if any(word in normalized for word in ("avui", "today", "hoy")):
        return today, True

    weekday_aliases = {
        "dilluns": 0,
        "lunes": 0,
        "monday": 0,
        "dimarts": 1,
        "martes": 1,
        "tuesday": 1,
        "dimecres": 2,
        "miercoles": 2,
        "wednesday": 2,
        "dijous": 3,
        "jueves": 3,
        "thursday": 3,
        "divendres": 4,
        "viernes": 4,
        "friday": 4,
        "dissabte": 5,
        "sabado": 5,
        "saturday": 5,
        "diumenge": 6,
        "domingo": 6,
        "sunday": 6,
    }
    for day_name, weekday in weekday_aliases.items():
        if re.search(rf"\b{day_name}\b", normalized):
            return today + timedelta(days=(weekday - today.weekday()) % 7), True
    return today, False


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
    if not supports_safi_recommendations(actual_space_id):
        return {
            "type": "info",
            "message": "SAFi no ofereix recomanacions d'ocupació per aquest tipus d'espai.",
            "alternative": None,
            "occupancy_score": None,
        }
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
    normalized = normalize_text(message)
    space_id = detect_space_id(message)
    if space_id is not None and not supports_safi_recommendations(space_id):
        return {
            "message": "SAFi no ofereix recomanacions d'ocupació per aquest tipus d'espai.",
            "sources": [],
            "can_answer": False,
        }
    if space_id is None or not any(
        word in normalized
        for word in (
            "ocup",
            "gent",
            "gente",
            "people",
            "menys",
            "menos",
            "tranquil",
            "quiet",
            "recoman",
            "recommend",
            "hour",
            "hora",
            "when",
            "quan",
            "cuando",
            "busy",
        )
    ):
        return {
            "message": UNKNOWN_MESSAGE,
            "sources": [],
            "can_answer": False,
        }

    parsed_reference = parse_date_reference(message)
    if parsed_reference is None:
        return {
            "message": UNKNOWN_MESSAGE,
            "sources": [],
            "can_answer": False,
        }
    date_reference, has_explicit_day = parsed_reference

    requested_time = re.search(
        r"\b\d{1,2}:\d{2}\b",
        normalized,
    )
    source_weekday = date_reference.weekday()
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
        asks_for_other_day = any(
            phrase in normalized
            for phrase in (
                "altre dia",
                "altre jorn",
                "otro dia",
                "another day",
                "other day",
            )
        )
        if asks_for_other_day:
            day_alternative = get_best_day_alternative(
                space_id,
                date_reference.isoformat(),
                recommendation["requested_slot"]["start"],
            )
            if day_alternative is not None:
                response_message += (
                    f" Un altre dia amb menys ocupació és el "
                    f"{day_alternative['date']} a les "
                    f"{day_alternative['start']}."
                )
    else:
        quietest = get_quietest_slot(
            space_id,
            date_reference.weekday() if has_explicit_day else None,
        )
        if quietest is None:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        quietest_start = quietest["start"]
        weekday = quietest["weekday"]
        source_weekday = weekday
        response_message = (
            f"Les {quietest_start} de {WEEKDAYS_CA[weekday]} acostumen "
            "a ser una de les franges amb menys ocupació."
        )
        if any(
            phrase in normalized
            for phrase in (
                "altre dia",
                "altre jorn",
                "otro dia",
                "another day",
                "other day",
            )
        ):
            day_alternative = get_best_day_alternative(
                space_id,
                date_reference.isoformat(),
                quietest_start,
            )
            if day_alternative is not None:
                response_message += (
                    f" Un altre dia amb menys ocupació és el "
                    f"{day_alternative['date']} a les "
                    f"{day_alternative['start']}."
                )

    return {
        "message": response_message,
        "sources": [
            {
                "type": "historical_occupancy",
                "space_id": space_id,
                "date_reference": WEEKDAYS_CA[source_weekday],
            }
        ],
        "can_answer": True,
    }
