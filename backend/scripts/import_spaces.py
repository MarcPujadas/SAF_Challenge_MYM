import hashlib
from pathlib import Path
import re
import unicodedata

import pandas as pd

from app.database.database import (
    get_connection,
    init_db,
)
from app.database.service_spaces import seed_service_spaces
from app.database.historical_usage import register_data_source


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "local"
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


def build_space_id(
    espai,
    subespai
):
    espai_id = slugify(
        espai
    )

    if not subespai:
        return espai_id

    subespai_id = slugify(
        subespai
    )

    # Al full Espais apareix "camps 3",
    # mentre que a les reserves històriques
    # el recurs correspon clarament a "camp 3".
    #
    # Normalitzem només l'identificador.
    # No modifiquem el nom original del dataset.
    if (
        espai_id == "futbol-7"
        and subespai_id == "camps-3"
    ):
        subespai_id = "camp-3"

    return (
        f"{espai_id}-{subespai_id}"
    )


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"No s'ha trobat el dataset: "
            f"{DATA_PATH}"
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

    checksum = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    imported = 0
    seen_rows = {}
    duplicate_rows = 0

    with get_connection() as connection:

        for row_number, (_, row) in enumerate(df.iterrows(), start=2):

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

            space_id = build_space_id(
                espai,
                subespai
            )

            if subespai:
                name = (
                    f"{espai} - {subespai}"
                )
            else:
                name = espai

            space_type = get_space_type(
                espai
            )

            definition = (name, space_type, capacity)
            if space_id in seen_rows:
                if seen_rows[space_id] != definition:
                    raise ValueError(
                        "Conflicting source rows resolve to the same "
                        f"space_id {space_id!r}; row {row_number} needs "
                        "manual review."
                    )
                duplicate_rows += 1
                print(
                    f"Fila duplicada {row_number}: {space_id} "
                    "(se conserva en el dataset original; una entidad SQLite)"
                )
                continue
            seen_rows[space_id] = definition

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

        seed_service_spaces(connection)
        register_data_source(
            connection,
            source_id="saf_spaces_2026",
            source_type="saf_catalog",
            label="SAF spaces 2026",
            period_from=None,
            period_to=None,
            checksum=checksum,
        )

    print()

    print(
        f"Importació completada: "
        f"{imported} espais únics, {duplicate_rows} files duplicades "
        "identificades."
    )


if __name__ == "__main__":
    main()