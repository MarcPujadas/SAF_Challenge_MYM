from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)


def normalize_time(value):
    if pd.isna(value):
        return None

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    parsed = pd.to_datetime(
        str(value).strip(),
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.strftime("%H:%M")


def main():
    df = pd.read_excel(
        SOURCE_PATH,
        sheet_name="Activitats dirigides",
    )

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

    key_columns = [
        "session_date",
        "CodiActivitat",
        "start_time",
        "Sala",
    ]

    valid = df[
        df[key_columns]
        .notna()
        .all(axis=1)
    ].copy()

    unique_rows = (
        valid
        .drop_duplicates()
        .copy()
    )

    end_counts = (
        unique_rows
        .groupby(
            key_columns,
            dropna=False,
        )["end_time"]
        .nunique(
            dropna=False
        )
    )

    conflicts = (
        end_counts[
            end_counts > 1
        ]
        .reset_index()
    )

    print("=" * 100)
    print("GUIDED ACTIVITY END-TIME CONFLICTS")
    print("=" * 100)

    print()
    print(
        "Sessions conflictives:",
        len(conflicts),
    )

    for index, conflict in conflicts.iterrows():

        mask = (
            (
                unique_rows["session_date"]
                == conflict["session_date"]
            )
            & (
                unique_rows["CodiActivitat"]
                == conflict["CodiActivitat"]
            )
            & (
                unique_rows["start_time"]
                == conflict["start_time"]
            )
            & (
                unique_rows["Sala"]
                == conflict["Sala"]
            )
        )

        rows = (
            unique_rows[
                mask
            ]
            .copy()
        )

        print()
        print("=" * 100)

        print(
            f"CONFLICT {index + 1}"
        )

        print("-" * 100)

        print(
            "Date:",
            conflict["session_date"],
        )

        print(
            "Code:",
            conflict["CodiActivitat"],
        )

        print(
            "Start:",
            conflict["start_time"],
        )

        print(
            "Room:",
            conflict["Sala"],
        )

        print()

        columns = [
            "DataInscripcio",
            "CodiActivitat",
            "Activitat",
            "AforamentMax",
            "Inscrits",
            "PctOcupacio",
            "HoraInici",
            "HoraFi",
            "start_time",
            "end_time",
            "Sala",
        ]

        print(
            rows[
                columns
            ].to_string(
                index=False
            )
        )

        print()
        print(
            "END TIME DISTRIBUTION"
        )
        print("-" * 50)

        original_mask = (
            (
                valid["session_date"]
                == conflict["session_date"]
            )
            & (
                valid["CodiActivitat"]
                == conflict["CodiActivitat"]
            )
            & (
                valid["start_time"]
                == conflict["start_time"]
            )
            & (
                valid["Sala"]
                == conflict["Sala"]
            )
        )

        distribution = (
            valid[
                original_mask
            ]["end_time"]
            .value_counts(
                dropna=False
            )
        )

        print(
            distribution.to_string()
        )

    print()
    print("=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()