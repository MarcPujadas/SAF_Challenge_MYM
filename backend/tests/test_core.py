from fastapi.testclient import TestClient

from app import main
from app.database import database


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_safhack.db")
    return TestClient(main.app)


def test_services_and_availability(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        services = client.get("/api/v1/services")
        assert services.status_code == 200
        assert services.json()["success"] is True
        assert any(item["id"] == "fitness" for item in services.json()["data"])

        availability = client.get(
            "/api/v1/availability",
            params={"space_id": "fitness", "date": "2026-11-10"},
        )
        assert availability.status_code == 200
        body = availability.json()
        assert body["success"] is True
        assert body["data"]["space_id"] == "fitness"
        assert len(body["data"]["slots"]) > 0


def test_create_and_list_reservation(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        payload = {
            "user_id": "demo-user",
            "space_id": "fitness",
            "date": "2026-11-10",
            "start": "19:00",
            "end": "20:15",
        }

        created = client.post("/api/v1/reservations", json=payload)
        assert created.status_code == 200
        assert created.json()["data"]["status"] == "confirmed"

        listed = client.get(
            "/api/v1/reservations",
            params={"user_id": "demo-user"},
        )
        assert listed.status_code == 200
        reservations = listed.json()["data"]
        assert len(reservations) == 1
        assert reservations[0]["space_id"] == "fitness"


def test_rejects_overlapping_user_reservation(tmp_path, monkeypatch):
    with make_client(tmp_path, monkeypatch) as client:
        first = {
            "user_id": "demo-user",
            "space_id": "fitness",
            "date": "2026-11-10",
            "start": "19:00",
            "end": "20:15",
        }
        second = {
            "user_id": "demo-user",
            "space_id": "pool",
            "date": "2026-11-10",
            "start": "19:30",
            "end": "20:30",
        }

        assert client.post("/api/v1/reservations", json=first).status_code == 200

        conflict = client.post("/api/v1/reservations", json=second)
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "RESERVATION_CONFLICT"
