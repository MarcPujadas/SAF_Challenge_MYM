from __future__ import annotations

from app.database.database import get_connection


def get_recommendation_stats(
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    conditions = []
    params = []

    if space_id is not None:
        conditions.append(
            "r.space_id = ?"
        )
        params.append(space_id)

    if date_from is not None:
        conditions.append(
            "r.date >= ?"
        )
        params.append(date_from)

    if date_to is not None:
        conditions.append(
            "r.date <= ?"
        )
        params.append(date_to)

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE "
            + " AND ".join(conditions)
        )

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
                r.id,
                r.requested_score,
                r.recommended_score,
                a.action
            FROM recommendations r
            LEFT JOIN recommendation_actions a
                ON a.recommendation_id = r.id
            {where_clause}
            """,
            params,
        ).fetchall()

    total = len(rows)

    accepted = sum(
        row["action"] == "accepted"
        for row in rows
    )

    ignored = sum(
        row["action"] == "ignored"
        for row in rows
    )

    without_action = (
        total
        - accepted
        - ignored
    )

    decided = (
        accepted
        + ignored
    )

    decision_rate = (
        round(
            decided / total * 100,
            1,
        )
        if total > 0
        else 0.0
    )

    acceptance_rate = (
        round(
            accepted / decided * 100,
            1,
        )
        if decided > 0
        else 0.0
    )

    improvements = [
        (
            row["requested_score"]
            - row["recommended_score"]
        )
        for row in rows
        if (
            row["requested_score"]
            is not None
            and row["recommended_score"]
            is not None
        )
    ]

    average_score_improvement = (
        round(
            sum(improvements)
            / len(improvements),
            1,
        )
        if improvements
        else None
    )

    return {
        "total_recommendations": total,
        "accepted": accepted,
        "ignored": ignored,
        "without_action": without_action,
        "decision_rate": decision_rate,
        "acceptance_rate": acceptance_rate,
        "average_score_improvement": (
            average_score_improvement
        ),
    }