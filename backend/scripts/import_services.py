from app.database.database import (
    get_connection,
    init_db,
)


SERVICES = [
    {
        "id": "fitness",
        "name": "Fitness",
        "description": "Sala de fitness i cardio",
        "space_id": "sala-fitnes-sala-cardio",
    },
    {
        "id": "pool-25m",
        "name": "Piscina 25 m",
        "description": "Piscina de 25 metres",
        "space_id": "piscina-25-metres-carrer-1",
    },
    {
        "id": "pool-16m",
        "name": "Piscina 16 m",
        "description": "Piscina de 16 metres",
        "space_id": "piscina-de-16-metres",
    },
    {
        "id": "padel",
        "name": "Pàdel",
        "description": "Pistes de pàdel",
        "space_id": "pistes-de-padel-pista-1",
    },
    {
        "id": "tennis",
        "name": "Tennis",
        "description": "Pistes de tennis",
        "space_id": "tennis-tennis-1",
    },
    {
        "id": "squash",
        "name": "Esquaix",
        "description": "Pistes d'esquaix",
        "space_id": "esquaix-esquaix-2",
    },
    {
        "id": "football",
        "name": "Futbol",
        "description": "Camps de futbol",
        "space_id": "futbol-7-camp-1",
    },
    {
        "id": "guided-activities",
        "name": "Activitats dirigides",
        "description": "Sales d'activitats dirigides",
        "space_id": "sales-activitats-dirigides-sala-1",
    },
]


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