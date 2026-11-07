import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import main
from app.common import ApiError
from app.database import database
from app.services import (
    availability_service,
    historical_service,
    reservation_service,
    schedule_service,
)


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"
TEST_DATE = "2026-11-10"


def empty_history():
    return pd.DataFrame(
        columns=[
            "space_id",
            "date",
            "weekday",
            "start_time",
            "reservations",
        ]
    )


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "hardening.db")
    monkeypatch.setattr(historical_service, "load_historical_data", empty_history)
    return TestClient(main.app)


def seed_space(space_id, space_type, capacity):
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO spaces (id, name, type, capacity, reservable)
            VALUES (?, ?, ?, ?, 1)
            """,
            (space_id, "Test space", space_type, capacity),
        )


def test_availability_service_and_reservation_share_exact_slots(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch):
        seed_space(FITNESS_SPACE_ID, "fitness", 2)
        day = availability_service.get_day_availability(
            FITNESS_SPACE_ID,
            schedule_service.parse_date(TEST_DATE),
        )
        slot = next(slot for slot in day["slots"] if slot["start"] == "18:30")

        assert slot["end"] == "19:45"
        assert slot["available"] is True
        assert (18 * 60 + 30, 19 * 60 + 45) in schedule_service.build_slots(
            FITNESS_SPACE_ID,
            "fitness",
            1,
        )

        created = reservation_service.create_reservation(
            "demo-user",
            FITNESS_SPACE_ID,
            TEST_DATE,
            slot["start"],
            slot["end"],
        )
        assert created["status"] == "confirmed"

        with pytest.raises(ApiError) as error:
            reservation_service.create_reservation(
                "demo-user",
                FITNESS_SPACE_ID,
                TEST_DATE,
                "18:00",
                "19:15",
            )
        assert error.value.code == "INVALID_TIME"


def test_cancelled_reservation_disappears_and_releases_capacity(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch):
        seed_space(TENNIS_SPACE_ID, "court", 1)
        reservation = reservation_service.create_reservation(
            "demo-user",
            TENNIS_SPACE_ID,
            TEST_DATE,
            "18:30",
            "19:45",
        )
        full_slot = availability_service.get_slot_availability(
            TENNIS_SPACE_ID,
            schedule_service.parse_date(TEST_DATE),
            "18:30",
            "19:45",
            include_forecast=False,
        )
        assert full_slot["available"] is False
        assert full_slot["remaining_capacity"] == 0

        assert reservation_service.list_user_reservations("demo-user")
        reservation_service.cancel_reservation(reservation["reservation_id"])
        assert reservation_service.list_user_reservations("demo-user") == []

        reopened_slot = availability_service.get_slot_availability(
            TENNIS_SPACE_ID,
            schedule_service.parse_date(TEST_DATE),
            "18:30",
            "19:45",
            include_forecast=False,
        )
        assert reopened_slot["available"] is True
        assert reopened_slot["remaining_capacity"] == 1


def test_user_conflict_across_spaces_and_capacity_rejection(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch):
        seed_space(FITNESS_SPACE_ID, "fitness", 1)
        seed_space(TENNIS_SPACE_ID, "court", 1)
        with database.get_connection() as connection:
            connection.execute(
                "INSERT INTO users (id, name) VALUES ('demo-user-2', 'Second user')"
            )
        reservation_service.create_reservation(
            "demo-user",
            FITNESS_SPACE_ID,
            TEST_DATE,
            "18:30",
            "19:45",
        )

        with pytest.raises(ApiError) as conflict:
            reservation_service.create_reservation(
                "demo-user",
                TENNIS_SPACE_ID,
                TEST_DATE,
                "18:30",
                "19:45",
            )
        assert conflict.value.code == "RESERVATION_CONFLICT"

        reservation_service.create_reservation(
            "demo-user-2",
            TENNIS_SPACE_ID,
            TEST_DATE,
            "19:45",
            "21:00",
        )
        with pytest.raises(ApiError) as full:
            reservation_service.create_reservation(
                "demo-user",
                TENNIS_SPACE_ID,
                TEST_DATE,
                "19:45",
                "21:00",
            )
        assert full.value.code == "SLOT_NOT_AVAILABLE"


def test_availability_forecast_is_unknown_when_history_is_empty(
    tmp_path, monkeypatch
):
    with make_client(tmp_path, monkeypatch):
        seed_space(FITNESS_SPACE_ID, "fitness", 10)
        slot = availability_service.get_slot_availability(
            FITNESS_SPACE_ID,
            schedule_service.parse_date(TEST_DATE),
            "18:30",
            "19:45",
        )
    assert slot["occupancy_score"] is None
    assert slot["occupancy_level"] == "unknown"
