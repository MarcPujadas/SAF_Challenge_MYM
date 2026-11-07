from app.database.database import (
    get_connection,
    init_db,
)
from app.config.services import services_for_database


SERVICES = services_for_database()


def main():
    init_db()

    with get_connection() as connection:

        for service in SERVICES:

            space = connection.execute(
                """
                SELECT id
                FROM spaces
                WHERE id = ?
                """,
                (
                    service["space_id"],
                )
            ).fetchone()

            if space is None:
                print(
                    "AVÍS: no existeix l'espai "
                    f"{service['space_id']}. "
                    f"No s'importa {service['id']}."
                )

                continue

            connection.execute(
                """
                INSERT INTO services (
                    id,
                    name,
                    description,
                    space_id,
                    reservable
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id)
                DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    space_id = excluded.space_id,
                    reservable = excluded.reservable
                """,
                (
                    service["id"],
                    service["name"],
                    service["description"],
                    service["space_id"],
                    1,
                )
            )

            print(
                f"{service['id']:20} "
                f"-> {service['space_id']}"
            )


if __name__ == "__main__":
    main()