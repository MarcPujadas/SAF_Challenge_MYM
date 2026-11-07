from contextlib import closing

from app.common import ApiError
from app.database.database import get_connection


UNSUPPORTED_SAFI_RECOMMENDATION_TYPES = {"court"}


def get_space(space_id: str):
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT id, name, type, capacity, reservable
            FROM spaces
            WHERE id = ?
            """,
            (space_id,),
        ).fetchone()

    if row is None:
        raise ApiError(
            "INVALID_SPACE",
            "The requested space does not exist.",
            404,
        )
    return row


def supports_safi_recommendations(space_id: str) -> bool:
    space = get_space(space_id)
    return space["type"] not in UNSUPPORTED_SAFI_RECOMMENDATION_TYPES


def list_spaces() -> list[dict]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, name, type, capacity, reservable
            FROM spaces
            ORDER BY name
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "capacity": row["capacity"],
            "reservable": bool(row["reservable"]),
        }
        for row in rows
    ]


def list_services() -> list[dict]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT
                services.id,
                services.name,
                services.description,
                services.space_id,
                CASE
                    WHEN services.reservable = 1
                        AND spaces.reservable = 1
                    THEN 1
                    ELSE 0
                END AS reservable
            FROM services
            LEFT JOIN spaces ON spaces.id = services.space_id
            ORDER BY services.name
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "space_id": row["space_id"],
            "reservable": bool(row["reservable"]),
        }
        for row in rows
    ]


def get_current_user() -> dict[str, str]:
    return {"id": "demo-user", "name": "Usuari Demo"}
