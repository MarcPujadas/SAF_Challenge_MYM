from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.routers import availability, recommendations, safi_admin
from app.services import historical_service
from app.services import recommendation_service
from app.services import safi_service


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"
POOL_SPACE_ID = "piscina-25-metres-carrer-1"


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_safhack.db")
    return TestClient(main.app)


def historical_records():
    return pd.DataFrame(
        [
            (FITNESS_SPACE_ID, "2026-04-06", 0, "08:30", 10),
            (FITNESS_SPACE_ID, "2026-04-06", 0, "18:30", 90),
            (FITNESS_SPACE_ID, "2026-04-13", 0, "08:30", 20),
            (FITNESS_SPACE_ID, "2026-04-13", 0, "18:30", 100),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "08:30", 20),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "18:30", 100),
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


def empty_historical_records():
    return pd.DataFrame(
        columns=[
            "space_id",
            "date",
            "weekday",
            "start_time",
            "reservations",
        ]
    )


def seed_space_and_reservation():
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO spaces (id, name, type, capacity, reservable)
            VALUES ('sala-fitnes-sala-cardio', 'Sala Fitness', 'fitness', 120, 1)
            """
        )
        connection.execute(
            """
            INSERT INTO reservations (id, user_id, space_id, date, start, end, status)
            VALUES ('res_1', 'demo-user', 'sala-fitnes-sala-cardio',
                    '2026-11-10', '18:30', '19:45', 'confirmed')
            """
        )
        connection.execute(
            """
            INSERT INTO reservations (id, user_id, space_id, date, start, end, status)
            VALUES ('res_cancelled', 'demo-user', 'sala-fitnes-sala-cardio',
                    '2026-11-10', '19:45', '21:00', 'cancelled')
            """
        )


def test_recommendation_uses_historical_service_and_rejects_missing_data(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_space_and_reservation()

        response_data = {
            "requested_slot": {
                "start": "18:30",
                "occupancy_score": 72,
                "occupancy_level": "high",
            },
            "recommended_slot": None,
            "message": "No s'ha trobat una alternativa millor amb les dades disponibles.",
            "confidence": "medium",
            "basis": {
                "space_id": "sala-fitnes-sala-cardio",
                "weekday": "Tuesday",
                "historical_period": "2026-04-01 to 2026-10-31",
            },
        }
        with patch.object(
            recommendations,
            "recommend",
            return_value=response_data,
        ) as mock:
            response = client.post(
                "/api/v1/recommendations",
                json={
                    "space_id": "sala-fitnes-sala-cardio",
                    "date": "2026-11-10",
                    "preferred_start": "18:30",
                    "preferred_end": "20:00",
                },
            )

        assert response.status_code == 200
        assert response.json()["data"] == response_data
        mock.assert_called_once_with(
            "sala-fitnes-sala-cardio",
            "2026-11-10",
            "18:30",
            "20:00",
        )

        with patch.object(
            recommendations,
            "recommend",
            return_value={
                **response_data,
                "requested_slot": {
                    **response_data["requested_slot"],
                    "occupancy_score": None,
                },
            },
        ):
            no_data = client.post(
                "/api/v1/recommendations",
                json={
                    "space_id": "sala-fitnes-sala-cardio",
                    "date": "2026-11-10",
                    "preferred_start": "18:30",
                    "preferred_end": "20:00",
                },
            )

        assert no_data.status_code == 404
        assert no_data.json()["error"]["code"] == "OCCUPANCY_DATA_UNAVAILABLE"


def test_recommendation_validates_time_before_calling_service(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        with patch.object(        recommendations, "recommend") as mock:
            response = client.post(
                "/api/v1/recommendations",
                json={
                    "space_id": "sala-fitnes-sala-cardio",
                    "date": "2026-11-10",
                    "preferred_start": "20:00",
                    "preferred_end": "19:00",
                },
            )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TIME"
    mock.assert_not_called()


def test_safi_advice_handles_missing_data_and_uses_space_alias():
    with patch.object(
        safi_service,
        "recommend",
        return_value={
            "requested_slot": {
                "start": "18:30",
                "occupancy_score": None,
                "occupancy_level": "unknown",
            },
            "recommended_slot": None,
        },
    ) as mock:
        result = safi_service.advice("fitness", "2026-11-10", "18:30")

    assert result["message"] == safi_service.UNKNOWN_MESSAGE
    assert result["occupancy_score"] is None
    mock.assert_called_once_with(
        "sala-fitnes-sala-cardio",
        "2026-11-10",
        "18:30",
        "20:30",
    )


def test_safi_advice_reports_occupancy_before_better_alternative():
    recommendation = {
        "requested_slot": {
            "start": "18:30",
            "occupancy_score": 72,
            "occupancy_level": "high",
        },
        "recommended_slot": {
            "start": "19:45",
            "occupancy_score": 40,
            "occupancy_level": "medium",
        },
    }
    with (
        patch.object(safi_service, "recommend", return_value=recommendation),
        patch.object(
            safi_service,
            "get_historical_occupancy",
            return_value={"samples": 12},
        ) as samples,
    ):
        result = safi_service.advice("fitness", "2026-11-10", "18:00")

    assert result["type"] == "warning"
    assert result["message"] == (
        "A les 18:30 de dimarts l'ocupació acostuma a ser alta. "
        "Les 19:45 solen estar més tranquil·les (ocupació mitjana). "
        "Basat en 12 dies amb dades (abril-octubre 2026)."
    )
    assert result["alternative"]["start"] == "19:45"
    samples.assert_called_once_with("sala-fitnes-sala-cardio", 1, "18:30")


def test_safi_advice_does_not_recommend_an_equal_or_busier_alternative():
    recommendation = {
        "requested_slot": {
            "start": "18:30",
            "occupancy_score": 72,
            "occupancy_level": "high",
        },
        "recommended_slot": {
            "start": "19:45",
            "occupancy_score": 80,
            "occupancy_level": "high",
        },
    }
    with (
        patch.object(safi_service, "recommend", return_value=recommendation),
        patch.object(
            safi_service,
            "get_historical_occupancy",
            return_value={"samples": 12},
        ),
    ):
        result = safi_service.advice("fitness", "2026-11-10", "18:00")

    assert result["alternative"] is None
    assert result["message"] == (
        "A les 18:30 de dimarts l'ocupació acostuma a ser alta. "
        "No hi ha cap franja propera més tranquil·la. "
        "Basat en 12 dies amb dades (abril-octubre 2026)."
    )


def test_chat_normalizes_time_uses_real_space_and_catalan_weekday():
    recommendation = {
        "requested_slot": {
            "start": "18:30",
            "occupancy_score": 72,
            "occupancy_level": "high",
        },
        "recommended_slot": {
            "start": "19:45",
            "occupancy_score": 40,
            "occupancy_level": "medium",
        },
    }
    with (
        patch.object(safi_service, "recommend", return_value=recommendation) as mock,
        patch.object(
            safi_service,
            "get_historical_occupancy",
            return_value={"samples": 12},
        ) as samples,
    ):
        result = safi_service.chat(
            "Quan hi ha menys gent al fitness el 2026-11-10 a les 9:00?"
        )

    mock.assert_called_once()
    assert mock.call_args.args[0] == "sala-fitnes-sala-cardio"
    assert mock.call_args.args[2] == "09:00"
    assert result["message"] == (
        "A les 18:30 de dimarts l'ocupació acostuma a ser alta. "
        "Les 19:45 solen estar més tranquil·les (ocupació mitjana). "
        "Basat en 12 dies amb dades (abril-octubre 2026)."
    )
    assert result["sources"][0]["type"] == "historical_occupancy"
    assert result["sources"][0]["space_id"] == "sala-fitnes-sala-cardio"
    assert result["sources"][0]["date_reference"] == "dimarts"
    samples.assert_called_once_with("sala-fitnes-sala-cardio", 1, "18:30")


def test_chat_returns_unknown_when_requested_occupancy_has_no_data():
    recommendation = {
        "requested_slot": {
            "start": "09:00",
            "occupancy_score": None,
            "occupancy_level": "unknown",
        },
        "recommended_slot": None,
    }
    with patch.object(safi_service, "recommend", return_value=recommendation):
        result = safi_service.chat("Quan hi ha menys gent al fitness a les 9:00?")

    assert result["can_answer"] is False
    assert result["message"] == safi_service.UNKNOWN_MESSAGE
    assert result["sources"] == []


def test_admin_routes_use_real_schema_and_exclude_cancelled(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        empty_historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        seed_space_and_reservation()

        summary = client.get("/api/v1/admin/summary")
        assert summary.status_code == 200
        assert summary.json()["data"]["total_reservations"] == 1
        assert summary.json()["data"]["busiest_space"] == {
            "id": "sala-fitnes-sala-cardio",
            "name": "Sala Fitness",
        }

        stats = client.get("/api/v1/admin/stats")
        assert stats.status_code == 200
        assert stats.json()["data"]["reservations_created_by_app"] == 1
        assert stats.json()["data"]["most_used_spaces"][0]["name"] == "Sala Fitness"
        assert stats.json()["data"]["busiest_hour"] is None
        assert stats.json()["data"]["quietest_hour"] is None

        reservations = client.get("/api/v1/admin/reservations")
        assert reservations.status_code == 200
        assert len(reservations.json()["data"]) == 1
        assert reservations.json()["data"][0]["reservation_id"] == "res_1"


def test_historical_occupancy_by_date_filters_and_scores_per_space_weekday(
    monkeypatch,
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )

    result = historical_service.get_historical_occupancy_by_date(
        date_from="2026-04-06",
        date_to="2026-04-07",
        space_id=FITNESS_SPACE_ID,
    )

    assert set(result["date"]) == {"2026-04-06", "2026-04-07"}
    assert set(result["space_id"]) == {FITNESS_SPACE_ID}
    monday_busy = result[
        (result["date"] == "2026-04-06")
        & (result["start_time"] == "18:30")
    ].iloc[0]
    monday_quiet = result[
        (result["date"] == "2026-04-06")
        & (result["start_time"] == "08:30")
    ].iloc[0]
    assert monday_busy["occupancy_score"] > monday_quiet["occupancy_score"]
    assert monday_busy["occupancy_level"] == "very_high"


def test_best_day_alternative_requires_lower_occupancy_at_same_hour(
    monkeypatch,
):
    records = pd.DataFrame(
        [
            (FITNESS_SPACE_ID, "2026-04-06", 0, "08:30", 10),
            (FITNESS_SPACE_ID, "2026-04-06", 0, "18:30", 100),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "08:30", 90),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "18:30", 5),
        ],
        columns=historical_records().columns,
    )
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        lambda: records,
    )

    alternative = recommendation_service.get_best_day_alternative(
        FITNESS_SPACE_ID,
        "2026-04-06",
        "18:30",
    )

    assert alternative == {
        "date": "2026-04-07",
        "start": "18:30",
        "occupancy_score": 6,
        "occupancy_level": "low",
    }


def test_best_day_alternative_returns_none_without_better_day_or_data(
    monkeypatch,
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    assert recommendation_service.get_best_day_alternative(
        FITNESS_SPACE_ID,
        "2026-04-06",
        "18:30",
    ) is None

    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        empty_historical_records,
    )
    assert recommendation_service.get_best_day_alternative(
        FITNESS_SPACE_ID,
        "2026-04-06",
        "18:30",
    ) is None


@pytest.mark.parametrize(
    ("phrase", "expected_space_id"),
    [
        ("fitness", FITNESS_SPACE_ID),
        ("piscina de 25 m", POOL_SPACE_ID),
        ("piscina de 16 m", "piscina-de-16-metres"),
        ("pàdel", "pistes-de-padel-pista-1"),
        ("tennis", TENNIS_SPACE_ID),
        ("esquaix", "esquaix-esquaix-2"),
        ("futbol", "futbol-7-camp-1"),
        ("activitats dirigides", "sales-activitats-dirigides-sala-1"),
    ],
)
def test_safi_chat_answers_supported_services_and_detects_weekday_time(
    phrase,
    expected_space_id,
):
    recommendation = {
        "requested_slot": {
            "start": "09:00",
            "occupancy_score": 72,
            "occupancy_level": "high",
        },
        "recommended_slot": None,
    }
    with (
        patch.object(
            safi_service,
            "recommend",
            return_value=recommendation,
        ) as recommend,
        patch.object(
            safi_service,
            "get_historical_occupancy",
            return_value={"samples": 12},
        ),
    ):
        result = safi_service.chat(
            f"Quan hi ha menys ocupació al {phrase} dimarts a les 9:00?"
        )

    assert result["can_answer"] is True
    assert result["sources"][0]["space_id"] == expected_space_id
    assert result["sources"][0]["date_reference"] == "dimarts"
    assert recommend.call_args.args[0] == expected_space_id
    assert recommend.call_args.args[2] == "09:00"


def test_safi_chat_returns_unknown_when_supported_service_has_no_data():
    with patch.object(
        safi_service,
        "recommend",
        return_value={
            "requested_slot": {
                "start": None,
                "occupancy_score": None,
                "occupancy_level": "unknown",
            },
            "recommended_slot": None,
        },
    ):
        result = safi_service.chat(
            "Quan hi ha menys ocupació a la piscina el dimarts a les 9:00?"
        )

    assert result["can_answer"] is False
    assert result["message"] == safi_service.UNKNOWN_MESSAGE
    assert result["sources"] == []


def test_heatmap_returns_contract_shape_and_applies_filters(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/availability/heatmap",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-06",
                "to": "2026-04-07",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["space_id"] == FITNESS_SPACE_ID
    days = body["data"]["days"]
    assert [day["date"] for day in days] == [
        "2026-04-06",
        "2026-04-07",
    ]
    assert all(
        set(slot) == {
            "hour",
            "occupancy_score",
            "occupancy_level",
        }
        for day in days
        for slot in day["slots"]
    )
    assert {
        slot["hour"] for slot in days[0]["slots"]
    } == set(historical_service.STANDARD_75_MINUTE_SLOTS[0])
    monday_slots = {slot["hour"]: slot for slot in days[0]["slots"]}
    assert monday_slots["18:30"]["occupancy_score"] == 100
    assert monday_slots["18:30"]["occupancy_level"] == "very_high"
    assert monday_slots["07:15"] == {
        "hour": "07:15",
        "occupancy_score": None,
        "occupancy_level": "unknown",
    }


def test_heatmap_without_matching_data_returns_all_requested_empty_days(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        empty_historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/availability/heatmap",
            params={
                "from": "2026-05-01",
                "to": "2026-05-02",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "space_id": None,
        "days": [
            {"date": "2026-05-01", "slots": []},
            {"date": "2026-05-02", "slots": []},
        ],
    }


def test_heatmap_filters_by_space_and_exact_date(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/availability/heatmap",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-04-07",
                "to": "2026-04-07",
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["space_id"] == TENNIS_SPACE_ID
    assert [day["date"] for day in data["days"]] == ["2026-04-07"]
    assert {slot["hour"] for slot in data["days"][0]["slots"]} == {
        "08:30",
        "18:30",
    }
    assert all(
        slot["occupancy_level"] in {"low", "medium", "high", "very_high"}
        for slot in data["days"][0]["slots"]
    )


def test_heatmap_emits_unknown_for_unobserved_dates_and_known_fitness_slots(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/availability/heatmap",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-20",
                "to": "2026-04-20",
            },
        )

    assert response.status_code == 200
    slots = response.json()["data"]["days"][0]["slots"]
    assert {slot["hour"] for slot in slots} == set(
        historical_service.STANDARD_75_MINUTE_SLOTS[0]
    )
    slots_by_hour = {slot["hour"]: slot for slot in slots}
    assert slots_by_hour["18:30"]["occupancy_score"] == 100
    assert slots_by_hour["18:30"]["occupancy_level"] == "very_high"
    assert all(
        slot["occupancy_score"] is None
        and slot["occupancy_level"] == "unknown"
        for hour, slot in slots_by_hour.items()
        if hour not in {"08:30", "18:30"}
    )


def test_heatmap_nonfitness_uses_observed_hours_on_unobserved_weekdays(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/availability/heatmap",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-04-08",
                "to": "2026-04-08",
            },
        )

    assert response.status_code == 200
    slots = response.json()["data"]["days"][0]["slots"]
    assert {slot["hour"] for slot in slots} == {"08:30", "18:30"}
    assert all(
        slot["occupancy_score"] is None
        and slot["occupancy_level"] == "unknown"
        for slot in slots
    )


def test_heatmap_without_any_history_returns_unknown_known_fitness_slots(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        empty_historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/availability/heatmap",
            params={
                "space_id": FITNESS_SPACE_ID,
                "from": "2026-04-06",
                "to": "2026-04-06",
            },
        )

    assert response.status_code == 200
    slots = response.json()["data"]["days"][0]["slots"]
    assert {slot["hour"] for slot in slots} == set(
        historical_service.STANDARD_75_MINUTE_SLOTS[0]
    )
    assert all(
        slot["occupancy_score"] is None
        and slot["occupancy_level"] == "unknown"
        for slot in slots
    )


def test_heatmap_rejects_invalid_date_and_reversed_range(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        invalid_date = client.get(
            "/api/v1/availability/heatmap",
            params={"from": "2026-02-30"},
        )
        reversed_range = client.get(
            "/api/v1/availability/heatmap",
            params={
                "from": "2026-04-08",
                "to": "2026-04-06",
            },
        )

    assert invalid_date.status_code == 400
    assert invalid_date.json()["error"]["code"] == "INVALID_DATE"
    assert reversed_range.status_code == 400
    assert reversed_range.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_admin_occupancy_uses_historical_scores_and_space_filter(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/admin/occupancy",
            params={
                "from": "2026-04-06",
                "to": "2026-04-07",
                "space_id": FITNESS_SPACE_ID,
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["period"] == {
        "from": "2026-04-06",
        "to": "2026-04-07",
    }
    assert len(data["spaces"]) == 1
    space = data["spaces"][0]
    assert space["space_id"] == FITNESS_SPACE_ID
    assert space["peak_hour"] == "18:30"
    assert space["lowest_hour"] == "08:30"
    assert isinstance(space["average_occupancy_score"], int)


def test_admin_occupancy_returns_null_metrics_when_requested_space_has_no_data(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/v1/admin/occupancy",
            params={
                "from": "2026-05-01",
                "to": "2026-05-02",
                "space_id": FITNESS_SPACE_ID,
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["spaces"] == [
        {
            "space_id": FITNESS_SPACE_ID,
            "average_occupancy_score": None,
            "peak_hour": None,
            "lowest_hour": None,
        }
    ]


def test_admin_occupancy_rejects_invalid_date_and_reversed_range(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch) as client:
        invalid_date = client.get(
            "/api/v1/admin/occupancy",
            params={"to": "not-a-date"},
        )
        reversed_range = client.get(
            "/api/v1/admin/occupancy",
            params={
                "from": "2026-04-08",
                "to": "2026-04-06",
            },
        )

    assert invalid_date.status_code == 400
    assert invalid_date.json()["error"]["code"] == "INVALID_DATE"
    assert reversed_range.status_code == 400
    assert reversed_range.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_admin_stats_uses_real_occupancy_scores_not_app_reservations(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        seed_space_and_reservation()
        response = client.get("/api/v1/admin/stats")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["busiest_hour"] == "18:30"
    assert data["quietest_hour"] == "08:30"
    assert data["reservations_created_by_app"] == 1


def test_admin_stats_does_not_promote_a_rare_single_record_hour(
    tmp_path, monkeypatch
):
    records = historical_records()
    rare_hour = pd.DataFrame(
        [
            (
                TENNIS_SPACE_ID,
                "2026-04-06",
                0,
                "00:00",
                1,
            )
        ],
        columns=records.columns,
    )
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        lambda: pd.concat([records, rare_hour], ignore_index=True),
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/v1/admin/stats")

    assert response.status_code == 200
    assert response.json()["data"]["busiest_hour"] == "18:30"


def test_admin_stats_returns_null_hours_without_historical_data(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        empty_historical_records,
    )
    with make_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/v1/admin/stats")

    assert response.status_code == 200
    assert response.json()["data"]["busiest_hour"] is None
    assert response.json()["data"]["quietest_hour"] is None


def test_analytics_routes_keep_api_v1_prefix():
    paths = {
        route.path
        for route in safi_admin.router.routes
        if hasattr(route, "path")
    }

    assert "/api/v1/availability/heatmap" in paths
    assert "/api/v1/admin/occupancy" in paths
    assert "/api/v1/admin/stats" in paths
    assert "/availability/heatmap" not in paths

    app_paths = {
        route.path
        for route in main.app.routes
        if hasattr(route, "path")
    }
    assert "/api/v1/availability/week" in app_paths
    assert "/api/v1/services" in app_paths
    assert "/availability/week" not in app_paths
