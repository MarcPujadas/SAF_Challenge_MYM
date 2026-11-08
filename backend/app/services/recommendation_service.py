from datetime import date, datetime, timedelta

from app.common import ApiError
from app.config.services import SERVICE_BY_ID
from app.services.historical_service import (
    get_best_alternative,
    get_historical_occupancy,
    get_historical_occupancy_by_date,
    get_service_best_alternative,
    get_service_historical_occupancy,
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
            "No tenim prou dades històriques d'aquesta franja "
            "per fer una previsió fiable."
        )

    level_labels = {
        "low": "baixa",
        "medium": "mitjana",
        "high": "alta",
        "very_high": "molt alta",
        "unknown": "desconeguda",
    }

    requested_level = level_labels[requested["occupancy_level"]]
    requested_score = requested["occupancy_score"]
    requested_start = requested["start_time"]

    if alternative is None or (
        alternative["occupancy_score"] >= requested_score
    ):
        if requested["occupancy_level"] == "low":
            return (
                f"És una bona franja: a les {requested_start} "
                f"l'ocupació acostuma a ser baixa ({requested_score}/100)."
            )

        return (
            f"A les {requested_start} l'ocupació acostuma a ser "
            f"{requested_level} ({requested_score}/100). "
            "No he trobat cap franja propera clarament millor."
        )

    return (
        f"A les {requested_start} acostuma a haver-hi una ocupació "
        f"{requested_level}. Si pots, et recomano les {alternative['start']}, "
        f"que acostumen a estar més tranquil·les "
        f"({alternative['occupancy_score']}/100 vs {requested_score}/100)."
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


def recommend_service(
    service_id: str,
    date: str,
    preferred_start: str,
    preferred_end: str | None = None,
):
    service = SERVICE_BY_ID.get(service_id)
    if service is None:
        raise ApiError(
            "INVALID_SERVICE",
            "The requested service does not exist.",
            404,
        )
    if service_id != "fitness":
        weekday = get_weekday_from_date(date)
        return {
            "requested_slot": {
                "start": preferred_start,
                "occupancy_score": None,
                "occupancy_level": "unknown",
            },
            "recommended_slot": None,
            "message": (
                "No hi ha una previsió agregada validada "
                "per aquest servei."
            ),
            "confidence": "low",
            "basis": {
                "service_id": service_id,
                "weekday": WEEKDAY_NAMES[weekday],
                "historical_period": None,
            },
            "recommendation_available": False,
            "unavailable_reason": "aggregated_forecast_not_validated",
        }

    weekday = get_weekday_from_date(date)
    requested = get_service_historical_occupancy(
        service_id,
        weekday,
        preferred_start,
        aggregate=True,
    )
    if requested["occupancy_score"] is None:
        return {
            "requested_slot": {
                "start": preferred_start,
                "occupancy_score": None,
                "occupancy_level": "unknown",
            },
            "recommended_slot": None,
            "message": "No ho sé amb les dades disponibles.",
            "confidence": "low",
            "basis": {
                "service_id": service_id,
                "weekday": WEEKDAY_NAMES[get_weekday_from_date(date)],
                "historical_period": None,
            },
            "recommendation_available": False,
            "unavailable_reason": "historical_data_unavailable",
        }
    alternative_result = get_service_best_alternative(
        service_id,
        weekday,
        preferred_start,
        aggregate=True,
    )
    alternative = alternative_result["alternative"]
    if (
        alternative is not None
        and alternative["occupancy_score"]
        >= requested["occupancy_score"]
    ):
        alternative = None
    result = {
        "requested_slot": {
            "start": requested["start_time"],
            "occupancy_score": requested["occupancy_score"],
            "occupancy_level": requested["occupancy_level"],
        },
        "recommended_slot": (
            {
                "start": alternative["start"],
                "occupancy_score": alternative["occupancy_score"],
                "occupancy_level": alternative["occupancy_level"],
            }
            if alternative is not None
            else None
        ),
        "message": build_message(requested, alternative),
        "confidence": get_confidence(requested["samples"]),
        "basis": {
            "service_id": service_id,
            "weekday": WEEKDAY_NAMES[weekday],
            "historical_period": None,
        },
    }
    return result


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
