import json
from pathlib import Path

import pandas as pd

from app.database.database import (
    get_connection,
    init_db,
)
from app.services.catalog_service import (
    get_historical_import_quality_report,
)


BASE_DIR = Path(__file__).resolve().parents[1]

HISTORICAL_PATH = (
    BASE_DIR
    / "data"
    / "local"
    / "historical_occupancy.csv"
)


def main():
    init_db()
    print("=" * 70)
    print("SAF DATA INTEGRITY CHECK")
    print("=" * 70)

    with get_connection() as connection:

        spaces = connection.execute(
            """
            SELECT id, name, type
            FROM spaces
            ORDER BY id
            """
        ).fetchall()

        services = connection.execute(
            """
            SELECT id, name, space_id
            FROM services
            ORDER BY id
            """
        ).fetchall()
        virtual_resources = connection.execute(
            """
            SELECT space_id
            FROM service_spaces
            WHERE is_active = 1 AND is_virtual = 1
            """
        ).fetchall()

    space_ids = {
        row["id"]
        for row in spaces
    } | {row["space_id"] for row in virtual_resources}

    print()
    print("SQLITE")
    print("-" * 70)

    print(
        "Espais:",
        len(spaces)
    )

    print(
        "Serveis:",
        len(services)
    )

    print()
    print("SERVEIS AMB ESPAI INEXISTENT")
    print("-" * 70)

    invalid_services = [
        service
        for service in services
        if service["space_id"] not in space_ids
    ]

    if invalid_services:
        for service in invalid_services:
            print(
                service["id"],
                "->",
                service["space_id"]
            )
    else:
        print("Cap.")

    if not HISTORICAL_PATH.exists():
        print()
        print(
            "AVÍS: no existeix "
            "historical_occupancy.csv"
        )
        historical = pd.DataFrame(columns=["space_id"])
    else:
        historical = pd.read_csv(HISTORICAL_PATH)

    historical_space_ids = set(
        historical["space_id"].dropna().unique()
    )

    print()
    print("HISTÒRIC PROCESSAT")
    print("-" * 70)

    print(
        "Files:",
        len(historical)
    )

    if "reservations" in historical.columns:
        print(
            "Volum legacy de reserves (no s'afegeix al nou import):",
            pd.to_numeric(
                historical["reservations"],
                errors="coerce",
            ).sum(),
        )

    print(
        "Espais diferents:",
        len(historical_space_ids)
    )

    orphan_historical = sorted(
        historical_space_ids
        - space_ids
    )

    print()
    print(
        "SPACE_ID DE L'HISTÒRIC "
        "QUE NO EXISTEIXEN A SQLITE"
    )
    print("-" * 70)

    if orphan_historical:
        for space_id in orphan_historical:

            count = len(
                historical[
                    historical["space_id"]
                    == space_id
                ]
            )

            print(
                f"{space_id:45} "
                f"{count} registres"
            )

    else:
        print("Cap.")

    without_history = sorted(
        space_ids
        - historical_space_ids
    )

    print()
    print(
        "ESPAIS SQLITE SENSE "
        "DADES HISTÒRIQUES"
    )
    print("-" * 70)

    if without_history:
        for space_id in without_history:
            print(space_id)

    else:
        print("Cap.")

    print()
    print("RESUM")
    print("-" * 70)

    print(
        "Espais SQLite:",
        len(space_ids)
    )

    print(
        "Espais històric:",
        len(historical_space_ids)
    )

    print(
        "Històric sense espai SQLite:",
        len(orphan_historical)
    )

    print(
        "Espais sense històric:",
        len(without_history)
    )

    if (
        not invalid_services
        and not orphan_historical
    ):
        print()
        print(
            "OK: no s'han detectat "
            "inconsistències crítiques."
        )

    else:
        print()
        print(
            "ATENCIÓ: hi ha inconsistències "
            "que s'han de revisar."
        )

    print()
    print("HISTORICAL USAGE QUALITY")
    print("-" * 70)
    quality_report = get_historical_import_quality_report()
    print(
        json.dumps(
            quality_report,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()