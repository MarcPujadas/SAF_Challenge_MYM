from datetime import date as date_type
from pathlib import Path

import pandas as pd

from app.config.services import SPACE_ID_BY_SERVICE_ID
from app.config.schedules import STANDARD_75_MINUTE_SLOTS
from app.services.schedule_service import time_to_minutes

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
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