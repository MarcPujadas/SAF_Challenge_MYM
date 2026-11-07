from datetime import date, datetime, timedelta

from app.services.historical_service import (
    get_best_alternative,
    get_historical_occupancy,
    get_historical_occupancy_by_date,
    add_occupancy_scores,
    calculate_slot_statistics,
    occupancy_level,
    prepare_space_data,
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


def get_best_day_alternative(
    space_id: str,
    preferred_date: str,
    preferred_start: str,
):
    requested_date = date.fromisoformat(preferred_date)
    requested = get_historical_occupancy(
        space_id=space_id,
        weekday=requested_date.weekday(),
        start_time=preferred_start,
    )
    if requested["occupancy_score"] is None:
        return None

    start_time = requested["start_time"]
    records = get_historical_occupancy_by_date(
        space_id=space_id,
    )
    if records.empty:
        return None

    records = records[records["start_time"] == start_time].copy()
    if records.empty:
        return None
    records["weekday"] = records["date"].map(
        lambda value: date.fromisoformat(value).weekday()
    )
    weekday_scores = records.groupby("weekday")["occupancy_score"].mean()

    alternatives = []
    for day_offset in range(1, 8):
        candidate_date = requested_date + timedelta(days=day_offset)
        candidate_score = weekday_scores.get(candidate_date.weekday())
        if (
            candidate_score is not None
            and candidate_score < requested["occupancy_score"]
        ):
            alternatives.append(
                (
                    float(candidate_score),
                    day_offset,
                    candidate_date,
                )
            )
    if not alternatives:
        return None

    score, _, candidate_date = min(alternatives)
    occupancy_score = int(round(score))
    return {
        "date": candidate_date.isoformat(),
        "start": start_time,
        "occupancy_score": occupancy_score,
        "occupancy_level": occupancy_level(occupancy_score),
    }


def get_quietest_slot(space_id: str, weekday: int | None = None):
    weekdays = range(7) if weekday is None else (weekday,)
    options = []
    for current_weekday in weekdays:
        statistics = add_occupancy_scores(
            calculate_slot_statistics(
                prepare_space_data(space_id, current_weekday)
            )
        )
        if statistics.empty:
            continue
        for row in statistics.itertuples():
            options.append(
                {
                    "weekday": current_weekday,
                    "start": row.start_time,
                    "occupancy_score": int(row.occupancy_score),
                    "samples": int(row.samples),
                }
            )
    if not options:
        return None
    return min(
        options,
        key=lambda option: (
            option["occupancy_score"],
            option["start"],
            option["weekday"],
        ),
    )
