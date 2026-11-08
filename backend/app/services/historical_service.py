from contextlib import closing
from datetime import date as date_type
from pathlib import Path

import pandas as pd

from app.config.services import SPACE_ID_BY_SERVICE_ID
from app.config.schedules import STANDARD_75_MINUTE_SLOTS
from app.config.service_spaces import SPACE_IDS_BY_SERVICE_ID
from app.database.database import get_connection
from app.services.schedule_service import (
    build_slots,
    minutes_to_time,
    time_to_minutes,
)

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "local"
    / "historical_occupancy.csv"
)


# Compatibility with the existing historical service.
FITNESS_VALID_SLOTS = STANDARD_75_MINUTE_SLOTS


def occupancy_level(score):
    if score < 35:
        return "low"

    if score < 65:
        return "medium"

    if score < 85:
        return "high"

    return "very_high"


def load_historical_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Historical occupancy data not found. "
            "Run scripts/process_historical_data.py first."
        )

    return pd.read_csv(DATA_PATH)


def get_valid_slots(space_id, weekday, available_slots):
    """
    Elimina franges que sabem que no representen torns reals.

    De moment només Fitness necessita aquest tractament especial.
    """

    if space_id == SPACE_ID_BY_SERVICE_ID["fitness"]:
        return FITNESS_VALID_SLOTS.get(weekday, [])

    return sorted(available_slots)


def find_nearest_slot(requested_time, valid_slots):
    if not valid_slots:
        return None

    requested_minutes = time_to_minutes(requested_time)

    return min(
        valid_slots,
        key=lambda slot: abs(
            time_to_minutes(slot) - requested_minutes
        )
    )


def prepare_space_data(space_id, weekday):
    df = load_historical_data()

    space_data = df[
        (df["space_id"] == space_id)
        & (df["weekday"] == weekday)
    ].copy()

    if space_data.empty:
        return space_data

    valid_slots = get_valid_slots(
        space_id,
        weekday,
        space_data["start_time"].unique()
    )

    space_data = space_data[
        space_data["start_time"].isin(valid_slots)
    ].copy()

    return space_data


def prepare_service_data(service_id, weekday=None, *, normalized=True):
    """Prepare service history from normalized SAF records by default."""
    if normalized:
        return _validated_service_data(service_id, weekday)
    return _prepare_legacy_service_data(service_id, weekday)


def _prepare_legacy_service_data(service_id, weekday=None):
    if service_id not in SPACE_IDS_BY_SERVICE_ID:
        raise ValueError(f"Unknown service_id: {service_id}")

    df = load_historical_data()
    if df.empty:
        return df.copy()
    service_data = df[
        df["space_id"].isin(SPACE_IDS_BY_SERVICE_ID[service_id])
    ].copy()
    if "mapping_status" in service_data.columns:
        service_data = service_data[
            service_data["mapping_status"] == "mapped"
        ].copy()
    if weekday is not None:
        if "weekday" in service_data.columns:
            service_data = service_data[
                service_data["weekday"].astype(int) == int(weekday)
            ].copy()
        else:
            service_data = service_data[
                service_data["date"].map(
                    lambda value: date_type.fromisoformat(str(value)).weekday()
                )
                == int(weekday)
            ].copy()
    service_data["service_id"] = service_id
    return service_data.reset_index(drop=True)


def _service_resource_ids(service_id, space_id=None):
    if service_id not in SPACE_IDS_BY_SERVICE_ID:
        raise ValueError(f"Unknown service_id: {service_id}")
    resource_ids = SPACE_IDS_BY_SERVICE_ID[service_id]
    if space_id is not None:
        if space_id not in resource_ids:
            raise ValueError(
                f"Space {space_id!r} is not mapped to {service_id!r}."
            )
        return (space_id,)
    return resource_ids


def _service_forecast_resource(service_id):
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT link.space_id, link.capacity_mode
            FROM service_spaces AS link
            JOIN spaces ON spaces.id = link.space_id
            WHERE link.service_id = ?
                AND link.is_active = 1
                AND link.is_virtual = 0
            ORDER BY link.display_order, link.space_id
            """,
            (service_id,),
        ).fetchall()
    if (
        service_id == "fitness"
        and len(rows) == 1
        and rows[0]["capacity_mode"] == "people"
    ):
        return rows[0]["space_id"]
    return None


def _validated_service_data(service_id, weekday=None):
    columns = [
        "service_id",
        "space_id",
        "date",
        "weekday",
        "start_time",
        "people_count",
        "capacity_people_snapshot",
        "occupancy_ratio",
    ]
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT
                usage.service_id,
                usage.space_id,
                usage.date,
                usage.weekday,
                usage.start_time,
                usage.people_count,
                usage.capacity_people_snapshot,
                usage.occupancy_ratio
            FROM historical_usage AS usage
            JOIN data_sources AS source ON source.id = usage.source_id
            JOIN service_spaces AS link
                ON link.service_id = usage.service_id
                AND link.space_id = usage.space_id
            WHERE usage.service_id = ?
                AND usage.mapping_status = 'mapped'
                AND usage.capacity_mode = 'people'
                AND link.is_active = 1
                AND link.is_virtual = 0
                AND link.capacity_mode = 'people'
                AND usage.date IS NOT NULL
                AND usage.start_time IS NOT NULL
                AND source.source_type != 'application_operational'
                AND (
                    source.checksum IS NULL
                    OR source.checksum = usage.source_checksum
                )
                AND (
                    usage.occupancy_ratio IS NOT NULL
                    OR (
                        usage.people_count IS NOT NULL
                        AND usage.capacity_people_snapshot > 0
                    )
                )
            ORDER BY usage.date, usage.start_time, usage.space_id
            """,
            (service_id,),
        ).fetchall()
    data = pd.DataFrame([dict(row) for row in rows], columns=columns)
    if data.empty:
        return data
    data["date"] = data["date"].astype(str)
    data["weekday"] = data.apply(
        lambda row: (
            int(row["weekday"])
            if pd.notna(row["weekday"])
            else date_type.fromisoformat(row["date"]).weekday()
        ),
        axis=1,
    )
    data["occupancy_ratio"] = data.apply(
        lambda row: (
            float(row["occupancy_ratio"])
            if pd.notna(row["occupancy_ratio"])
            else float(row["people_count"])
            / float(row["capacity_people_snapshot"])
        ),
        axis=1,
    )
    if weekday is not None:
        data = data[data["weekday"] == int(weekday)]
    return data.reset_index(drop=True)


def _score_service_slot(slot_data):
    if slot_data.empty:
        return {
            "occupancy_score": None,
            "occupancy_level": "unknown",
            "occupancy_ratio": None,
            "samples": 0,
            "unavailable_reason": "historical_data_unavailable",
        }
    daily_ratios = slot_data.groupby("date")["occupancy_ratio"].mean()
    average_ratio = float(daily_ratios.mean())
    score = max(0, min(round(average_ratio * 100), 100))
    return {
        "occupancy_score": int(score),
        "occupancy_level": occupancy_level(score),
        "occupancy_ratio": round(average_ratio, 4),
        "samples": int(len(daily_ratios)),
    }


def get_service_historical_occupancy(
    service_id,
    weekday,
    start_time,
    *,
    space_id=None,
    aggregate=True,
):
    if not aggregate:
        resources = [
            get_historical_occupancy(resource_id, weekday, start_time)
            for resource_id in _service_resource_ids(service_id, space_id)
        ]
        return {
            "service_id": service_id,
            "aggregate": False,
            "resources": resources,
        }
    if space_id is not None:
        resource_ids = _service_resource_ids(service_id, space_id)
        resource_id = resource_ids[0]
        result = get_historical_occupancy(
            resource_id,
            weekday,
            start_time,
        )
        return {
            **result,
            "service_id": service_id,
            "aggregate": False,
            "occupancy_ratio": None,
            "source": "historical_occupancy.csv",
        }

    resource_id = _service_forecast_resource(service_id)
    if resource_id is None:
        return {
            "service_id": service_id,
            "aggregate": False,
            "requested_start": start_time,
            "occupancy_score": None,
            "occupancy_level": "unknown",
            "occupancy_ratio": None,
            "samples": 0,
            "unavailable_reason": "aggregated_forecast_not_validated",
            "source": "historical_usage",
        }
    service_data = _validated_service_data(service_id, weekday)
    slot_data = service_data[
        service_data["start_time"] == start_time
    ]
    score = _score_service_slot(slot_data)
    return {
        "service_id": service_id,
        "weekday": int(weekday),
        "requested_start": start_time,
        "start_time": start_time if not slot_data.empty else None,
        **score,
        "aggregate": True,
        "source": "historical_usage",
    }


def get_service_historical_heatmap(
    service_id,
    date_from=None,
    date_to=None,
    *,
    space_id=None,
    aggregate=True,
):
    if not aggregate:
        return {
            "service_id": service_id,
            "aggregate": False,
            "resources": [
                {
                    "space_id": resource_id,
                    "days": get_historical_heatmap(
                        date_from=date_from,
                        date_to=date_to,
                        space_id=resource_id,
                    ),
                }
                for resource_id in _service_resource_ids(
                    service_id,
                    space_id,
                )
            ],
        }
    if space_id is not None:
        resource_ids = _service_resource_ids(service_id, space_id)
        resource_id = resource_ids[0]
        return {
            "service_id": service_id,
            "aggregate": False,
            "resources": [
                {
                    "space_id": resource_id,
                    "days": get_historical_heatmap(
                        date_from=date_from,
                        date_to=date_to,
                        space_id=resource_id,
                    ),
                }
            ],
        }

    resource_id = _service_forecast_resource(service_id)
    service_data = _validated_service_data(service_id)
    if date_from is None and date_to is None:
        if service_data.empty:
            dates = []
        else:
            start_date = date_type.fromisoformat(
                str(service_data["date"].min())
            )
            end_date = date_type.fromisoformat(
                str(service_data["date"].max())
            )
            dates = []
            while start_date <= end_date:
                dates.append(start_date.isoformat())
                start_date = date_type.fromordinal(
                    start_date.toordinal() + 1
                )
    else:
        start_date = date_type.fromisoformat(date_from or date_to)
        end_date = date_type.fromisoformat(date_to or date_from)
        dates = []
        while start_date <= end_date:
            dates.append(start_date.isoformat())
            start_date = date_type.fromordinal(
                start_date.toordinal() + 1
            )

    if resource_id is None:
        resource_ids = _service_resource_ids(service_id)
        slots_for_day = lambda weekday: sorted(
            {
                start
                for current_resource in resource_ids
                for start, _ in build_slots(
                    current_resource,
                    "",
                    weekday,
                )
            }
        )
        return {
            "service_id": service_id,
            "aggregate": False,
            "days": [
                {
                    "date": date_value,
                    "slots": [
                        {
                            "hour": minutes_to_time(start),
                            "occupancy_score": None,
                            "occupancy_level": "unknown",
                            "occupancy_ratio": None,
                            "samples": 0,
                            "unavailable_reason": (
                                "aggregated_forecast_not_validated"
                            ),
                        }
                        for start in slots_for_day(
                            date_type.fromisoformat(date_value).weekday()
                        )
                    ],
                }
                for date_value in dates
            ],
            "unavailable_reason": "aggregated_forecast_not_validated",
            "source": "historical_usage",
        }

    days = []
    for date_value in dates:
        weekday = date_type.fromisoformat(date_value).weekday()
        historical_day = service_data[
            service_data["weekday"] == weekday
        ]
        valid_slots = get_valid_slots(
            resource_id,
            weekday,
            historical_day["start_time"].unique(),
        )
        slots = []
        for hour in valid_slots:
            slot_data = historical_day[
                historical_day["start_time"] == hour
            ]
            slots.append(
                {
                    "hour": hour,
                    **_score_service_slot(slot_data),
                }
            )
        days.append({"date": date_value, "slots": slots})
    return {
        "service_id": service_id,
        "aggregate": True,
        "days": days,
        "source": "historical_usage",
        "occupancy_ratio_available": True,
    }


def get_service_best_alternative(
    service_id,
    weekday,
    preferred_start,
    *,
    space_id=None,
    aggregate=True,
):
    if not aggregate:
        return {
            "service_id": service_id,
            "aggregate": False,
            "resources": [
                {
                    "space_id": resource_id,
                    "alternative": get_best_alternative(
                        resource_id,
                        weekday,
                        preferred_start,
                    ),
                }
                for resource_id in _service_resource_ids(
                    service_id,
                    space_id,
                )
            ],
        }
    if space_id is not None:
        _service_resource_ids(service_id, space_id)
        return {
            "service_id": service_id,
            "aggregate": False,
            "alternative": get_best_alternative(
                space_id,
                weekday,
                preferred_start,
            ),
        }
    if space_id is None:
        space_id = _service_forecast_resource(service_id)
    if space_id is None:
        return {
            "service_id": service_id,
            "aggregate": False,
            "alternative": None,
            "unavailable_reason": "aggregated_forecast_not_validated",
        }
    service_data = _validated_service_data(service_id, weekday)
    if service_data.empty:
        return {
            "service_id": service_id,
            "aggregate": True,
            "alternative": None,
        }
    requested_data = service_data[
        service_data["start_time"] == preferred_start
    ]
    if requested_data.empty:
        return {
            "service_id": service_id,
            "aggregate": True,
            "alternative": None,
        }
    requested_minutes = time_to_minutes(preferred_start)
    alternatives = []
    for start_time, slot_data in service_data.groupby("start_time"):
        if start_time == preferred_start:
            continue
        distance = abs(time_to_minutes(start_time) - requested_minutes)
        if distance > 180:
            continue
        alternatives.append(
            {
                "start": start_time,
                "distance": distance,
                **_score_service_slot(slot_data),
            }
        )
    if not alternatives:
        alternative = None
    else:
        alternative = min(
            alternatives,
            key=lambda item: (
                item["occupancy_score"],
                item["distance"],
            ),
        )
        alternative.pop("distance")
    return {
        "service_id": service_id,
        "aggregate": True,
        "alternative": alternative,
    }


def get_service_quietest_slot(
    service_id,
    weekday,
    *,
    space_id=None,
    aggregate=True,
):
    if not aggregate:
        results = []
        for resource_id in _service_resource_ids(service_id, space_id):
            resource_data = prepare_space_data(resource_id, weekday)
            if resource_data.empty:
                quietest = None
            else:
                statistics = calculate_slot_statistics(resource_data)
                statistics = add_occupancy_scores(statistics)
                row = statistics.sort_values(
                    ["occupancy_score", "start_time"]
                ).iloc[0]
                quietest = {
                    "start": row["start_time"],
                    "occupancy_score": int(row["occupancy_score"]),
                    "occupancy_level": occupancy_level(
                        int(row["occupancy_score"])
                    ),
                    "samples": int(row["samples"]),
                }
            results.append({"space_id": resource_id, "slot": quietest})
        return {
            "service_id": service_id,
            "aggregate": False,
            "resources": results,
        }
    if space_id is not None:
        _service_resource_ids(service_id, space_id)
        resource_data = prepare_space_data(space_id, weekday)
        if resource_data.empty:
            quietest = None
        else:
            statistics = calculate_slot_statistics(resource_data)
            statistics = add_occupancy_scores(statistics)
            row = statistics.sort_values(
                ["occupancy_score", "start_time"]
            ).iloc[0]
            quietest = {
                "start": row["start_time"],
                "occupancy_score": int(row["occupancy_score"]),
                "occupancy_level": occupancy_level(
                    int(row["occupancy_score"])
                ),
                "samples": int(row["samples"]),
            }
        return {
            "service_id": service_id,
            "aggregate": False,
            "slot": quietest,
        }
    if space_id is None:
        space_id = _service_forecast_resource(service_id)
    if space_id is None:
        return {
            "service_id": service_id,
            "aggregate": False,
            "slot": None,
            "unavailable_reason": "aggregated_forecast_not_validated",
        }
    resource_data = _validated_service_data(service_id, weekday)
    if resource_data.empty:
        quietest = None
    else:
        slot_scores = [
            {
                "start": start_time,
                **_score_service_slot(slot_data),
            }
            for start_time, slot_data in resource_data.groupby("start_time")
        ]
        row = min(
            slot_scores,
            key=lambda item: (
                item["occupancy_score"],
                item["start"],
            ),
        )
        quietest = {
            "start": row["start"],
            "occupancy_score": row["occupancy_score"],
            "occupancy_level": row["occupancy_level"],
            "samples": row["samples"],
        }
    return {
        "service_id": service_id,
        "aggregate": True,
        "slot": quietest,
    }


def calculate_slot_statistics(space_data):
    return (
        space_data
        .groupby("start_time")
        .agg(
            average_reservations=("reservations", "mean"),
            samples=("reservations", "count")
        )
        .reset_index()
    )


def add_occupancy_scores(statistics):
    if statistics.empty:
        return statistics

    reference_peak = (
        statistics["average_reservations"]
        .quantile(0.90)
    )

    if reference_peak <= 0:
        statistics["occupancy_score"] = 0

    else:
        statistics["occupancy_score"] = (
            statistics["average_reservations"]
            / reference_peak
            * 100
        ).round()

    statistics["occupancy_score"] = (
        statistics["occupancy_score"]
        .clip(0, 100)
        .astype(int)
    )

    return statistics


def _empty_historical_occupancy():
    return pd.DataFrame(
        columns=[
            "space_id",
            "date",
            "start_time",
            "reservations",
            "occupancy_score",
            "occupancy_level",
        ]
    )


def _get_scored_historical_occupancy():
    df = load_historical_data()
    if df.empty:
        return _empty_historical_occupancy()

    df = df.copy()
    df["date"] = df["date"].astype(str)
    df["weekday"] = df["date"].map(
        lambda value: date_type.fromisoformat(value).weekday()
    )
    is_fitness = df["space_id"] == SPACE_ID_BY_SERVICE_ID["fitness"]
    if is_fitness.any():
        fitness = df[is_fitness]
        valid_slots = fitness.apply(
            lambda row: row["start_time"]
            in get_valid_slots(
                row["space_id"],
                int(row["weekday"]),
                [row["start_time"]],
            ),
            axis=1,
        )
        df = pd.concat(
            [
                df[~is_fitness],
                fitness[valid_slots],
            ],
            ignore_index=True,
        )
    if df.empty:
        return _empty_historical_occupancy()

    daily_reservations = (
        df.groupby(
            ["space_id", "date", "weekday", "start_time"],
            as_index=False,
        )["reservations"]
        .sum()
    )
    scores = []
    for (current_space, weekday), weekday_data in daily_reservations.groupby(
        ["space_id", "weekday"]
    ):
        statistics = calculate_slot_statistics(weekday_data)
        statistics = add_occupancy_scores(statistics)
        statistics["space_id"] = current_space
        statistics["weekday"] = weekday
        scores.append(
            statistics[
                [
                    "space_id",
                    "weekday",
                    "start_time",
                    "occupancy_score",
                ]
            ]
        )

    slot_scores = pd.concat(scores, ignore_index=True)
    result = daily_reservations.merge(
        slot_scores,
        on=["space_id", "weekday", "start_time"],
        how="left",
    )
    result["occupancy_level"] = result["occupancy_score"].map(
        lambda score: occupancy_level(int(score))
    )
    return result[
        [
            "space_id",
            "date",
            "start_time",
            "reservations",
            "occupancy_score",
            "occupancy_level",
        ]
    ]


def get_historical_occupancy_by_date(
    date_from=None,
    date_to=None,
    space_id=None,
):
    result = _get_scored_historical_occupancy()
    if date_from is not None:
        result = result[result["date"] >= date_from]
    if date_to is not None:
        result = result[result["date"] <= date_to]
    if space_id is not None:
        result = result[result["space_id"] == space_id]
    return result.reset_index(drop=True)


def get_historical_heatmap(
    date_from=None,
    date_to=None,
    space_id=None,
):
    records = get_historical_occupancy_by_date(
        space_id=space_id,
    )
    records = records.copy()
    records["weekday"] = records["date"].map(
        lambda value: date_type.fromisoformat(value).weekday()
    )
    if date_from is None and date_to is None:
        if records.empty:
            return []
        start_date = date_type.fromisoformat(records["date"].min())
        end_date = date_type.fromisoformat(records["date"].max())
    elif date_from is None:
        start_date = date_type.fromisoformat(date_to)
        end_date = start_date
    elif date_to is None:
        start_date = date_type.fromisoformat(date_from)
        end_date = start_date
    else:
        start_date = date_type.fromisoformat(date_from)
        end_date = date_type.fromisoformat(date_to)

    spaces = (
        [space_id]
        if space_id is not None
        else sorted(records["space_id"].unique())
    )
    slots_by_space_weekday = {}
    for current_space_id in spaces:
        space_records = records[
            records["space_id"] == current_space_id
        ]
        for weekday in range(7):
            if current_space_id == SPACE_ID_BY_SERVICE_ID["fitness"]:
                valid_slots = FITNESS_VALID_SLOTS.get(weekday, [])
            else:
                valid_slots = sorted(space_records["start_time"].unique())
            slots_by_space_weekday[(current_space_id, weekday)] = valid_slots

    days = []
    current_date = start_date
    while current_date <= end_date:
        weekday = current_date.weekday()
        valid_slots = sorted(
            {
                slot
                for current_space_id in spaces
                for slot in slots_by_space_weekday[
                    (current_space_id, weekday)
                ]
            }
        )
        weekday_records = records[records["weekday"] == weekday]
        slots = []
        for hour in valid_slots:
            matching_records = weekday_records[
                weekday_records["start_time"] == hour
            ]
            if space_id is not None:
                matching_records = matching_records[
                    matching_records["space_id"] == space_id
                ]
            if matching_records.empty:
                score = None
                level = "unknown"
            else:
                score = int(
                    round(matching_records["occupancy_score"].mean())
                )
                level = occupancy_level(score)
            slots.append(
                {
                    "hour": hour,
                    "occupancy_score": score,
                    "occupancy_level": level,
                }
            )
        days.append(
            {
                "date": current_date.isoformat(),
                "slots": slots,
            }
        )
        current_date = date_type.fromordinal(
            current_date.toordinal() + 1
        )
    return days


def get_historical_occupancy_by_hour():
    daily_occupancy = get_historical_occupancy_by_date()
    if daily_occupancy.empty:
        return pd.DataFrame(
            columns=[
                "space_id",
                "start_time",
                "occupancy_score",
                "occupancy_level",
            ]
        )

    hourly_scores = []
    for space_id, space_records in daily_occupancy.groupby("space_id"):
        slot_statistics = (
            space_records.groupby("start_time", as_index=False)
            .agg(
                average_reservations=("reservations", "mean"),
                samples=("reservations", "count"),
            )
        )
        slot_statistics = add_occupancy_scores(slot_statistics)
        slot_statistics["space_id"] = space_id
        hourly_scores.append(
            slot_statistics[
                [
                    "space_id",
                    "start_time",
                    "occupancy_score",
                    "samples",
                ]
            ]
        )

    return pd.concat(hourly_scores, ignore_index=True)


def get_historical_occupancy(
    space_id,
    weekday,
    start_time
):
    space_data = prepare_space_data(
        space_id,
        weekday
    )

    if space_data.empty:
        return {
            "space_id": space_id,
            "weekday": weekday,
            "requested_start": start_time,
            "start_time": None,
            "occupancy_score": None,
            "occupancy_level": "unknown",
            "average_reservations": None,
            "samples": 0
        }

    valid_slots = sorted(
        space_data["start_time"].unique()
    )

    # Per a prediccions/recomanacions no inventem una franja equivalent:
    # si l'hora demanada no existeix exactament a l'historic, retornem unknown.
    if start_time not in valid_slots:
        return {
            "space_id": space_id,
            "weekday": weekday,
            "requested_start": start_time,
            "start_time": None,
            "occupancy_score": None,
            "occupancy_level": "unknown",
            "average_reservations": None,
            "samples": 0
        }

    actual_slot = start_time

    statistics = calculate_slot_statistics(
        space_data
    )

    statistics = add_occupancy_scores(
        statistics
    )

    selected = statistics[
        statistics["start_time"] == actual_slot
    ]

    if selected.empty:
        return {
            "space_id": space_id,
            "weekday": weekday,
            "requested_start": start_time,
            "start_time": None,
            "occupancy_score": None,
            "occupancy_level": "unknown",
            "average_reservations": None,
            "samples": 0
        }

    row = selected.iloc[0]

    score = int(row["occupancy_score"])

    return {
        "space_id": space_id,
        "weekday": int(weekday),

        # Hora que ha demanat l'usuari
        "requested_start": start_time,

        # Torn real utilitzat per calcular l'ocupació
        "start_time": actual_slot,

        "occupancy_score": score,

        "occupancy_level": occupancy_level(
            score
        ),

        "average_reservations": round(
            float(row["average_reservations"]),
            2
        ),

        "samples": int(row["samples"])
    }


def get_best_alternative(
    space_id,
    weekday,
    preferred_start
):
    space_data = prepare_space_data(
        space_id,
        weekday
    )

    if space_data.empty:
        return None

    statistics = calculate_slot_statistics(
        space_data
    )

    statistics = add_occupancy_scores(
        statistics
    )

    valid_slots = sorted(
        statistics["start_time"].tolist()
    )

    requested_slot = find_nearest_slot(
        preferred_start,
        valid_slots
    )

    if requested_slot is None:
        return None

    requested_minutes = time_to_minutes(
        requested_slot
    )

    # Només recomanem alternatives relativament properes.
    # Evitem que una reserva de les 18:00 recomani les 07:15.
    statistics["distance"] = (
        statistics["start_time"]
        .apply(time_to_minutes)
        .apply(
            lambda value: abs(
                value - requested_minutes
            )
        )
    )

    alternatives = statistics[
        statistics["start_time"] != requested_slot
    ].copy()

    # Màxim 3 hores de diferència.
    nearby = alternatives[
        alternatives["distance"] <= 180
    ].copy()

    if not nearby.empty:
        alternatives = nearby

    if alternatives.empty:
        return None

    best = alternatives.sort_values(
        [
            "occupancy_score",
            "distance"
        ]
    ).iloc[0]

    score = int(
        best["occupancy_score"]
    )

    return {
        "start": best["start_time"],
        "occupancy_score": score,
        "occupancy_level": occupancy_level(
            score
        ),
        "average_reservations": round(
            float(best["average_reservations"]),
            2
        ),
        "samples": int(best["samples"])
    }