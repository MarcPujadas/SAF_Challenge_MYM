from fastapi.testclient import TestClient

from app import main
from app.database import database


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"


def make_client(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_recommendation_analytics.db",
    )

    return TestClient(main.app)


def seed_spaces():
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
                TENNIS_SPACE_ID,
                "Tennis 1",
                "tennis",
                4,
                1,
            ),
        )


def seed_recommendations():
    with database.get_connection() as connection:
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
                "rec_1",
                "demo-user",
                FITNESS_SPACE_ID,
                "2026-11-10",
                "18:30",
                "19:45",
                80,
                40,
            ),
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
                "rec_2",
                "demo-user",
                FITNESS_SPACE_ID,
                "2026-11-11",
                "18:30",
                "19:45",
                70,
                50,
            ),
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
                "rec_3",
                "demo-user",
                TENNIS_SPACE_ID,
                "2026-11-12",
                "17:15",
                None,
                60,
                None,
            ),
        )

        connection.execute(
            """
            INSERT INTO recommendation_actions (
                recommendation_id,
                action
            )
            VALUES (?, ?)
            """,
            (
                "rec_1",
                "accepted",
            ),
        )

        connection.execute(
            """
            INSERT INTO recommendation_actions (
                recommendation_id,
                action
            )
            VALUES (?, ?)
            """,
            (
                "rec_2",
                "ignored",
            ),
        )


def test_recommendation_stats_without_data(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        response = client.get(
            "/api/v1/admin/recommendations/stats"
        )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["total_recommendations"] == 0
    assert data["accepted"] == 0
    assert data["ignored"] == 0
    assert data["without_action"] == 0
    assert data["acceptance_rate"] == 0.0
    assert data["average_score_improvement"] is None


def test_recommendation_stats_calculate_totals(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_spaces()
        seed_recommendations()

        response = client.get(
            "/api/v1/admin/recommendations/stats"
        )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["total_recommendations"] == 3
    assert data["accepted"] == 1
    assert data["ignored"] == 1
    assert data["without_action"] == 1

    assert data["decision_rate"] == 66.7
    assert data["acceptance_rate"] == 50.0

    assert (
        data["average_score_improvement"]
        == 30.0
    )


def test_recommendation_stats_filter_by_space(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_spaces()
        seed_recommendations()

        response = client.get(
            "/api/v1/admin/recommendations/stats",
            params={
                "space_id": FITNESS_SPACE_ID,
            },
        )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["space_id"] == FITNESS_SPACE_ID
    assert data["total_recommendations"] == 2
    assert data["accepted"] == 1
    assert data["ignored"] == 1
    assert data["without_action"] == 0

    assert data["acceptance_rate"] == 50.0

    assert (
        data["average_score_improvement"]
        == 30.0
    )


def test_recommendation_stats_filter_by_dates(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_spaces()
        seed_recommendations()

        response = client.get(
            "/api/v1/admin/recommendations/stats",
            params={
                "from": "2026-11-11",
                "to": "2026-11-12",
            },
        )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["period"] == {
        "from": "2026-11-11",
        "to": "2026-11-12",
    }

    assert data["total_recommendations"] == 2
    assert data["accepted"] == 0
    assert data["ignored"] == 1
    assert data["without_action"] == 1
    assert data["acceptance_rate"] == 0.0

    assert (
        data["average_score_improvement"]
        == 20.0
    )


def test_recommendation_stats_validate_dates(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        invalid_date = client.get(
            "/api/v1/admin/recommendations/stats",
            params={
                "from": "not-a-date",
            },
        )

        invalid_range = client.get(
            "/api/v1/admin/recommendations/stats",
            params={
                "from": "2026-11-20",
                "to": "2026-11-10",
            },
        )

    assert invalid_date.status_code == 400
    assert (
        invalid_date.json()["error"]["code"]
        == "INVALID_DATE"
    )

    assert invalid_range.status_code == 400
    assert (
        invalid_range.json()["error"]["code"]
        == "INVALID_DATE_RANGE"
    )