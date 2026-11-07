from fastapi.testclient import TestClient

from app import main
from app.database import database


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"


def fake_historical_occupancy(
    space_id,
    weekday,
    start_time
):
    return {
        "space_id": space_id,
        "weekday": weekday,
        "requested_start": start_time,
        "start_time": start_time,
        "occupancy_score": 60,
        "occupancy_level": "medium",
        "average_reservations": 10,
        "samples": 20,
    }


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_safhack.db"
    )

    monkeypatch.setattr(
        main,
        "get_historical_occupancy",
        fake_historical_occupancy
    )

    return TestClient(main.app)


def seed_test_data():
    with database.get_connection() as connection:

        connection.execute(
            """
            INSERT INTO users (id, name)
            VALUES (?, ?)
            """,
            (
                "demo-user-2",
                "Usuari Demo 2"
            )
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
                FITNESS_SPACE_ID,
                "Sala fitnes + sala cardio",
                "fitness",
                120,
                1
            )
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
                "Tennis - Tennis 1",
                "court",
                1,
                1
            )
        )

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
            """,
            (
                "fitness",
                "Fitness",
                "Sala de fitness i cardio",
                FITNESS_SPACE_ID,
                1
            )
        )

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
            """,
            (
                "tennis",
                "Tennis",
                "Pistes de tennis",
                TENNIS_SPACE_ID,
                1
            )
        )


def test_services_and_availability(
    tmp_path,
    monkeypatch
):
    with make_client(
        tmp_path,
        monkeypatch
    ) as client:

        seed_test_data()

        services = client.get(
            "/api/v1/services"
        )

        assert services.status_code == 200
        assert services.json()["success"] is True

        assert any(
            item["id"] == "fitness"
            for item in services.json()["data"]
        )

        availability = client.get(
            "/api/v1/availability",
            params={
                "space_id": FITNESS_SPACE_ID,
                "date": "2026-11-10"
            }
        )

        assert availability.status_code == 200

        body = availability.json()

        assert body["success"] is True

        assert (
            body["data"]["space_id"]
            == FITNESS_SPACE_ID
        )

        assert len(
            body["data"]["slots"]
        ) == 11

        slot = next(
            item
            for item in body["data"]["slots"]
            if item["start"] == "18:30"
        )

        assert slot["end"] == "19:45"
        assert slot["available"] is True
        assert slot["occupancy_score"] == 60
        assert slot["occupancy_level"] == "medium"


def test_create_and_list_reservation(
    tmp_path,
    monkeypatch
):
    with make_client(
        tmp_path,
        monkeypatch
    ) as client:

        seed_test_data()

        payload = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45"
        }

        created = client.post(
            "/api/v1/reservations",
            json=payload
        )

        assert created.status_code == 200
        assert created.json()["success"] is True

        assert (
            created.json()["data"]["status"]
            == "confirmed"
        )

        listed = client.get(
            "/api/v1/reservations",
            params={
                "user_id": "demo-user"
            }
        )

        assert listed.status_code == 200

        reservations = listed.json()["data"]

        assert len(reservations) == 1

        assert (
            reservations[0]["space_id"]
            == FITNESS_SPACE_ID
        )

        assert (
            reservations[0]["start"]
            == "18:30"
        )

        assert (
            reservations[0]["end"]
            == "19:45"
        )


def test_rejects_invalid_fitness_slot(
    tmp_path,
    monkeypatch
):
    with make_client(
        tmp_path,
        monkeypatch
    ) as client:

        seed_test_data()

        payload = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:00",
            "end": "19:00"
        }

        response = client.post(
            "/api/v1/reservations",
            json=payload
        )

        assert response.status_code == 400

        assert (
            response.json()["error"]["code"]
            == "INVALID_TIME"
        )


def test_rejects_overlapping_user_reservation(
    tmp_path,
    monkeypatch
):
    with make_client(
        tmp_path,
        monkeypatch
    ) as client:

        seed_test_data()

        first = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45"
        }

        second = {
            "user_id": "demo-user",
            "space_id": TENNIS_SPACE_ID,
            "date": "2026-11-10",
            "start": "19:00",
            "end": "20:00"
        }

        first_response = client.post(
            "/api/v1/reservations",
            json=first
        )

        assert first_response.status_code == 200

        conflict = client.post(
            "/api/v1/reservations",
            json=second
        )

        assert conflict.status_code == 409

        assert (
            conflict.json()["error"]["code"]
            == "RESERVATION_CONFLICT"
        )


def test_rejects_full_slot(
    tmp_path,
    monkeypatch
):
    with make_client(
        tmp_path,
        monkeypatch
    ) as client:

        seed_test_data()

        first = {
            "user_id": "demo-user",
            "space_id": TENNIS_SPACE_ID,
            "date": "2026-11-10",
            "start": "19:00",
            "end": "20:00"
        }

        second = {
            "user_id": "demo-user-2",
            "space_id": TENNIS_SPACE_ID,
            "date": "2026-11-10",
            "start": "19:00",
            "end": "20:00"
        }

        first_response = client.post(
            "/api/v1/reservations",
            json=first
        )

        assert first_response.status_code == 200

        full = client.post(
            "/api/v1/reservations",
            json=second
        )

        assert full.status_code == 409

        assert (
            full.json()["error"]["code"]
            == "SLOT_NOT_AVAILABLE"
        )

def test_cancel_reservation(
    tmp_path,
    monkeypatch
):
    with make_client(
        tmp_path,
        monkeypatch
    ) as client:

        seed_test_data()

        payload = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45"
        }

        created = client.post(
            "/api/v1/reservations",
            json=payload
        )

        assert created.status_code == 200

        reservation_id = (
            created.json()["data"][
                "reservation_id"
            ]
        )

        cancelled = client.delete(
            f"/api/v1/reservations/"
            f"{reservation_id}"
        )

        assert cancelled.status_code == 200
        assert cancelled.json()["success"] is True

        assert (
            cancelled.json()["data"]["status"]
            == "cancelled"
        )

        listed = client.get(
            "/api/v1/reservations",
            params={
                "user_id": "demo-user"
            }
        )

        reservations = listed.json()["data"]

        assert len(reservations) == 1

        assert (
            reservations[0]["status"]
            == "cancelled"
        )