from pathlib import Path
from datetime import datetime

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_occupancy.csv"
)


# Torns reals de Fitness detectats al dataset.
#
# Dilluns-divendres:
# torns de 75 minuts.
#
# Dissabte:
# horari diferent.
#
# Diumenge:
# el SAF tanca a les 14:00.
STANDARD_75_MINUTE_SLOTS = {
    0: [
        "07:15", "08:30", "09:45", "11:00",
        "12:15", "13:30", "14:45", "16:00",
        "17:15", "18:30", "19:45"
    ],
    1: [
        "07:15", "08:30", "09:45", "11:00",
        "12:15", "13:30", "14:45", "16:00",
        "17:15", "18:30", "19:45"
    ],
    2: [
        "07:15", "08:30", "09:45", "11:00",
        "12:15", "13:30", "14:45", "16:00",
        "17:15", "18:30", "19:45"
    ],
    3: [
        "07:15", "08:30", "09:45", "11:00",
        "12:15", "13:30", "14:45", "16:00",
        "17:15", "18:30", "19:45"
    ],
    4: [
        "07:15", "08:30", "09:45", "11:00",
        "12:15", "13:30", "14:45", "16:00",
        "17:15", "18:30", "19:45"
    ],
    5: [
        "08:30", "09:45", "11:00",
        "12:15", "13:30", "14:45",
        "16:00", "17:15", "18:30"
    ],
    6: [
        "09:45", "11:00", "12:15"
    ],
}


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


def time_to_minutes(value):
    time = datetime.strptime(value, "%H:%M")

    return time.hour * 60 + time.minute


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

    if space_id == "sala-fitnes-sala-cardio":
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

    actual_slot = find_nearest_slot(
        start_time,
        valid_slots
    )

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