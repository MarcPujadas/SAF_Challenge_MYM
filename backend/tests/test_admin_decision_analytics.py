import pandas as pd
from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.services import historical_service


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"


def historical_records():
    return pd.DataFrame(
        [
            (FITNESS_SPACE_ID, "2026-04-06", 0, "08:30", 10),
            (FITNESS_SPACE_ID, "2026-04-06", 0, "18:30", 90),
            (FITNESS_SPACE_ID, "2026-04-13", 0, "08:30", 20),
            (FITNESS_SPACE_ID, "2026-04-13", 0, "18:30", 100),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "08:30", 20),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "18:30", 100),
            (FITNESS_SPACE_ID, "2026-04-14", 1, "08:30", 30),
            (FITNESS_SPACE_ID, "2026-04-14", 1, "18:30", 80),
            (TENNIS_SPACE_ID, "2026-04-06", 0, "08:30", 1),
            (TENNIS_SPACE_ID, "2026-04-06", 0, "18:30", 4),
            (TENNIS_SPACE_ID, "2026-04-07", 1, "08:30", 3),
            (TENNIS_SPACE_ID, "2026-04-07", 1, "18:30", 2),
        ],
        columns=[
            "space_id",
            "date",
            "weekday",
            "start_time",
            "reservations",
        ],
    )


def make_client(tmp_path, monkeypatch, history=historical_records):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "admin_analytics.db")
    monkeypatch.setattr(historical_service, "load_historical_data", history)
    return TestClient(main.app)


def seed_space(space_id=FITNESS_SPACE_ID):
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO spaces (id, name, type, capacity, reservable)
            VALUES (?, ?, 'fitness', 120, 1)
            """,
            (space_id, "Test space"),
        )


def seed_reservation(reservation_id, day, start, status, space_id=FITNESS_SPACE_ID):
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reservations (
                id, user_id, space_id, date, start, end, status
            )
            VALUES (?, 'demo-user', ?, ?, ?, '19:45', ?)
            """,
            (reservation_id, space_id, day, start, status),
        )


def seed_recommendation(
    recommendation_id,
    action,
    requested_score,
    recommended_score,
    requested_start="18:30",
    recommended_start="19:45",
    day="2026-04-06",
    space_id=FITNESS_SPACE_ID,
):
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO recommendations (
                id, user_id, space_id, date, requested_start,
                recommended_start, requested_score, recommended_score
            )
            VALUES (?, 'demo-user', ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation_id,
                space_id,
                day,
                requested_start,
                recommended_start,
                requested_score,
                recommended_score,
            ),
        )
        if action is not None:
            connection.execute(
                """
                INSERT INTO recommendation_actions (recommendation_id, action)
                VALUES (?, ?)
                """,
                (recommendation_id, action),
            )


def test_occupancy_by_weekday_uses_historical_scores_and_filters(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/admin/analytics/occupancy-by-weekday",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-06",
                "to": "2026-04-13",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    data = body["data"]
    assert data["period"] == {
        "from": "2026-04-06",
        "to": "2026-04-13",
    }
    assert len(data["spaces"]) == 1
    weekdays = data["spaces"][0]["weekdays"]
    assert [item["day_of_week"] for item in weekdays] == ["Monday", "Tuesday"]
    assert weekdays[0]["samples"] == 4
    assert weekdays[1]["samples"] == 2
    assert 0 <= weekdays[0]["average_occupancy_score"] <= 100
    assert weekdays[0]["occupancy_level"] in {
        "low",
        "medium",
        "high",
        "very_high",
    }


def test_occupancy_slot_rankings_are_per_space_and_omit_missing_slots(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/admin/analytics/occupancy-slots",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-06",
                "to": "2026-04-13",
            },
        )

    assert response.status_code == 200
    spaces = response.json()["data"]["spaces"]
    assert [item["space_id"] for item in spaces] == [FITNESS_SPACE_ID]
    space = spaces[0]
    assert 0 < len(space["most_saturated"]) <= 5
    assert 0 < len(space["quietest"]) <= 5
    assert all(
        slot["hour"] in {"08:30", "18:30"}
        for slot in space["most_saturated"] + space["quietest"]
    )
    assert space["most_saturated"][0]["occupancy_score"] == 100
    assert space["most_saturated"][0]["occupancy_level"] == "very_high"
    assert all(
        item["occupancy_score"] is not None
        for item in space["most_saturated"] + space["quietest"]
    )


def test_occupancy_filters_and_empty_history_return_valid_empty_arrays(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        filtered = client.get(
            "/api/v1/admin/analytics/occupancy-by-weekday",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-04-07",
                "to": "2026-04-07",
            },
        )
        empty = client.get(
            "/api/v1/admin/analytics/occupancy-slots",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-05-01",
                "to": "2026-05-02",
            },
        )

    assert filtered.status_code == 200
    assert [row["space_id"] for row in filtered.json()["data"]["spaces"]] == [
        TENNIS_SPACE_ID
    ]
    assert filtered.json()["data"]["spaces"][0]["weekdays"][0][
        "day_of_week"
    ] == "Tuesday"
    assert empty.status_code == 200
    assert empty.json()["data"]["spaces"] == []


def test_utilization_is_explicitly_unknown_without_historical_capacity(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/admin/analytics/utilization",
            params={"space_id": FITNESS_SPACE_ID},
        )

    assert response.status_code == 200
    assert response.json()["data"]["spaces"] == [
        {
            "space_id": FITNESS_SPACE_ID,
            "utilization_percentage": None,
            "status": "insufficient_data",
            "reason": "historical_capacity_unavailable",
            "samples": 8,
        }
    ]


def test_occupancy_trend_weekly_monthly_and_filtered(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        weekly = client.get(
            "/api/v1/admin/analytics/occupancy-trend",
            params={
                "group_by": "week",
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-06",
                "to": "2026-04-13",
            },
        )
        monthly = client.get(
            "/api/v1/admin/analytics/occupancy-trend",
            params={
                "group_by": "month",
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-01",
                "to": "2026-04-30",
            },
        )

    assert weekly.status_code == monthly.status_code == 200
    weekly_data = weekly.json()["data"]
    assert weekly_data["group_by"] == "week"
    assert [row["period"] for row in weekly_data["series"]] == [
        "2026-04-06",
        "2026-04-13",
    ]
    assert [row["samples"] for row in weekly_data["series"]] == [4, 2]
    monthly_data = monthly.json()["data"]
    assert monthly_data["group_by"] == "month"
    assert [row["period"] for row in monthly_data["series"]] == ["2026-04"]
    assert monthly_data["series"][0]["samples"] == 8


def test_occupancy_trend_empty_invalid_grouping_and_date_filters(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        empty = client.get(
            "/api/v1/admin/analytics/occupancy-trend",
            params={"from": "2026-05-01", "to": "2026-05-31"},
        )
        invalid_group = client.get(
            "/api/v1/admin/analytics/occupancy-trend",
            params={"group_by": "day"},
        )
        invalid_date = client.get(
            "/api/v1/admin/analytics/occupancy-trend",
            params={"from": "2026-04-31"},
        )
        invalid_range = client.get(
            "/api/v1/admin/analytics/occupancy-trend",
            params={"from": "2026-04-13", "to": "2026-04-06"},
        )

    assert empty.status_code == 200
    assert empty.json()["data"]["series"] == []
    assert invalid_group.status_code == 400
    assert invalid_group.json()["error"]["code"] == "INVALID_GROUP_BY"
    assert invalid_date.status_code == 400
    assert invalid_date.json()["error"]["code"] == "INVALID_DATE"
    assert invalid_range.status_code == 400
    assert invalid_range.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_cancellation_rate_counts_cancelled_rows_and_cancelled_slots(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_space()
        seed_space(TENNIS_SPACE_ID)
        seed_reservation("res-confirmed-1", "2026-04-06", "18:30", "confirmed")
        seed_reservation("res-cancelled-1", "2026-04-06", "18:30", "cancelled")
        seed_reservation("res-cancelled-2", "2026-04-13", "18:30", "cancelled")
        seed_reservation(
            "res-tennis",
            "2026-04-06",
            "08:30",
            "confirmed",
            TENNIS_SPACE_ID,
        )
        response = client.get(
            "/api/v1/admin/analytics/cancellations",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-06",
                "to": "2026-04-13",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["spaces"] == [
        {
            "space_id": FITNESS_SPACE_ID,
            "total_reservations": 3,
            "confirmed_reservations": 1,
            "cancelled_reservations": 2,
            "cancellation_rate": 66.7,
            "most_cancelled_slots": [
                {
                    "day_of_week": "Monday",
                    "hour": "18:30",
                    "cancelled_reservations": 2,
                }
            ],
        }
    ]


def test_cancellation_empty_and_date_validation(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        no_rows = client.get(
            "/api/v1/admin/analytics/cancellations",
            params={"space_id": FITNESS_SPACE_ID},
        )
        invalid_date = client.get(
            "/api/v1/admin/analytics/cancellations",
            params={"from": "bad-date"},
        )
        invalid_range = client.get(
            "/api/v1/admin/analytics/cancellations",
            params={"from": "2026-04-13", "to": "2026-04-06"},
        )

    assert no_rows.status_code == 200
    assert no_rows.json()["data"]["spaces"] == [
        {
            "space_id": FITNESS_SPACE_ID,
            "total_reservations": 0,
            "confirmed_reservations": 0,
            "cancelled_reservations": 0,
            "cancellation_rate": None,
            "most_cancelled_slots": [],
        }
    ]
    assert invalid_date.json()["error"]["code"] == "INVALID_DATE"
    assert invalid_range.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_safi_impact_uses_actions_and_only_accepted_valid_reductions(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_space()
        seed_space(TENNIS_SPACE_ID)
        seed_recommendation("rec-accepted-high", "accepted", 80, 40)
        seed_recommendation(
            "rec-accepted-medium",
            "accepted",
            60,
            30,
            requested_start="08:30",
            recommended_start="09:45",
        )
        seed_recommendation("rec-ignored", "ignored", 95, 10)
        seed_recommendation("rec-no-action", None, 90, 20)
        seed_recommendation("rec-no-score", "accepted", 90, None)
        seed_recommendation(
            "rec-tennis",
            "accepted",
            90,
            20,
            space_id=TENNIS_SPACE_ID,
        )
        response = client.get(
            "/api/v1/admin/analytics/safi-impact",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-01",
                "to": "2026-04-30",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["spaces"] == [
        {
            "space_id": FITNESS_SPACE_ID,
            "recommendations_generated": 5,
            "accepted": 3,
            "ignored": 1,
            "without_action": 1,
            "decision_rate": 80.0,
            "acceptance_rate": 75.0,
            "accepted_high_to_lower_recommendations": 1,
            "accepted_recommendations_with_score_reduction": 2,
            "average_saturation_reduction": 35.0,
        }
    ]


def test_safi_impact_without_actions_or_valid_scores_has_null_rates(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_space()
        seed_recommendation("rec-no-action-only", None, 80, 30)
        seed_recommendation("rec-invalid-score", "accepted", 120, 20)
        response = client.get(
            "/api/v1/admin/analytics/safi-impact",
            params={"space_id": FITNESS_SPACE_ID},
        )

    assert response.status_code == 200
    assert response.json()["data"]["spaces"] == [
        {
            "space_id": FITNESS_SPACE_ID,
            "recommendations_generated": 2,
            "accepted": 1,
            "ignored": 0,
            "without_action": 1,
            "decision_rate": 50.0,
            "acceptance_rate": 100.0,
            "accepted_high_to_lower_recommendations": 0,
            "accepted_recommendations_with_score_reduction": 0,
            "average_saturation_reduction": None,
        }
    ]


def test_analytics_routes_use_api_prefix():
    paths = {
        route.path
        for route in main.app.routes
        if hasattr(route, "path")
    }
    assert "/api/v1/admin/analytics/occupancy-by-weekday" in paths
    assert "/api/v1/admin/analytics/occupancy-slots" in paths
    assert "/api/v1/admin/analytics/utilization" in paths
    assert "/api/v1/admin/analytics/occupancy-trend" in paths
    assert "/api/v1/admin/analytics/cancellations" in paths
    assert "/api/v1/admin/analytics/safi-impact" in paths
