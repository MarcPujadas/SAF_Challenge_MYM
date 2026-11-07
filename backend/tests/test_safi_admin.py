from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.routers import safi_admin
from app.services import safi_service


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_safhack.db")
    return TestClient(main.app)


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
        with patch.object(safi_admin, "recommend", return_value=response_data) as mock:
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
            safi_admin,
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
        with patch.object(safi_admin, "recommend") as mock:
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
