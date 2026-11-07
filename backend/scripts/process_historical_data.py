from pathlib import Path

import pandas as pd

from app.database.database import (
    get_connection,
)

from scripts.build_resource_mapping import (
    detect_space_id,
)


BASE_DIR = Path(__file__).resolve().parents[1]

FILE_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_occupancy.csv"
)


def get_valid_space_ids():
    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT id
            FROM spaces
            """
        ).fetchall()

    return {
        row["id"]
        for row in rows
    }


def main():
    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"No s'ha trobat el dataset: "
            f"{FILE_PATH}"
        )

    valid_space_ids = (
        get_valid_space_ids()
    )

    if not valid_space_ids:
        raise RuntimeError(
            "No hi ha espais a SQLite. "
            "Executa primer "
            "'python -m scripts.import_spaces'."
        )

    df = pd.read_excel(
        FILE_PATH,
        sheet_name="Reserves per franja"
    )

    print(
        "Registres originals:",
        len(df)
    )

    df["space_id"] = (
        df["Recurs"]
        .apply(detect_space_id)
    )

    mapped = df[
        df["space_id"].notna()
    ].copy()

    print(
        "Registres amb recurs mapejat:",
        len(mapped)
    )

    orphan_space_ids = sorted(
        set(
            mapped["space_id"]
            .unique()
        )
        - valid_space_ids
    )

    if orphan_space_ids:
        print()
        print(
            "RECURSOS MAPEJATS A ESPAIS "
            "QUE NO EXISTEIXEN A SQLITE:"
        )

        for space_id in orphan_space_ids:

            count = len(
                mapped[
                    mapped["space_id"]
                    == space_id
                ]
            )

            print(
                f"{space_id:45} "
                f"{count} registres descartats"
            )

    mapped = mapped[
        mapped["space_id"].isin(
            valid_space_ids
        )
    ].copy()

    print()
    print(
        "Registres vàlids:",
        len(mapped)
    )

    print(
        "Registres descartats totals:",
        len(df) - len(mapped)
    )

    mapped["DataUs"] = pd.to_datetime(
        mapped["DataUs"]
    )

    mapped["date"] = (
        mapped["DataUs"]
        .dt.strftime("%Y-%m-%d")
    )

    mapped["weekday"] = (
        mapped["DataUs"]
        .dt.day_of_week
    )

    mapped["start_time"] = (
        mapped["HoraInici"]
        .astype(str)
        .str[:5]
    )

    result = mapped[
        [
            "space_id",
            "date",
            "weekday",
            "start_time",
            "Reserves"
        ]
    ].rename(
        columns={
            "Reserves": "reservations"
        }
    )

    result = (
        result
        .groupby(
            [
                "space_id",
                "date",
                "weekday",
                "start_time"
            ],
            as_index=False
        )
        ["reservations"]
        .sum()
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8"
    )

    print()
    print(
        "Fitxer creat:"
    )

    print(
        OUTPUT_PATH
    )

    print()
    print(
        "Files finals:",
        len(result)
    )


if __name__ == "__main__":
    main()