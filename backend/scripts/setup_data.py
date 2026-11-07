from __future__ import annotations

import argparse
from pathlib import Path

from app.database.database import (
    DB_PATH,
    get_connection,
)

from scripts.import_spaces import (
    main as import_spaces,
)

from scripts.import_services import (
    main as import_services,
)

from scripts.process_historical_data import (
    main as process_historical_data,
)

from scripts.validate_data_integrity import (
    main as validate_data_integrity,
)


BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "saf-espais-2026-equips.xlsx"
)

HISTORICAL_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "historical_occupancy.csv"
)


def reset_database():
    if not DB_PATH.exists():
        print(
            "No existeix cap base SQLite anterior. "
            "No cal eliminar-la."
        )

        return

    try:
        DB_PATH.unlink()

    except PermissionError as exc:
        raise RuntimeError(
            "No es pot eliminar safhack.db perquè "
            "un altre procés l'està utilitzant. "
            "Atura Uvicorn/Python i torna-ho a provar."
        ) from exc

    print(
        "Base SQLite anterior eliminada."
    )


def get_database_summary():
    with get_connection() as connection:

        spaces = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM spaces
            """
        ).fetchone()["total"]

        services = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM services
            """
        ).fetchone()["total"]

        users = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            """
        ).fetchone()["total"]

        reservations = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM reservations
            """
        ).fetchone()["total"]

    return {
        "spaces": spaces,
        "services": services,
        "users": users,
        "reservations": reservations,
    }


def validate_setup():
    summary = get_database_summary()

    errors = []

    if summary["spaces"] != 40:
        errors.append(
            f"Expected 40 spaces, found "
            f"{summary['spaces']}."
        )

    if summary["services"] != 8:
        errors.append(
            f"Expected 8 services, found "
            f"{summary['services']}."
        )

    if summary["users"] < 1:
        errors.append(
            "No users found."
        )

    if not HISTORICAL_PATH.exists():
        errors.append(
            "historical_occupancy.csv was not created."
        )

    if errors:
        print()
        print("=" * 70)
        print("DATA SETUP FAILED")
        print("=" * 70)

        for error in errors:
            print(
                "-",
                error
            )

        return False

    print()
    print("=" * 70)
    print("DATA SETUP SUMMARY")
    print("=" * 70)

    print(
        "Spaces:",
        summary["spaces"]
    )

    print(
        "Services:",
        summary["services"]
    )

    print(
        "Users:",
        summary["users"]
    )

    print(
        "Reservations:",
        summary["reservations"]
    )

    print(
        "Historical file:",
        HISTORICAL_PATH
    )

    return True


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Prepare local SAF Hack data."
        )
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Delete the local SQLite database "
            "before importing data."
        ),
    )

    args = parser.parse_args()

    print("=" * 70)
    print("SAF HACK DATA SETUP")
    print("=" * 70)

    print()
    print(
        "Dataset:",
        DATASET_PATH
    )

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "No s'ha trobat el dataset privat a:\n"
            f"{DATASET_PATH}"
        )

    if args.reset:
        print()
        print("RESET DATABASE")
        print("-" * 70)

        reset_database()

    print()
    print("1. IMPORT SPACES")
    print("-" * 70)

    import_spaces()

    print()
    print("2. IMPORT SERVICES")
    print("-" * 70)

    import_services()

    print()
    print("3. PROCESS HISTORICAL DATA")
    print("-" * 70)

    process_historical_data()

    print()
    print("4. VALIDATE DATA INTEGRITY")
    print("-" * 70)

    validate_data_integrity()

    setup_ok = validate_setup()

    if not setup_ok:
        raise RuntimeError(
            "Data setup finished with errors."
        )

    print()
    print("=" * 70)
    print("DATA SETUP OK")
    print("=" * 70)


if __name__ == "__main__":
    main()