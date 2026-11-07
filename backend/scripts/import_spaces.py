from pathlib import Path
import re
import unicodedata

import pandas as pd

from app.database.database import (
    get_connection,
    init_db,
)


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)


def slugify(text):
    text = str(text).lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    )

    return text.strip("-")


def get_space_type(name):
    name = name.lower()

    if (
        "fitness" in name
        or "fitnes" in name
        or "cardio" in name
    ):
        return "fitness"

    if "piscina" in name:
        return "pool"

    if (
        "pàdel" in name
        or "padel" in name
        or "tennis" in name
        or "esquaix" in name
        or "futbol" in name
        or "bàsquet" in name
        or "basquet" in name
        or "voleibol" in name
        or "poliesportiu" in name
    ):
        return "court"

    if (
        "rocòdrom" in name
        or "rocodrom" in name
        or "cal·listènia" in name
        or "calistenia" in name
    ):
        return "outdoor"

    if "activitats dirigides" in name:
        return "activity_room"

    return "other"


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"No s'ha trobat el dataset: {DATA_PATH}"
        )

    init_db()

    df = pd.read_excel(
        DATA_PATH,
        sheet_name="Espais"
    )

    required_columns = {
        "Espai",
        "Subespai",
        "Aforament",
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Falten columnes al full Espais: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    duplicates = df[
        df.duplicated()
    ]

    if not duplicates.empty:
        print("DUPLICATS DETECTATS:")
        print(
            duplicates.to_string(
                index=False
            )
        )
        print()

    df = df.drop_duplicates()

    imported = 0

    with get_connection() as connection:

        for _, row in df.iterrows():

            espai = str(
                row["Espai"]
            ).strip()

            if pd.notna(
                row["Subespai"]
            ):
                subespai = str(
                    row["Subespai"]
                ).strip()
            else:
                subespai = None

            capacity = int(
                row["Aforament"]
            )

            if subespai:
                space_id = slugify(
                    f"{espai}-{subespai}"
                )

                name = (
                    f"{espai} - {subespai}"
                )

            else:
                space_id = slugify(
                    espai
                )

                name = espai

            space_type = get_space_type(
                espai
            )

            connection.execute(
                """
                INSERT INTO spaces (
                    id,
                    name,
                    type,
                    capacity,
                    reservable
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id)
                DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    capacity = excluded.capacity,
                    reservable = excluded.reservable
                """,
                (
                    space_id,
                    name,
                    space_type,
                    capacity,
                    1
                )
            )

            imported += 1

            print(
                f"{space_id:45} "
                f"{capacity:3} persones   "
                f"{space_type}"
            )

    print()
    print(
        f"Importació completada: "
        f"{imported} espais."
    )


if __name__ == "__main__":
    main()