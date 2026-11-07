from pathlib import Path

import pandas as pd

from scripts.build_resource_mapping import (
    detect_space_id,
)


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)


WEEKDAYS = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


def main():
    df = pd.read_excel(
        DATA_PATH,
        sheet_name="Reserves"
    )

    df["space_id"] = (
        df["Recurs"]
        .apply(detect_space_id)
    )

    df = df[
        df["space_id"].notna()
    ].copy()

    df["DataUs"] = pd.to_datetime(
        df["DataUs"]
    )

    df["weekday"] = (
        df["DataUs"]
        .dt.day_of_week
    )

    df["DuradaMin"] = pd.to_numeric(
        df["DuradaMin"],
        errors="coerce"
    )

    df["start_time"] = (
        df["HoraInici"]
        .astype(str)
        .str[:5]
    )

    df = df[
        df["DuradaMin"].notna()
    ].copy()

    print("=" * 90)
    print("SAF SLOT PATTERN ANALYSIS")
    print("=" * 90)

    for space_id in sorted(
        df["space_id"].unique()
    ):
        space_data = df[
            df["space_id"] == space_id
        ].copy()

        duration_counts = (
            space_data["DuradaMin"]
            .value_counts()
        )

        if duration_counts.empty:
            continue

        standard_duration = int(
            duration_counts.index[0]
        )

        standard_data = space_data[
            space_data["DuradaMin"]
            == standard_duration
        ].copy()

        print()
        print("=" * 90)
        print(space_id)
        print(
            f"Standard duration: "
            f"{standard_duration} min"
        )
        print("=" * 90)

        for weekday in range(7):
            day_data = standard_data[
                standard_data["weekday"]
                == weekday
            ]

            if day_data.empty:
                continue

            starts = (
                day_data["start_time"]
                .value_counts()
                .sort_index()
            )

            print()
            print(
                WEEKDAYS[weekday],
                f"({len(day_data)} reservations)"
            )

            print("-" * 50)

            for start, count in starts.items():
                percentage = (
                    count
                    / len(day_data)
                    * 100
                )

                # Ignore extremely isolated anomalies.
                if count >= 3:
                    print(
                        f"{start} "
                        f"-> {count:5} "
                        f"({percentage:5.1f}%)"
                    )


if __name__ == "__main__":
    main()