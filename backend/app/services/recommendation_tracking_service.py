from uuid import uuid4

from app.common import ApiError
from app.database.database import get_connection


VALID_ACTIONS = {
    "accepted",
    "ignored",
}


def save_recommendation(
    user_id: str,
    space_id: str,
    date: str,
    requested_start: str,
    recommended_start: str | None,
    requested_score: int | None,
    recommended_score: int | None,
) -> str:
    recommendation_id = (
        f"rec_{uuid4().hex[:12]}"
    )

    with get_connection() as connection:

        user = connection.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user is None:
            raise ApiError(
                "INVALID_USER",
                "The requested user does not exist.",
                404,
            )

        space = connection.execute(
            """
            SELECT id
            FROM spaces
            WHERE id = ?
            """,
            (space_id,),
        ).fetchone()

        if space is None:
            raise ApiError(
                "INVALID_SPACE",
                "The requested space does not exist.",
                404,
            )

        connection.execute(
            """
            INSERT INTO recommendations (
                id,
                user_id,
                space_id,
                date,
                requested_start,
                recommended_start,
                requested_score,
                recommended_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation_id,
                user_id,
                space_id,
                date,
                requested_start,
                recommended_start,
                requested_score,
                recommended_score,
            ),
        )

    return recommendation_id


def save_recommendation_action(
    recommendation_id: str,
    action: str,
) -> None:
    if action not in VALID_ACTIONS:
        raise ApiError(
            "INVALID_RECOMMENDATION_ACTION",
            (
                "Recommendation action must be "
                "'accepted' or 'ignored'."
            ),
            400,
        )

    with get_connection() as connection:

        recommendation = connection.execute(
            """
            SELECT id
            FROM recommendations
            WHERE id = ?
            """,
            (recommendation_id,),
        ).fetchone()

        if recommendation is None:
            raise ApiError(
                "RECOMMENDATION_NOT_FOUND",
                "The recommendation does not exist.",
                404,
            )

        connection.execute(
            """
            INSERT INTO recommendation_actions (
                recommendation_id,
                action
            )
            VALUES (?, ?)
            ON CONFLICT(recommendation_id)
            DO UPDATE SET
                action = excluded.action,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                recommendation_id,
                action,
            ),
        )