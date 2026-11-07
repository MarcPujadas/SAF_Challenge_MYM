from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.routers import recommendations


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"


def fake_recommend(
    space_id,
    date,
    preferred_start,
    preferred_end=None,
):
    return {
        "requested_slot": {
            "start": preferred_start,
            "occupancy_score": 80,
            "occupancy_level": "high",
        },
        "recommended_slot": {
            "start": "19:45",
            "occupancy_score": 40,
            "occupancy_level": "medium",
        },
        "message": (
            "Les 19:45 acostumen a tenir "
            "menys ocupació."
        ),
        "confidence": "high",
        "basis": {
            "space_id": space_id,
            "weekday": "Tuesday",
            "historical_period": (
                "2026-04-01 to 2026-10-31"
            ),
        },
    }


def make_client(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_tracking.db",
    )

    monkeypatch.setattr(
        recommendations,
        "recommend",
        fake_recommend,
    )

    return TestClient(main.app)


def seed_space():
    with database.get_connection() as connection:
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
            """,
            (
                FITNESS_SPACE_ID,
                "Sala Fitness",
                "fitness",
                120,
                1,
            ),
        )


def test_recommendation_is_persisted(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_space()

        response = client.post(
            "/api/v1/recommendations",
            json={
                "space_id": FITNESS_SPACE_ID,
                "date": "2026-11-10",
                "preferred_start": "18:30",
                "preferred_end": "19:45",
            },
        )

        assert response.status_code == 200

        body = response.json()

        recommendation_id = (
            body["data"]["recommendation_id"]
        )

        assert recommendation_id.startswith(
            "rec_"
        )

        with database.get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM recommendations
                WHERE id = ?
                """,
                (recommendation_id,),
            ).fetchone()

        assert row is not None
        assert row["user_id"] == "demo-user"
        assert row["space_id"] == FITNESS_SPACE_ID
        assert row["requested_start"] == "18:30"
        assert row["recommended_start"] == "19:45"
        assert row["requested_score"] == 80
        assert row["recommended_score"] == 40


def test_recommendation_action_is_saved(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_space()

        recommendation = client.post(
            "/api/v1/recommendations",
            json={
                "space_id": FITNESS_SPACE_ID,
                "date": "2026-11-10",
                "preferred_start": "18:30",
                "preferred_end": "19:45",
            },
        )

        recommendation_id = (
            recommendation.json()[
                "data"
            ]["recommendation_id"]
        )

        action = client.post(
            (
                "/api/v1/recommendations/"
                f"{recommendation_id}/action"
            ),
            json={
                "action": "accepted",
            },
        )

        assert action.status_code == 200

        assert (
            action.json()["data"]["action"]
            == "accepted"
        )

        with database.get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM recommendation_actions
                WHERE recommendation_id = ?
                """,
                (recommendation_id,),
            ).fetchone()

        assert row is not None
        assert row["action"] == "accepted"


def test_recommendation_action_can_be_updated(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_space()

        recommendation = client.post(
            "/api/v1/recommendations",
            json={
                "space_id": FITNESS_SPACE_ID,
                "date": "2026-11-10",
                "preferred_start": "18:30",
                "preferred_end": "19:45",
            },
        )

        recommendation_id = (
            recommendation.json()[
                "data"
            ]["recommendation_id"]
        )

        client.post(
            (
                "/api/v1/recommendations/"
                f"{recommendation_id}/action"
            ),
            json={
                "action": "accepted",
            },
        )

        client.post(
            (
                "/api/v1/recommendations/"
                f"{recommendation_id}/action"
            ),
            json={
                "action": "ignored",
            },
        )

        with database.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM recommendation_actions
                WHERE recommendation_id = ?
                """,
                (recommendation_id,),
            ).fetchall()

        assert len(rows) == 1
        assert rows[0]["action"] == "ignored"


def test_invalid_recommendation_action(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_space()

        recommendation = client.post(
            "/api/v1/recommendations",
            json={
                "space_id": FITNESS_SPACE_ID,
                "date": "2026-11-10",
                "preferred_start": "18:30",
                "preferred_end": "19:45",
            },
        )

        recommendation_id = (
            recommendation.json()[
                "data"
            ]["recommendation_id"]
        )

        response = client.post(
            (
                "/api/v1/recommendations/"
                f"{recommendation_id}/action"
            ),
            json={
                "action": "maybe",
            },
        )

        assert response.status_code == 400

        assert (
            response.json()["error"]["code"]
            == "INVALID_RECOMMENDATION_ACTION"
        )


def test_unknown_recommendation_returns_404(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        response = client.post(
            "/api/v1/recommendations/rec_unknown/action",
            json={
                "action": "accepted",
            },
        )

        assert response.status_code == 404

        assert (
            response.json()["error"]["code"]
            == "RECOMMENDATION_NOT_FOUND"
        )