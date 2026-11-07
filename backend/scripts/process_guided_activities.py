from __future__ import annotations

from hashlib import sha1
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "guided_activity_sessions.csv"
)


REQUIRED_COLUMNS = [
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


def normalize_time(value):
    if pd.isna(value):
        return None

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    text = str(value).strip()

    parsed = pd.to_datetime(
        text,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.strftime("%H:%M")


def time_to_minutes(value):
    if value is None:
        return None

    hours, minutes = value.split(":")

    return (
        int(hours) * 60
        + int(minutes)
    )


def build_session_id(
    session_date,
    activity_code,
    start_time,
    room,
):
    key = (
        f"{session_date}|"
        f"{activity_code}|"
        f"{start_time}|"
        f"{room}"
    )

    digest = sha1(
        key.encode("utf-8")
    ).hexdigest()[:12]

    return f"ga_{digest}"


def resolve_dominant_value(
    group,
    column,
):
    """
    Return the most frequent value for a field
    inside a historical session.

    If two or more values are tied for first place,
    the data cannot be resolved safely and the
    processing stops.
    """

    counts = (
        group[column]
        .value_counts(
            dropna=False
        )
    )

    if counts.empty:
        return None

    if len(counts) == 1:
        return counts.index[0]

    top_count = counts.iloc[0]

    tied = counts[
        counts == top_count
    ]

    if len(tied) > 1:
        values = [
            str(value)
            for value in tied.index.tolist()
        ]

        raise RuntimeError(
            "No es pot resoldre "
            f"'{column}': hi ha un empat "
            "entre els valors "
            + ", ".join(values)
        )

    return counts.index[0]


def main():
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_excel(
        SOURCE_PATH,
        sheet_name="Activitats dirigides",
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise RuntimeError(
            "Falten columnes requerides: "
            + ", ".join(missing_columns)
        )

    print("=" * 80)
    print("PROCESS GUIDED ACTIVITIES")
    print("=" * 80)

    print()
    print(
        "Files originals:",
        len(df),
    )

    exact_duplicates = (
        df.duplicated().sum()
    )

    print(
        "Duplicats exactes:",
        exact_duplicates,
    )

    # --------------------------------------------------
    # Normalize fields
    # --------------------------------------------------

    df["session_date"] = (
        pd.to_datetime(
            df["DataInscripcio"],
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    df["start_time"] = (
        df["HoraInici"]
        .apply(normalize_time)
    )

    df["end_time"] = (
        df["HoraFi"]
        .apply(normalize_time)
    )

    df["AforamentMax"] = (
        pd.to_numeric(
            df["AforamentMax"],
            errors="coerce",
        )
    )

    df["Inscrits"] = (
        pd.to_numeric(
            df["Inscrits"],
            errors="coerce",
        )
    )

    df["PctOcupacio"] = (
        pd.to_numeric(
            df["PctOcupacio"],
            errors="coerce",
        )
    )

    # --------------------------------------------------
    # Remove rows without a valid session key
    # --------------------------------------------------

    key_columns = [
        "session_date",
        "CodiActivitat",
        "start_time",
        "Sala",
    ]

    invalid_mask = (
        df[key_columns]
        .isna()
        .any(axis=1)
    )

    invalid_rows = int(
        invalid_mask.sum()
    )

    print(
        "Files sense clau de sessió:",
        invalid_rows,
    )

    df = df[
        ~invalid_mask
    ].copy()

    # --------------------------------------------------
    # Remove exact duplicates for structural analysis
    # --------------------------------------------------

    unique_rows = (
        df.drop_duplicates()
        .copy()
    )

    print(
        "Files després d'eliminar "
        "duplicats exactes:",
        len(unique_rows),
    )

    # --------------------------------------------------
    # Detect metadata differences inside the same session
    # --------------------------------------------------

    consistency_columns = [
        "Activitat",
        "AforamentMax",
        "end_time",
    ]

    conflicts = []

    for column in consistency_columns:

        counts = (
            unique_rows
            .groupby(
                key_columns,
                dropna=False,
            )[column]
            .nunique(
                dropna=False
            )
        )

        conflicting = (
            counts[
                counts > 1
            ]
        )

        if not conflicting.empty:
            conflicts.append(
                (
                    column,
                    len(conflicting),
                )
            )

    if conflicts:
        print()
        print(
            "CONFLICTES RESOLUBLES "
            "DINS DE SESSIONS"
        )

        print("-" * 80)

        for column, count in conflicts:
            print(
                f"{column}: "
                f"{count} sessions"
            )

        print()
        print(
            "S'utilitzarà el valor més "
            "freqüent de cada sessió."
        )

        print(
            "Si hi ha un empat, el procés "
            "s'aturarà per evitar inventar dades."
        )

    # --------------------------------------------------
    # Count original and distinct source rows per session
    # --------------------------------------------------

    source_counts = (
        df
        .groupby(
            key_columns,
            dropna=False,
        )
        .size()
        .rename(
            "source_rows"
        )
        .reset_index()
    )

    distinct_counts = (
        unique_rows
        .groupby(
            key_columns,
            dropna=False,
        )
        .size()
        .rename(
            "distinct_source_rows"
        )
        .reset_index()
    )

    # --------------------------------------------------
    # Build one clean row per historical session
    # --------------------------------------------------

    session_rows = []

    grouped = (
        unique_rows
        .groupby(
            key_columns,
            dropna=False,
        )
    )

    for key, _ in grouped:

        (
            session_date,
            activity_code,
            start_time,
            room,
        ) = key

        # Important:
        # use the ORIGINAL rows here so frequency
        # information is preserved.
        #
        # Example:
        # 17:50 appears 9 times
        # 17:45 appears 1 time
        #
        # If duplicates were removed first, this
        # would incorrectly look like a 1-1 tie.

        original_group = df[
            (
                df["session_date"]
                == session_date
            )
            & (
                df["CodiActivitat"]
                == activity_code
            )
            & (
                df["start_time"]
                == start_time
            )
            & (
                df["Sala"]
                == room
            )
        ].copy()

        activity_name = (
            resolve_dominant_value(
                original_group,
                "Activitat",
            )
        )

        end_time = (
            resolve_dominant_value(
                original_group,
                "end_time",
            )
        )

        capacity = (
            resolve_dominant_value(
                original_group,
                "AforamentMax",
            )
        )

        peak_enrolled = (
            original_group[
                "Inscrits"
            ].max()
        )

        peak_occupancy_pct = (
            original_group[
                "PctOcupacio"
            ].max()
        )

        session_rows.append(
            {
                "session_date":
                    session_date,

                "CodiActivitat":
                    activity_code,

                "start_time":
                    start_time,

                "Sala":
                    room,

                "activity_name":
                    activity_name,

                "end_time":
                    end_time,

                "capacity":
                    capacity,

                "peak_enrolled":
                    peak_enrolled,

                "peak_occupancy_pct":
                    peak_occupancy_pct,
            }
        )

    sessions = pd.DataFrame(
        session_rows
    )

    # --------------------------------------------------
    # Add source row statistics
    # --------------------------------------------------

    sessions = sessions.merge(
        source_counts,
        on=key_columns,
        how="left",
    )

    sessions = sessions.merge(
        distinct_counts,
        on=key_columns,
        how="left",
    )

    # --------------------------------------------------
    # Calculate duration
    # --------------------------------------------------

    def calculate_duration(row):
        start = time_to_minutes(
            row["start_time"]
        )

        end = time_to_minutes(
            row["end_time"]
        )

        if (
            start is None
            or end is None
        ):
            return None

        duration = (
            end - start
        )

        # Defensive support for sessions crossing
        # midnight, even though this should not occur
        # in the current SAF dataset.
        if duration < 0:
            duration += (
                24 * 60
            )

        return duration

    sessions["duration_min"] = (
        sessions.apply(
            calculate_duration,
            axis=1,
        )
    )

    # --------------------------------------------------
    # Build stable session IDs
    # --------------------------------------------------

    sessions["session_id"] = (
        sessions.apply(
            lambda row: (
                build_session_id(
                    row[
                        "session_date"
                    ],
                    row[
                        "CodiActivitat"
                    ],
                    row[
                        "start_time"
                    ],
                    row[
                        "Sala"
                    ],
                )
            ),
            axis=1,
        )
    )

    # --------------------------------------------------
    # Mark historical over-capacity sessions
    # --------------------------------------------------

    sessions["over_capacity"] = (
        sessions[
            "peak_enrolled"
        ]
        > sessions[
            "capacity"
        ]
    )

    # --------------------------------------------------
    # Rename source columns
    # --------------------------------------------------

    sessions = sessions.rename(
        columns={
            "CodiActivitat":
                "activity_code",
            "Sala":
                "room",
        }
    )

    # --------------------------------------------------
    # Final column order
    # --------------------------------------------------

    sessions = sessions[
        [
            "session_id",
            "session_date",
            "activity_code",
            "activity_name",
            "room",
            "start_time",
            "end_time",
            "duration_min",
            "capacity",
            "peak_enrolled",
            "peak_occupancy_pct",
            "over_capacity",
            "source_rows",
            "distinct_source_rows",
        ]
    ]

    sessions = (
        sessions
        .sort_values(
            [
                "session_date",
                "start_time",
                "room",
                "activity_name",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    duplicate_session_ids = (
        sessions[
            "session_id"
        ].duplicated().sum()
    )

    if duplicate_session_ids:
        raise RuntimeError(
            "S'han generat IDs de sessió "
            "duplicats."
        )

    missing_required = (
        sessions[
            [
                "session_id",
                "session_date",
                "activity_code",
                "activity_name",
                "room",
                "start_time",
                "end_time",
                "capacity",
            ]
        ]
        .isna()
        .any(axis=1)
        .sum()
    )

    if missing_required:
        raise RuntimeError(
            "Hi ha sessions finals amb "
            "camps obligatoris buits."
        )

    # --------------------------------------------------
    # Save processed data
    # --------------------------------------------------

    sessions.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)

    print(
        "Sessions històriques:",
        len(sessions),
    )

    print(
        "Codis d'activitat:",
        sessions[
            "activity_code"
        ].nunique(),
    )

    print(
        "Noms d'activitat:",
        sessions[
            "activity_name"
        ].nunique(),
    )

    print(
        "Sales:",
        sessions[
            "room"
        ].nunique(),
    )

    print(
        "Sessions sobre aforament:",
        int(
            sessions[
                "over_capacity"
            ].sum()
        ),
    )

    print(
        "IDs de sessió duplicats:",
        duplicate_session_ids,
    )

    print()
    print("DURADES")
    print("-" * 80)

    print(
        sessions[
            "duration_min"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("SALES")
    print("-" * 80)

    print(
        sessions[
            "room"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print("Fitxer creat:")
    print(
        OUTPUT_PATH
    )

    print()
    print("=" * 80)
    print(
        "GUIDED ACTIVITIES PROCESSING OK"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()