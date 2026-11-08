import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import main
from app.common import ApiError
from app.config.service_spaces import SERVICE_SPACE_MAPPINGS
from app.config.services import SERVICES
from app.database import database
from app.database.service_spaces import seed_service_spaces
from app.services import historical_service, reservation_service
from app.services.recommendation_tracking_service import save_recommendation


TEST_DATE = "2026-11-10"
FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"


@pytest.fixture
def phase3_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "phase3.db")
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        lambda: pd.DataFrame(
            columns=[
                "space_id",
                "date",
                "weekday",
                "start_time",
                "reservations",
            ]
        ),
    )
    with TestClient(main.app) as client:
        with database.get_connection() as connection:
            for resource in SERVICE_SPACE_MAPPINGS:
                if resource.allow_virtual:
                    continue
                capacity = 10 if resource.capacity_mode == "people" else 1
                space_type = (
                    "fitness"
                    if resource.service_id == "fitness"
                    else "pool"
                    if resource.service_id.startswith("pool-")
                    else "activity_room"
                    if resource.service_id == "guided-activities"
                    else "court"
                )
                connection.execute(
                    """
                    INSERT INTO spaces (id, name, type, capacity, reservable)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (
                        resource.space_id,
                        resource.label,
                        space_type,
                        capacity,
                    ),
                )
            for service in SERVICES:
                connection.execute(
                    """
                    INSERT INTO services (
                        id, name, description, space_id, reservable
                    )
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (
                        service.service_id,
                        service.name,
                        service.description,
                        service.space_id,
                    ),
                )
            seed_service_spaces(connection)
        yield client


def _create(client, *, user_id, service_id, space_id=None, participants=None):
    return client.post(
        "/api/v1/reservations",
        json={
            "user_id": user_id,
            "service_id": service_id,
            "space_id": space_id,
            "participants_count": participants,
            "date": TEST_DATE,
            "start": "18:30",
            "end": "19:45",
        },
    )


def test_catalog_adds_service_metadata_and_real_spaces(phase3_client):
    services = phase3_client.get("/api/v1/services").json()["data"]
    tennis = next(item for item in services if item["id"] == "tennis")

    spaces = phase3_client.get(
        "/api/v1/services/tennis/spaces"
    ).json()["data"]

    assert tennis["resource_count"] == 5
    assert tennis["capacity_mode"] == "unit"
    assert len(spaces) == 5
    assert {item["space_id"] for item in spaces} == {
        f"tennis-tennis-{number}" for number in range(1, 6)
    }


def test_service_week_availability_aggregates_units_and_people(phase3_client):
    tennis = phase3_client.get(
        "/api/v1/services/tennis/availability/week",
        params={"from": TEST_DATE, "to": TEST_DATE},
    ).json()["data"]
    tennis_slot = next(
        slot
        for slot in tennis["days"][0]["slots"]
        if slot["start"] == "18:30"
    )

    fitness_booking = _create(
        phase3_client,
        user_id="demo-user",
        service_id="fitness",
        participants=3,
    )
    assert fitness_booking.status_code == 200
    fitness = phase3_client.get(
        "/api/v1/services/fitness/availability/week",
        params={"from": TEST_DATE, "to": TEST_DATE},
    ).json()["data"]
    fitness_slot = next(
        slot
        for slot in fitness["days"][0]["slots"]
        if slot["start"] == "18:30"
    )

    assert tennis["capacity_mode"] == "unit"
    assert tennis_slot["available_units"] == 5
    assert tennis_slot["total_units"] == 5
    assert fitness["capacity_mode"] == "people"
    assert fitness_slot["available_units"] is None
    assert fitness_slot["total_units"] is None
    assert fitness_slot["remaining_people_capacity"] == 7


def test_pool_forecast_stays_unknown_without_people_metrics(phase3_client):
    pool_spaces = phase3_client.get(
        "/api/v1/services/pool-25m/spaces"
    ).json()["data"]
    heatmap = phase3_client.get(
        "/api/v1/availability/heatmap",
        params={
            "service_id": "pool-25m",
            "from": TEST_DATE,
            "to": TEST_DATE,
        },
    ).json()["data"]

    assert len(pool_spaces) == 8
    assert {
        item["space_id"] for item in pool_spaces
    } == {
        f"piscina-25-metres-carrer-{number}"
        for number in range(1, 9)
    }
    assert heatmap["aggregate"] is False
    assert heatmap["unavailable_reason"] == (
        "aggregated_forecast_not_validated"
    )
    assert all(
        slot["occupancy_score"] is None
        and slot["occupancy_level"] == "unknown"
        for day in heatmap["days"]
        for slot in day["slots"]
    )


def test_service_reservation_autoassigns_and_cancellation_releases_capacity(
    phase3_client,
):
    first = _create(
        phase3_client,
        user_id="demo-user",
        service_id="tennis",
    )
    assert first.status_code == 200
    assigned = first.json()["data"]
    assert assigned["service_id"] == "tennis"
    assert assigned["space_id"] == "tennis-tennis-1"

    available = phase3_client.get(
        "/api/v1/services/tennis/availability/week",
        params={"from": TEST_DATE, "to": TEST_DATE},
    ).json()["data"]
    slot = next(
        slot
        for slot in available["days"][0]["slots"]
        if slot["start"] == "18:30"
    )
    assert slot["available_units"] == 4

    cancelled = phase3_client.delete(
        f"/api/v1/reservations/{assigned['reservation_id']}"
    )
    assert cancelled.status_code == 200
    available_after_cancel = phase3_client.get(
        "/api/v1/services/tennis/availability/week",
        params={"from": TEST_DATE, "to": TEST_DATE},
    ).json()["data"]
    slot_after_cancel = next(
        slot
        for slot in available_after_cancel["days"][0]["slots"]
        if slot["start"] == "18:30"
    )
    assert slot_after_cancel["available_units"] == 5


def test_padel_pista_2_is_available_and_autoassigned_when_first_is_full(
    phase3_client,
):
    with database.get_connection() as connection:
        connection.execute(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ("padel-user-2", "Padel User 2"),
        )

    spaces = phase3_client.get(
        "/api/v1/services/padel/spaces"
    ).json()["data"]
    pista_2 = next(
        item
        for item in spaces
        if item["space_id"] == "pistes-de-padel-pista-2"
    )
    first = _create(
        phase3_client,
        user_id="demo-user",
        service_id="padel",
        space_id="pistes-de-padel-pista-1",
    )
    second = _create(
        phase3_client,
        user_id="padel-user-2",
        service_id="padel",
    )

    assert pista_2["is_virtual"] is True
    assert pista_2["reservable"] is True
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["space_id"] == "pistes-de-padel-pista-2"

    week = phase3_client.get(
        "/api/v1/services/padel/availability/week",
        params={"from": TEST_DATE, "to": TEST_DATE},
    ).json()["data"]
    slot = next(
        slot
        for slot in week["days"][0]["slots"]
        if slot["start"] == "18:30"
    )
    availability = {
        item["space_id"]: item["available"]
        for item in slot["spaces"]
    }
    assert week["capacity_mode"] == "unit"
    assert availability["pistes-de-padel-pista-1"] is False
    assert availability["pistes-de-padel-pista-2"] is False
    assert availability["pistes-de-padel-pista-3"] is True
    assert availability["pistes-de-padel-pista-4"] is True

    phase3_client.delete(
        f"/api/v1/reservations/{second.json()['data']['reservation_id']}"
    )
    released = phase3_client.get(
        "/api/v1/services/padel/availability/week",
        params={"from": TEST_DATE, "to": TEST_DATE},
    ).json()["data"]
    released_slot = next(
        slot
        for slot in released["days"][0]["slots"]
        if slot["start"] == "18:30"
    )
    released_availability = {
        item["space_id"]: item["available"]
        for item in released_slot["spaces"]
    }
    assert released_availability["pistes-de-padel-pista-1"] is False
    assert released_availability["pistes-de-padel-pista-2"] is True


@pytest.mark.parametrize(
    ("first_space", "second_space", "conflict_expected"),
    [
        ("futbol-7-camp-4", "futbol-7-camp-4-1", True),
        ("futbol-7-camp-4", "futbol-7-camp-4-2", True),
        ("futbol-7-camp-4-1", "futbol-7-camp-4", True),
        ("futbol-7-camp-4-1", "futbol-7-camp-4-2", False),
    ],
)
def test_football_full_and_half_field_conflicts(
    phase3_client,
    first_space,
    second_space,
    conflict_expected,
):
    with database.get_connection() as connection:
        connection.executemany(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            [
                ("football-user-1", "Football User 1"),
                ("football-user-2", "Football User 2"),
            ],
        )

    first = reservation_service.create_reservation(
        "football-user-1",
        first_space,
        TEST_DATE,
        "18:00",
        "19:00",
        service_id="football",
    )
    second_availability = phase3_client.get(
        "/api/v1/availability/week",
        params={
            "space_id": second_space,
            "from": TEST_DATE,
            "to": TEST_DATE,
        },
    ).json()["data"]
    second_slot = next(
        slot
        for slot in second_availability["days"][0]["slots"]
        if slot["start"] == "18:00"
    )
    assert second_slot["available"] is not conflict_expected

    if conflict_expected:
        with pytest.raises(ApiError) as conflict:
            reservation_service.create_reservation(
                "football-user-2",
                second_space,
                TEST_DATE,
                "18:00",
                "19:00",
                service_id="football",
            )
        assert conflict.value.code == "SLOT_NOT_AVAILABLE"
    else:
        second = reservation_service.create_reservation(
            "football-user-2",
            second_space,
            TEST_DATE,
            "18:00",
            "19:00",
            service_id="football",
        )
        assert first["space_id"] != second["space_id"]


def test_service_reservation_validates_membership_and_preserves_old_payload(
    phase3_client,
):
    invalid = _create(
        phase3_client,
        user_id="demo-user",
        service_id="tennis",
        space_id="pistes-de-padel-pista-1",
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_SERVICE_SPACE"

    legacy = phase3_client.post(
        "/api/v1/reservations",
        json={
            "user_id": "demo-user",
            "space_id": "tennis-tennis-1",
            "date": TEST_DATE,
            "start": "18:30",
            "end": "19:45",
        },
    )
    assert legacy.status_code == 200
    assert legacy.json()["data"]["service_id"] == "tennis"
    assert legacy.json()["data"]["space_id"] == "tennis-tennis-1"


def test_autoselection_refuses_full_service_and_user_conflicts_across_spaces(
    phase3_client,
):
    with database.get_connection() as connection:
        for index in range(2, 7):
            connection.execute(
                "INSERT INTO users (id, name) VALUES (?, ?)",
                (f"user-{index}", f"User {index}"),
            )
    for index in range(1, 6):
        response = _create(
            phase3_client,
            user_id="demo-user" if index == 1 else f"user-{index}",
            service_id="tennis",
        )
        assert response.status_code == 200

    with pytest.raises(ApiError) as full:
        reservation_service.create_reservation(
            "user-6",
            None,
            TEST_DATE,
            "18:30",
            "19:45",
            service_id="tennis",
        )
    assert full.value.code == "SLOT_NOT_AVAILABLE"

    with pytest.raises(ApiError) as conflict:
        reservation_service.create_reservation(
            "demo-user",
            None,
            TEST_DATE,
            "18:30",
            "19:45",
            service_id="tennis",
        )
    assert conflict.value.code == "RESERVATION_CONFLICT"


def test_concurrent_service_bookings_do_not_overassign_resources(
    phase3_client,
):
    with database.get_connection() as connection:
        for index in range(1, 9):
            connection.execute(
                "INSERT INTO users (id, name) VALUES (?, ?)",
                (f"parallel-user-{index}", f"Parallel {index}"),
            )

    def create(index):
        try:
            reservation_service.create_reservation(
                f"parallel-user-{index}",
                None,
                TEST_DATE,
                "18:30",
                "19:45",
                service_id="tennis",
            )
            return "created"
        except ApiError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(create, range(1, 9)))

    assert outcomes.count("created") == 5
    assert outcomes.count("SLOT_NOT_AVAILABLE") == 3
    with database.get_connection() as connection:
        reservations = connection.execute(
            """
            SELECT COUNT(*)
            FROM reservations
            WHERE service_id = 'tennis' AND status = 'confirmed'
            """
        ).fetchone()[0]
    assert reservations == 5


def test_service_heatmap_only_returns_validated_service_forecast(
    phase3_client,
):
    with database.get_connection() as connection:
        for date_value, count in (
            ("2026-04-07", 5),
            ("2026-04-14", 7),
        ):
            connection.execute(
                """
                INSERT INTO historical_usage (
                    source_id, source_checksum, source_record_key,
                    service_id, space_id, date, weekday, start_time,
                    people_count, capacity_people_snapshot,
                    occupancy_ratio, raw_resource_name, capacity_mode,
                    mapping_status
                )
                VALUES (
                    'saf_reserves_2026', 'fixture-checksum', ?,
                    'fitness', ?, ?, 1, '18:30', ?, 10, ?, 'Fitness',
                    'people', 'mapped'
                )
                """,
                (
                    date_value,
                    FITNESS_SPACE_ID,
                    date_value,
                    count,
                    count / 10,
                ),
            )
        connection.execute(
            """
            INSERT INTO historical_usage (
                source_id, source_checksum, source_record_key,
                service_id, space_id, date, weekday, start_time,
                people_count, capacity_people_snapshot, occupancy_ratio,
                raw_resource_name, capacity_mode, mapping_status
            )
            VALUES (
                'app_live', 'app-checksum', 'not-historical',
                'fitness', ?, '2026-04-21', 1, '18:30', 10, 10, 1.0,
                'Fitness app reservation', 'people', 'mapped'
            )
            """,
            (FITNESS_SPACE_ID,),
        )

    fitness = phase3_client.get(
        "/api/v1/availability/heatmap",
        params={
            "service_id": "fitness",
            "from": "2026-04-07",
            "to": "2026-04-07",
        },
    ).json()["data"]
    court = phase3_client.get(
        "/api/v1/availability/heatmap",
        params={
            "service_id": "tennis",
            "from": TEST_DATE,
            "to": TEST_DATE,
        },
    ).json()["data"]

    fitness_slot = next(
        slot for slot in fitness["days"][0]["slots"]
        if slot["hour"] == "18:30"
    )
    court_slot = next(
        slot for slot in court["days"][0]["slots"]
        if slot["hour"] == "18:30"
    )
    assert fitness["aggregate"] is True
    assert fitness_slot["occupancy_score"] == 60
    assert fitness_slot["samples"] == 2
    assert fitness_slot["occupancy_ratio"] == 0.6
    assert court["aggregate"] is False
    assert court["unavailable_reason"] == (
        "aggregated_forecast_not_validated"
    )
    assert court_slot["occupancy_score"] is None
    assert court_slot["occupancy_level"] == "unknown"


def test_court_recommendations_remain_unknown_without_aggregate_forecast(
    phase3_client,
):
    response = phase3_client.post(
        "/api/v1/recommendations",
        json={
            "service_id": "tennis",
            "date": TEST_DATE,
            "preferred_start": "18:30",
            "preferred_end": "19:45",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["recommendation_id"] is None
    assert data["requested_slot"]["occupancy_score"] is None
    assert data["requested_slot"]["occupancy_level"] == "unknown"
    assert data["unavailable_reason"] == (
        "aggregated_forecast_not_validated"
    )


def test_valid_service_recommendation_uses_normalized_people_history(
    phase3_client,
):
    with database.get_connection() as connection:
        rows = [
            ("2026-04-07", "18:30", 9),
            ("2026-04-07", "19:45", 2),
            ("2026-04-14", "18:30", 8),
            ("2026-04-14", "19:45", 3),
        ]
        for date_value, start_time, people_count in rows:
            connection.execute(
                """
                INSERT INTO historical_usage (
                    source_id, source_checksum, source_record_key,
                    service_id, space_id, date, weekday, start_time,
                    people_count, capacity_people_snapshot,
                    occupancy_ratio, raw_resource_name, capacity_mode,
                    mapping_status
                )
                VALUES (
                    'saf_reserves_2026', 'fixture-checksum', ?,
                    'fitness', ?, ?, 1, ?, ?, 10, ?, 'Fitness',
                    'people', 'mapped'
                )
                """,
                (
                    f"{date_value}-{start_time}",
                    FITNESS_SPACE_ID,
                    date_value,
                    start_time,
                    people_count,
                    people_count / 10,
                ),
            )

    response = phase3_client.post(
        "/api/v1/recommendations",
        json={
            "service_id": "fitness",
            "date": TEST_DATE,
            "preferred_start": "18:30",
            "preferred_end": "19:45",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["recommendation_id"]
    assert data["requested_slot"]["occupancy_score"] == 85
    assert data["recommended_slot"]["start"] == "19:45"
    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT service_id, space_id FROM recommendations WHERE id = ?",
            (data["recommendation_id"],),
        ).fetchone()
    assert row["service_id"] == "fitness"
    assert row["space_id"] is None
    stats = phase3_client.get(
        "/api/v1/admin/recommendations/stats",
        params={"service_id": "fitness"},
    ).json()["data"]
    assert stats["service_id"] == "fitness"
    assert stats["total_recommendations"] == 1
    impact = phase3_client.get(
        "/api/v1/admin/analytics/safi-impact",
        params={"service_id": "fitness"},
    ).json()["data"]
    assert impact["services"][0]["service_id"] == "fitness"
    assert impact["services"][0]["recommendations_generated"] == 1


def test_future_fitness_forecast_uses_comparable_legacy_history(
    phase3_client,
    monkeypatch,
):
    history = pd.DataFrame(
        [
            (FITNESS_SPACE_ID, date_value, 1, start_time, reservations)
            for date_value, counts in (
                ("2026-04-07", (9, 2)),
                ("2026-04-14", (10, 3)),
                ("2026-04-21", (8, 1)),
            )
            for start_time, reservations in zip(
                ("18:30", "19:45"),
                counts,
            )
        ],
        columns=[
            "space_id",
            "date",
            "weekday",
            "start_time",
            "reservations",
        ],
    )
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        lambda: history.copy(),
    )

    comparable = historical_service.get_historical_occupancy(
        FITNESS_SPACE_ID,
        1,
        "18:30",
    )
    forecast = historical_service.get_service_historical_occupancy(
        "fitness",
        1,
        "18:30",
    )
    heatmap = historical_service.get_service_historical_heatmap(
        "fitness",
        "2026-11-10",
        "2026-11-10",
    )
    recommendation = phase3_client.post(
        "/api/v1/recommendations",
        json={
            "service_id": "fitness",
            "date": "2026-11-10",
            "preferred_start": "18:30",
            "preferred_end": "19:45",
        },
    ).json()["data"]
    heatmap_slot = next(
        slot
        for slot in heatmap["days"][0]["slots"]
        if slot["hour"] == "18:30"
    )

    assert forecast["source"] == "historical_occupancy.csv"
    assert forecast["samples"] == 3
    assert forecast["occupancy_score"] == comparable["occupancy_score"]
    assert forecast["occupancy_ratio"] is None
    assert heatmap["source"] == "historical_occupancy.csv"
    assert heatmap_slot["samples"] == 3
    assert heatmap_slot["occupancy_score"] == comparable["occupancy_score"]
    assert recommendation["recommendation_id"] is not None
    assert recommendation["requested_slot"]["occupancy_score"] == (
        comparable["occupancy_score"]
    )
    assert recommendation["recommended_slot"]["start"] == "19:45"


def test_future_fitness_without_comparable_samples_stays_unknown(
    phase3_client,
    monkeypatch,
):
    monkeypatch.setattr(
        historical_service,
        "load_historical_data",
        lambda: pd.DataFrame(
            columns=[
                "space_id",
                "date",
                "weekday",
                "start_time",
                "reservations",
            ]
        ),
    )

    forecast = historical_service.get_service_historical_occupancy(
        "fitness",
        1,
        "18:30",
    )
    recommendation = phase3_client.post(
        "/api/v1/recommendations",
        json={
            "service_id": "fitness",
            "date": "2026-11-10",
            "preferred_start": "18:30",
            "preferred_end": "19:45",
        },
    ).json()["data"]

    assert forecast["occupancy_score"] is None
    assert forecast["occupancy_level"] == "unknown"
    assert forecast["samples"] == 0
    assert forecast["unavailable_reason"] == "historical_data_unavailable"
    assert recommendation["recommendation_available"] is False
    assert recommendation["requested_slot"]["occupancy_score"] is None
    assert recommendation["unavailable_reason"] == (
        "historical_data_unavailable"
    )


def test_service_recommendation_tracking_stores_service_without_proxy_space(
    phase3_client,
):
    recommendation_id = save_recommendation(
        user_id="demo-user",
        space_id=None,
        service_id="fitness",
        date=TEST_DATE,
        requested_start="18:30",
        recommended_start=None,
        requested_score=60,
        recommended_score=None,
    )
    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT service_id, space_id FROM recommendations WHERE id = ?",
            (recommendation_id,),
        ).fetchone()

    assert row["service_id"] == "fitness"
    assert row["space_id"] is None


def test_legacy_recommendation_schema_migrates_additively(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", database_path)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE spaces (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
                capacity INTEGER NOT NULL, reservable INTEGER NOT NULL
            );
            CREATE TABLE services (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                description TEXT NOT NULL, space_id TEXT NOT NULL,
                reservable INTEGER NOT NULL,
                FOREIGN KEY (space_id) REFERENCES spaces(id)
            );
            CREATE TABLE reservations (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                space_id TEXT NOT NULL, date TEXT NOT NULL,
                start TEXT NOT NULL, end TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE recommendations (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                space_id TEXT NOT NULL, date TEXT NOT NULL,
                requested_start TEXT NOT NULL, recommended_start TEXT,
                requested_score INTEGER, recommended_score INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (space_id) REFERENCES spaces(id)
            );
            CREATE TABLE recommendation_actions (
                recommendation_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recommendation_id)
                    REFERENCES recommendations(id)
            );
            INSERT INTO users VALUES ('demo-user', 'Demo');
            INSERT INTO spaces VALUES (
                'sala-fitnes-sala-cardio', 'Fitness', 'fitness', 10, 1
            );
            INSERT INTO services VALUES (
                'fitness', 'Fitness', 'Fitness', 'sala-fitnes-sala-cardio', 1
            );
            INSERT INTO recommendations (
                id, user_id, space_id, date, requested_start
            ) VALUES (
                'legacy-rec', 'demo-user', 'sala-fitnes-sala-cardio',
                '2026-11-10', '18:30'
            );
            INSERT INTO recommendation_actions (
                recommendation_id, action
            ) VALUES ('legacy-rec', 'accepted');
            """
        )

    database.init_db()
    with database.get_connection() as connection:
        columns = {
            row["name"]: row
            for row in connection.execute(
                "PRAGMA table_info(recommendations)"
            ).fetchall()
        }
        recommendation = connection.execute(
            "SELECT service_id, space_id FROM recommendations WHERE id = ?",
            ("legacy-rec",),
        ).fetchone()
        action = connection.execute(
            "SELECT action FROM recommendation_actions WHERE recommendation_id = ?",
            ("legacy-rec",),
        ).fetchone()
        foreign_key_violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

    assert columns["space_id"]["notnull"] == 0
    assert recommendation["service_id"] == "fitness"
    assert recommendation["space_id"] == FITNESS_SPACE_ID
    assert action["action"] == "accepted"
    assert foreign_key_violations == []
