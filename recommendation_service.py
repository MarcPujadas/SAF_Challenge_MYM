from datetime import date, datetime
from typing import Any


SPACE_NAMES = {"fitness": "Sala Fitness"}
SIMULATED_FITNESS_SCORES = {
    "09:00": 42,
    "11:00": 55,
    "12:00": 48,
    "14:00": 58,
    "16:00": 67,
    "17:00": 74,
    "18:00": 89,
    "19:00": 52,
    "20:00": 65,
    "21:00": 45,
}
FITNESS_EXCLUDED_ALTERNATIVES = {"10:00", "15:00"}


def occupancy_level(score: int) -> str:
    if score >= 85:
        return "very_high"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


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


def recommend(
    space_id: str,
    date_value: str,
    preferred_start: str,
    preferred_end: str,
) -> dict[str, Any] | None:
    parsed_date, start_minutes = validate_date_time(date_value, preferred_start)
    _, end_minutes = validate_date_time(date_value, preferred_end)
    if end_minutes <= start_minutes:
        raise ValueError("preferred_end must be later than preferred_start.")
    if space_id not in SPACE_NAMES or space_id != "fitness":
        return None

    requested_score = SIMULATED_FITNESS_SCORES.get(preferred_start)
    if requested_score is None:
        return None

    candidate_slots = [
        (slot, score)
        for slot, score in SIMULATED_FITNESS_SCORES.items()
        if start_minutes < validate_date_time(date_value, slot)[1] <= end_minutes
        and slot not in FITNESS_EXCLUDED_ALTERNATIVES
        and score < requested_score
    ]
    alternative = (
        min(candidate_slots, key=lambda item: (item[1], item[0]))
        if candidate_slots
        else None
    )
    if alternative is None:
        recommended_slot = None
        message = "No hi ha cap alternativa millor amb les dades simulades disponibles."
    else:
        alternative_start, alternative_score = alternative
        recommended_slot = {
            "start": alternative_start,
            "occupancy_score": alternative_score,
            "occupancy_level": occupancy_level(alternative_score),
        }
        message = (
            f"Les {alternative_start} acostumen a tenir menys ocupació simulada "
            f"que les {preferred_start}."
        )

    return {
        "requested_slot": {
            "start": preferred_start,
            "occupancy_score": requested_score,
            "occupancy_level": occupancy_level(requested_score),
        },
        "recommended_slot": recommended_slot,
        "message": message,
        "confidence": "low",
        "basis": {
            "space": SPACE_NAMES[space_id],
            "weekday": parsed_date.strftime("%A"),
            "historical_period": "simulated demonstration data (not historical)",
        },
    }


def quietest_slot(space_id: str) -> tuple[str, int] | None:
    if space_id != "fitness":
        return None
    return min(SIMULATED_FITNESS_SCORES.items(), key=lambda item: item[1])
