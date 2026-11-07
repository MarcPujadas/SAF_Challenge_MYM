from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.services import availability_service
from scripts.import_services import SERVICES, main as import_services


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"
POOL_SPACE_ID = "piscina-25-metres-carrer-1"


def fake_historical_occupancy(
    space_id,
    weekday,
    start_time,
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


def make_client(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_safhack.db",
    )

    monkeypatch.setattr(
        availability_service,
        "get_historical_occupancy",
        fake_historical_occupancy,
    )

    return TestClient(
        main.app
    )


def seed_test_data():
    with database.get_connection() as connection:

        connection.execute(
            """
            INSERT INTO users (
                id,
                name
            )
            VALUES (?, ?)
            """,
            (
                "demo-user-2",
                "Usuari Demo 2",
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
                FITNESS_SPACE_ID,
                "Sala fitnes + sala cardio",
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
                "Tennis - Tennis 1",
                "court",
                1,
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
                POOL_SPACE_ID,
                "Piscina 25 metres - Carrer 1",
                "pool",
                5,
                1,
            ),
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
                1,
            ),
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
                1,
            ),
        )


def test_services_and_availability(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
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
                "date": "2026-11-10",
            },
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


def test_services_include_configured_spaces_and_effective_reservability(
    tmp_path,
    monkeypatch,
):
    with make_client(tmp_path, monkeypatch) as client:
        with database.get_connection() as connection:
            for service in SERVICES:
                connection.execute(
                    """
                    INSERT INTO spaces (
                        id, name, type, capacity, reservable
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        service["space_id"],
                        service["name"],
                        "fitness" if service["id"] == "fitness" else "court",
                        20,
                        0 if service["id"] == "pool-16m" else 1,
                    ),
                )
        import_services()

        response = client.get("/api/v1/services")

        assert response.status_code == 200
        services = response.json()["data"]
        expected = {service["id"]: service for service in SERVICES}
        assert {service["id"] for service in services} == set(expected)
        assert len(services) == len(expected)
        assert len({service["id"] for service in services}) == len(services)
        with database.get_connection() as connection:
            existing_space_ids = {
                row["id"]
                for row in connection.execute("SELECT id FROM spaces")
            }
        assert all(service["space_id"] for service in services)
        assert all(
            service["space_id"] in existing_space_ids
            for service in services
        )
        assert all(
            service["space_id"] == expected[service["id"]]["space_id"]
            for service in services
        )
        assert next(
            service for service in services if service["id"] == "pool-16m"
        )["reservable"] is False


def test_create_and_list_reservation(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        payload = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45",
        }

        created = client.post(
            "/api/v1/reservations",
            json=payload,
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
                "user_id": "demo-user",
            },
        )

        assert listed.status_code == 200

        reservations = listed.json()["data"]

        assert len(reservations) == 1
        assert (
            reservations[0]["space_id"]
            == FITNESS_SPACE_ID
        )
        assert reservations[0]["start"] == "18:30"
        assert reservations[0]["end"] == "19:45"


def test_rejects_invalid_fitness_slot(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        payload = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:00",
            "end": "19:00",
        }

        response = client.post(
            "/api/v1/reservations",
            json=payload,
        )

        assert response.status_code == 400
        assert (
            response.json()["error"]["code"]
            == "INVALID_TIME"
        )


def test_rejects_overlapping_user_reservation(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        first = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45",
        }

        second = {
            "user_id": "demo-user",
            "space_id": TENNIS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45",
        }

        first_response = client.post(
            "/api/v1/reservations",
            json=first,
        )

        assert first_response.status_code == 200

        conflict = client.post(
            "/api/v1/reservations",
            json=second,
        )

        assert conflict.status_code == 409
        assert (
            conflict.json()["error"]["code"]
            == "RESERVATION_CONFLICT"
        )


def test_rejects_full_slot(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        first = {
            "user_id": "demo-user",
            "space_id": TENNIS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45",
        }

        second = {
            "user_id": "demo-user-2",
            "space_id": TENNIS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45",
        }

        first_response = client.post(
            "/api/v1/reservations",
            json=first,
        )

        assert first_response.status_code == 200

        full = client.post(
            "/api/v1/reservations",
            json=second,
        )

        assert full.status_code == 409
        assert (
            full.json()["error"]["code"]
            == "SLOT_NOT_AVAILABLE"
        )


def test_cancel_reservation(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        payload = {
            "user_id": "demo-user",
            "space_id": FITNESS_SPACE_ID,
            "date": "2026-11-10",
            "start": "18:30",
            "end": "19:45",
        }

        created = client.post(
            "/api/v1/reservations",
            json=payload,
        )

        assert created.status_code == 200

        reservation_id = (
            created.json()["data"]["reservation_id"]
        )

        cancelled = client.delete(
            f"/api/v1/reservations/{reservation_id}"
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
                "user_id": "demo-user",
            },
        )

        reservations = listed.json()["data"]

        assert reservations == []
        with database.get_connection() as connection:
            stored = connection.execute(
                "SELECT status FROM reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
        assert stored["status"] == "cancelled"


def test_week_availability_includes_all_days_and_uses_sqlite_only(
    tmp_path,
    monkeypatch,
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_test_data()
        with monkeypatch.context() as patcher:
            patcher.setattr(
                availability_service,
                "get_historical_occupancy",
                lambda **_: (_ for _ in ()).throw(
                    AssertionError("weekly availability must not use history")
                ),
            )
            response = client.get(
                "/api/v1/availability/week",
                params={
                    "space_id": TENNIS_SPACE_ID,
                    "from": "2026-11-09",
                    "to": "2026-11-15",
                },
            )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["from"] == "2026-11-09"
        assert data["to"] == "2026-11-15"
        assert [day["date"] for day in data["days"]] == [
            "2026-11-09",
            "2026-11-10",
            "2026-11-11",
            "2026-11-12",
            "2026-11-13",
            "2026-11-14",
            "2026-11-15",
        ]
        assert all(day["slots"] for day in data["days"])
        assert all(
            "occupancy_score" not in slot
            and "occupancy_level" not in slot
            for day in data["days"]
            for slot in day["slots"]
        )


def test_week_availability_counts_reservations_and_full_slots(
    tmp_path,
    monkeypatch,
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_test_data()
        available = client.get(
            "/api/v1/availability/week",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-11-10",
                "to": "2026-11-10",
            },
        )
        assert available.status_code == 200
        free_slot = next(
            slot
            for slot in available.json()["data"]["days"][0]["slots"]
            if slot["start"] == "07:15"
        )
        assert free_slot["available"] is True
        assert free_slot["remaining_capacity"] == 1

        created = client.post(
            "/api/v1/reservations",
            json={
                "user_id": "demo-user",
                "space_id": TENNIS_SPACE_ID,
                "date": "2026-11-10",
                "start": "07:15",
                "end": "08:30",
            },
        )
        assert created.status_code == 200

        occupied = client.get(
            "/api/v1/availability/week",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-11-10",
                "to": "2026-11-10",
            },
        )
        full_slot = next(
            slot
            for slot in occupied.json()["data"]["days"][0]["slots"]
            if slot["start"] == "07:15"
        )
        assert full_slot["available"] is False
        assert full_slot["remaining_capacity"] == 0


def test_week_availability_rejects_bad_dates_and_spaces(
    tmp_path,
    monkeypatch,
):
    with make_client(tmp_path, monkeypatch) as client:
        seed_test_data()
        invalid_date = client.get(
            "/api/v1/availability/week",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-02-30",
                "to": "2026-03-01",
            },
        )
        invalid_range = client.get(
            "/api/v1/availability/week",
            params={
                "space_id": TENNIS_SPACE_ID,
                "from": "2026-11-11",
                "to": "2026-11-10",
            },
        )
        invalid_space = client.get(
            "/api/v1/availability/week",
            params={
                "space_id": "missing-space",
                "from": "2026-11-10",
                "to": "2026-11-10",
            },
        )

    assert invalid_date.status_code == 400
    assert invalid_date.json()["error"]["code"] == "INVALID_DATE"
    assert invalid_range.status_code == 400
    assert invalid_range.json()["error"]["code"] == "INVALID_DATE_RANGE"
    assert invalid_space.status_code == 404
    assert invalid_space.json()["error"]["code"] == "INVALID_SPACE"


def test_general_opening_hours(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        weekday_response = client.get(
            "/api/v1/availability",
            params={
                "space_id": POOL_SPACE_ID,
                "date": "2026-11-09",
            },
        )

        assert weekday_response.status_code == 200

        weekday_slots = (
            weekday_response.json()["data"]["slots"]
        )

        assert len(weekday_slots) == 14
        assert weekday_slots[0]["start"] == "07:00"
        assert weekday_slots[-1]["end"] == "21:00"

        sunday_response = client.get(
            "/api/v1/availability",
            params={
                "space_id": POOL_SPACE_ID,
                "date": "2026-11-15",
            },
        )

        assert sunday_response.status_code == 200

        sunday_slots = (
            sunday_response.json()["data"]["slots"]
        )

        assert len(sunday_slots) == 5
        assert sunday_slots[0]["start"] == "09:00"
        assert sunday_slots[-1]["end"] == "14:00"


def test_75_minute_court_slots(
    tmp_path,
    monkeypatch,
):
    with make_client(
        tmp_path,
        monkeypatch,
    ) as client:

        seed_test_data()

        weekday_response = client.get(
            "/api/v1/availability",
            params={
                "space_id": TENNIS_SPACE_ID,
                "date": "2026-11-10",
            },
        )

        assert weekday_response.status_code == 200

        weekday_slots = (
            weekday_response.json()["data"]["slots"]
        )

        assert len(weekday_slots) == 11
        assert weekday_slots[0]["start"] == "07:15"
        assert weekday_slots[0]["end"] == "08:30"
        assert weekday_slots[-1]["start"] == "19:45"
        assert weekday_slots[-1]["end"] == "21:00"

        sunday_response = client.get(
            "/api/v1/availability",
            params={
                "space_id": TENNIS_SPACE_ID,
                "date": "2026-11-15",
            },
        )

        assert sunday_response.status_code == 200

        sunday_slots = (
            sunday_response.json()["data"]["slots"]
        )

        assert len(sunday_slots) == 3
        assert sunday_slots[0]["start"] == "09:45"
        assert sunday_slots[-1]["end"] == "13:30"