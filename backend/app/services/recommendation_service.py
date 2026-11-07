from datetime import datetime

from app.services.historical_service import (
    get_best_alternative,
    get_historical_occupancy,
)


WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def get_weekday_from_date(date_string):
    date = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    return date.weekday()


def get_confidence(samples):
    if samples >= 20:
        return "high"

    if samples >= 10:
        return "medium"

    return "low"


def build_message(
    requested,
    alternative
):
    if requested["occupancy_level"] == "unknown":
        return (
            "No hi ha prou dades per estimar "
            "l'ocupació d'aquesta franja."
        )

    if alternative is None:
        return (
            "No s'ha trobat una alternativa millor "
            "amb les dades disponibles."
        )

    if (
        alternative["occupancy_score"]
        >= requested["occupancy_score"]
    ):
        return (
            "No s'ha trobat una franja propera "
            "amb menys ocupació."
        )

    return (
        f"Les {alternative['start']} acostumen "
        f"a tenir menys ocupació que les "
        f"{requested['start_time']}."
    )


def recommend(
    space_id,
    date,
    preferred_start,
    preferred_end=None
):
    weekday = get_weekday_from_date(date)

    requested = get_historical_occupancy(
        space_id=space_id,
        weekday=weekday,
        start_time=preferred_start
    )

    alternative = get_best_alternative(
        space_id=space_id,
        weekday=weekday,
        preferred_start=preferred_start
    )

    if requested["occupancy_score"] is None:
        confidence = "low"
    else:
        confidence = get_confidence(
            requested["samples"]
        )

    message = build_message(
        requested,
        alternative
    )

    requested_slot = {
        "start": requested["start_time"],
        "occupancy_score": requested["occupancy_score"],
        "occupancy_level": requested["occupancy_level"]
    }

    recommended_slot = None

    if alternative is not None:
        recommended_slot = {
            "start": alternative["start"],
            "occupancy_score": alternative["occupancy_score"],
            "occupancy_level": alternative["occupancy_level"]
        }

    return {
        "requested_slot": requested_slot,
        "recommended_slot": recommended_slot,
        "message": message,
        "confidence": confidence,
        "basis": {
            "space_id": space_id,
            "weekday": WEEKDAY_NAMES[weekday],
            "historical_period": (
                "2026-04-01 to 2026-10-31"
            )
        }
    }