from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)


def main():
    df = pd.read_excel(
        DATA_PATH,
        sheet_name="Activitats dirigides",
    )

    print("=" * 80)
    print("SAF GUIDED ACTIVITIES ANALYSIS")
    print("=" * 80)

    print()
    print("ROWS")
    print("-" * 80)
    print("Total:", len(df))

    print()
    print("COLUMNS")
    print("-" * 80)

    for column in df.columns:
        print(column)

    # -------------------------------------------------
    # Dates
    # -------------------------------------------------

    dates = pd.to_datetime(
        df["DataInscripcio"],
        errors="coerce",
    )

    print()
    print("DATE RANGE")
    print("-" * 80)

    print(
        "Valid dates:",
        dates.notna().sum(),
    )

    if dates.notna().any():
        print(
            "From:",
            dates.min().date(),
        )

        print(
            "To:",
            dates.max().date(),
        )

    # -------------------------------------------------
    # Null values
    # -------------------------------------------------

    print()
    print("NULL VALUES")
    print("-" * 80)

    nulls = (
        df.isna()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    for column, count in nulls.items():
        if count > 0:
            print(
                f"{column:25} {count}"
            )

    # -------------------------------------------------
    # Exact duplicates
    # -------------------------------------------------

    duplicates = df.duplicated().sum()

    print()
    print("EXACT DUPLICATES")
    print("-" * 80)
    print(duplicates)

    # -------------------------------------------------
    # Cardinality
    # -------------------------------------------------

    print()
    print("UNIQUE VALUES")
    print("-" * 80)

    for column in [
        "CodiActivitat",
        "Activitat",
        "Sala",
        "HoraInici",
        "HoraFi",
    ]:
        print(
            f"{column:25}",
            df[column].nunique(
                dropna=True
            ),
        )

    # -------------------------------------------------
    # Rooms
    # -------------------------------------------------

    print()
    print("ROOMS")
    print("-" * 80)

    rooms = (
        df["Sala"]
        .value_counts(
            dropna=False
        )
    )

    for room, count in rooms.items():
        print(
            f"{str(room):35} {count}"
        )

    # -------------------------------------------------
    # Activities
    # -------------------------------------------------

    print()
    print("TOP ACTIVITIES")
    print("-" * 80)

    activities = (
        df["Activitat"]
        .value_counts()
        .head(30)
    )

    for activity, count in activities.items():
        print(
            f"{str(activity):45} {count}"
        )

    # -------------------------------------------------
    # Duration
    # -------------------------------------------------

    start = pd.to_datetime(
        df["HoraInici"].astype(str),
        format="%H:%M:%S",
        errors="coerce",
    )

    if start.isna().all():
        start = pd.to_datetime(
            df["HoraInici"].astype(str),
            errors="coerce",
        )

    end = pd.to_datetime(
        df["HoraFi"].astype(str),
        format="%H:%M:%S",
        errors="coerce",
    )

    if end.isna().all():
        end = pd.to_datetime(
            df["HoraFi"].astype(str),
            errors="coerce",
        )

    duration = (
        end - start
    ).dt.total_seconds() / 60

    df["duration_min"] = duration

    print()
    print("DURATIONS")
    print("-" * 80)

    duration_counts = (
        df["duration_min"]
        .dropna()
        .value_counts()
        .sort_values(
            ascending=False
        )
    )

    for minutes, count in (
        duration_counts.head(20).items()
    ):
        print(
            f"{minutes:6.0f} min "
            f"-> {count:6}"
        )

    # -------------------------------------------------
    # Capacity consistency
    # -------------------------------------------------

    capacity = pd.to_numeric(
        df["AforamentMax"],
        errors="coerce",
    )

    enrolled = pd.to_numeric(
        df["Inscrits"],
        errors="coerce",
    )

    occupancy = pd.to_numeric(
        df["PctOcupacio"],
        errors="coerce",
    )

    calculated = (
        enrolled
        / capacity.replace(0, pd.NA)
        * 100
    )

    difference = (
        calculated - occupancy
    ).abs()

    inconsistent = (
        difference > 1
    ).sum()

    print()
    print("CAPACITY / OCCUPANCY")
    print("-" * 80)

    print(
        "Rows with capacity:",
        capacity.notna().sum(),
    )

    print(
        "Rows with enrolled:",
        enrolled.notna().sum(),
    )

    print(
        "Rows with occupancy:",
        occupancy.notna().sum(),
    )

    print(
        "Occupancy inconsistencies > 1%:",
        inconsistent,
    )

    print(
        "Over capacity:",
        (
            enrolled > capacity
        ).sum(),
    )

    # -------------------------------------------------
    # Determine dataset grain
    # -------------------------------------------------

    print()
    print("POSSIBLE SESSION KEY")
    print("-" * 80)

    session_columns = [
        "DataInscripcio",
        "CodiActivitat",
        "HoraInici",
        "HoraFi",
        "Sala",
    ]

    session_duplicates = (
        df.duplicated(
            subset=session_columns,
            keep=False,
        )
    )

    print(
        "Rows sharing same "
        "date/code/time/room:",
        session_duplicates.sum(),
    )

    unique_sessions = (
        df[session_columns]
        .drop_duplicates()
    )

    print(
        "Unique date/code/time/room "
        "combinations:",
        len(unique_sessions),
    )

    # -------------------------------------------------
    # Activity code consistency
    # -------------------------------------------------

    print()
    print("ACTIVITY CODE CONSISTENCY")
    print("-" * 80)

    code_summary = (
        df.groupby(
            "CodiActivitat"
        )
        .agg(
            names=(
                "Activitat",
                "nunique"
            ),
            rooms=(
                "Sala",
                "nunique"
            ),
            starts=(
                "HoraInici",
                "nunique"
            ),
            capacities=(
                "AforamentMax",
                "nunique"
            ),
            rows=(
                "CodiActivitat",
                "size"
            ),
        )
    )

    variable_codes = code_summary[
        (code_summary["names"] > 1)
        | (code_summary["rooms"] > 1)
        | (code_summary["starts"] > 1)
        | (code_summary["capacities"] > 1)
    ]

    print(
        "Activity codes:",
        len(code_summary),
    )

    print(
        "Codes with varying metadata:",
        len(variable_codes),
    )

    if not variable_codes.empty:
        print()
        print(
            variable_codes
            .sort_values(
                "rows",
                ascending=False,
            )
            .head(20)
            .to_string()
        )

    # -------------------------------------------------
    # Example rows
    # -------------------------------------------------

    print()
    print("SAMPLE ROWS")
    print("-" * 80)

    sample_columns = [
        "DataInscripcio",
        "CodiActivitat",
        "Activitat",
        "AforamentMax",
        "Inscrits",
        "PctOcupacio",
        "HoraInici",
        "HoraFi",
        "Sala",
    ]

    print(
        df[
            sample_columns
        ]
        .head(15)
        .to_string(
            index=False
        )
    )

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()