import re
from datetime import date, timedelta
from typing import Any

from recommendation_service import (
    quietest_slot,
    recommend,
    validate_date_time,
)

UNKNOWN_MESSAGE = "No ho sé amb les dades disponibles."


def advice(space_id: str, date_value: str, start: str) -> dict[str, Any]:
    parsed_date, start_minutes = validate_date_time(date_value, start)
    end_minutes = min(start_minutes + 120, 23 * 60 + 59)
    end = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
    result = recommend(space_id, parsed_date.isoformat(), start, end)
    if result is None:
        return {
            "type": "info",
            "message": UNKNOWN_MESSAGE,
            "alternative": None,
            "occupancy_score": None,
        }

    requested = result["requested_slot"]
    alternative = result["recommended_slot"]
    score = requested["occupancy_score"]
    if score >= 75:
        message = f"Aquesta franja té una ocupació simulada alta ({score}/100)."
        advice_type = "warning"
    else:
        message = f"Aquesta franja té una ocupació simulada de {score}/100."
        advice_type = "recommendation" if alternative is not None else "info"

    alternative_data = None
    if alternative is not None:
        alternative_data = {
            "start": alternative["start"],
            "message": f"Les {alternative['start']} tenen menys ocupació simulada.",
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

    date_reference = date.today()
    if "demà" in normalized or "dema" in normalized or "tomorrow" in normalized:
        date_reference += timedelta(days=1)
    elif "avui" in normalized or "today" in normalized:
        pass
    else:
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
        start = requested_time.group()
        _, start_minutes = validate_date_time(date_reference.isoformat(), start)
        end_minutes = min(start_minutes + 120, 23 * 60 + 59)
        end = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        recommendation = recommend("fitness", date_reference.isoformat(), start, end)
        if recommendation is None or recommendation["recommended_slot"] is None:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        alternative_start = recommendation["recommended_slot"]["start"]
        response_message = (
            f"Segons les dades simulades, les {alternative_start} tenen menys "
            f"ocupació prevista que les {start}."
        )
    else:
        quietest = quietest_slot("fitness")
        if quietest is None:
            return {
                "message": UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            }
        quietest_start, quietest_score = quietest
        response_message = (
            f"Amb les dades simulades disponibles, les {quietest_start} tenen "
            f"la puntuació d'ocupació més baixa ({quietest_score}/100)."
        )

    return {
        "message": response_message,
        "sources": [
            {
                "type": "simulated_occupancy",
                "space_id": "fitness",
                "date_reference": date_reference.strftime("%A"),
            }
        ],
        "can_answer": True,
    }
