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


def main():
    df = pd.read_excel(
        DATA_PATH,
        sheet_name="Reserves"
    )

    df["space_id"] = (
        df["Recurs"]
        .apply(detect_space_id)
    )

    mapped = df[
        df["space_id"].notna()
    ].copy()

    mapped["DuradaMin"] = pd.to_numeric(
        mapped["DuradaMin"],
        errors="coerce"
    )

    mapped = mapped[
        mapped["DuradaMin"].notna()
    ].copy()

    print("=" * 80)
    print("SAF RESERVATION SLOT ANALYSIS")
    print("=" * 80)

    print()
    print("Registres totals:", len(df))
    print("Registres mapejats:", len(mapped))

    space_ids = sorted(
        mapped["space_id"].unique()
    )

    for space_id in space_ids:

        space_data = mapped[
            mapped["space_id"]
            == space_id
        ]

        durations = (
            space_data["DuradaMin"]
            .value_counts()
            .sort_values(
                ascending=False
            )
        )

        print()
        print("=" * 80)
        print(space_id)
        print("-" * 80)

        print(
            "Reserves:",
            len(space_data)
        )

        print()
        print("Durades més habituals:")

        for duration, count in durations.head(8).items():

            percentage = (
                count
                / len(space_data)
                * 100
            )

            print(
                f"{int(duration):4} min"
                f"  -> {count:6} "
                f"({percentage:5.1f}%)"
            )

        starts = (
            space_data["HoraInici"]
            .astype(str)
            .str[:5]
            .value_counts()
            .head(10)
        )

        print()
        print("Hores d'inici més habituals:")

        for start, count in starts.items():
            print(
                f"{start:5} -> {count:6}"
            )

    print()
    print("=" * 80)
    print("SUMMARY BY SPACE TYPE")
    print("=" * 80)

    summary = (
        mapped
        .groupby(
            [
                "space_id",
                "DuradaMin"
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
    )

    most_common = (
        summary
        .sort_values(
            [
                "space_id",
                "count"
            ],
            ascending=[
                True,
                False
            ]
        )
        .groupby(
            "space_id"
        )
        .first()
        .reset_index()
    )

    print()

    for _, row in most_common.iterrows():

        print(
            f"{row['space_id']:45} "
            f"{int(row['DuradaMin']):4} min "
            f"({int(row['count'])} reserves)"
        )


if __name__ == "__main__":
    main()