import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import main
from app.config.resource_mapping import resolve_resource_mapping
from app.database import database
from app.database.service_spaces import seed_service_spaces
from app.services import historical_service
from app.services.catalog_service import get_historical_import_quality_report
from scripts import process_historical_data


FITNESS_SPACE_ID = "sala-fitnes-sala-cardio"
TENNIS_SPACE_ID = "tennis-tennis-1"


@pytest.fixture
def history_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "historical.db")
    monkeypatch.setattr(
        process_historical_data,
        "OUTPUT_PATH",
        tmp_path / "historical_occupancy.csv",
    )
    with TestClient(main.app):
        with database.get_connection() as connection:
            spaces = (
                ("piscina-25-metres-carrer-1", "pool", 8),
                ("pistes-de-padel-pista-1", "court", 1),
                ("sales-activitats-dirigides-sala-1", "activity_room", 20),
                (FITNESS_SPACE_ID, "fitness", 40),
                (TENNIS_SPACE_ID, "court", 1),
            )
            for space_id, space_type, capacity in spaces:
                connection.execute(
                    """
                    INSERT INTO spaces (id, name, type, capacity, reservable)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (space_id, space_id, space_type, capacity),
                )
            services = (
                ("pool-25m", "piscina-25-metres-carrer-1"),
                ("padel", "pistes-de-padel-pista-1"),
                (
                    "guided-activities",
                    "sales-activitats-dirigides-sala-1",
                ),
                ("fitness", FITNESS_SPACE_ID),
                ("tennis", TENNIS_SPACE_ID),
            )
            for service_id, space_id in services:
                connection.execute(
                    """
                    INSERT INTO services (
                        id, name, description, space_id, reservable
                    )
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (service_id, service_id, service_id, space_id),
                )
            seed_service_spaces(connection)
        yield


def create_synthetic_workbook(path):
    reserve_rows = pd.DataFrame(
        [
            {
                "Recurs": "P. 25m - C/1",
                "DataUs": "2026-04-06",
                "HoraInici": "08:30",
                "HoraFi": "09:30",
                "Reserves": 5,
            },
            {
                "Recurs": "Pàdel/Padbol - Pista 2",
                "DataUs": "2026-04-06",
                "HoraInici": "18:30",
                "HoraFi": "19:30",
                "Reserves": 7,
            },
            {
                "Recurs": "Unmapped sports resource",
                "DataUs": "2026-04-06",
                "HoraInici": "10:00",
                "HoraFi": None,
                "Reserves": 3,
            },
            {
                "Recurs": "Total",
                "DataUs": "2026-04-06",
                "HoraInici": "00:00",
                "HoraFi": None,
                "Reserves": 2,
            },
        ]
    )
    activity_rows = pd.DataFrame(
        [
            {
                "Recurs": "Activitats dirigides - Sala 1 - Ritmes",
                "DataUs": "2026-04-07",
                "HoraInici": "17:00",
                "HoraFi": "18:00",
                "Reserves": 4,
            }
        ]
    )
    with pd.ExcelWriter(path) as writer:
        reserve_rows.to_excel(
            writer,
            sheet_name="Reserves per franja",
            index=False,
        )
        activity_rows.to_excel(
            writer,
            sheet_name="Activitats dirigides",
            index=False,
        )


def test_resource_registry_maps_padel_two_and_known_resource_ranges():
    padel = resolve_resource_mapping("Pàdel/Padbol - Pista 2")
    pool_lane_8 = resolve_resource_mapping("P. 25m - C/8")
    tennis_5 = resolve_resource_mapping("Tennis/Pikleball - Pista 5")
    squash_4 = resolve_resource_mapping("Esquaix/C.Soccer - Pista 4")
    football_4 = resolve_resource_mapping("Futbol 7 - Camps 4")
    subdivision = resolve_resource_mapping("Futbol 7 - Mitja pista 1")
    unknown = resolve_resource_mapping("Unmapped sports resource")

    assert (padel.service_id, padel.space_id, padel.mapping_status) == (
        "padel",
        "pistes-de-padel-pista-2",
        "mapped",
    )
    assert pool_lane_8.space_id == "piscina-25-metres-carrer-8"
    assert tennis_5.space_id == "tennis-tennis-5"
    assert squash_4.space_id == "esquaix-esquaix-4"
    assert football_4.space_id == "futbol-7-camp-4"
    assert subdivision.mapping_status == "manual_review"
    assert subdivision.service_id == "football"
    assert unknown.mapping_status == "manual_review"
    assert unknown.raw_resource_name == "Unmapped sports resource"


def test_historical_import_is_idempotent_and_preserves_source_rows(
    history_client, tmp_path
):
    workbook_path = tmp_path / "synthetic_saf.xlsx"
    create_synthetic_workbook(workbook_path)

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reservations (
                id, user_id, space_id, date, start, end, status
            )
            VALUES (
                'app_reservation', 'demo-user', ?, '2026-04-06',
                '18:30', '19:30', 'confirmed'
            )
            """,
            (FITNESS_SPACE_ID,),
        )

    first = process_historical_data.process_workbook(workbook_path)
    second = process_historical_data.process_workbook(workbook_path)

    assert first["raw_rows"] == 5
    assert first["mapped_rows"] == 3
    assert first["manual_review_rows"] == 1
    assert first["ignored_rows"] == 1
    assert second["raw_rows"] == first["raw_rows"]
    assert second["source_checksum"] == first["source_checksum"]
    legacy_csv = pd.read_csv(process_historical_data.OUTPUT_PATH)
    assert set(
        (
            "space_id",
            "date",
            "weekday",
            "start_time",
            "reservations",
            "source_id",
            "service_id",
            "raw_resource_name",
            "raw_reservation_count",
            "capacity_mode",
            "mapping_status",
        )
    ).issubset(legacy_csv.columns)
    assert len(legacy_csv) == 2
    assert set(legacy_csv["date"]) == {"2026-04-06"}
    assert set(legacy_csv["mapping_status"]) == {"mapped"}

    with database.get_connection() as connection:
        source_rows = connection.execute(
            "SELECT id, checksum FROM data_sources ORDER BY id"
        ).fetchall()
        usage_rows = connection.execute(
            """
            SELECT source_id, raw_resource_name, raw_reservation_count,
                   space_id, mapping_status, people_count, occupied_units,
                   capacity_mode
            FROM historical_usage
            ORDER BY source_id, source_record_key
            """
        ).fetchall()
        operational_count = connection.execute(
            "SELECT COUNT(*) FROM reservations"
        ).fetchone()[0]
        app_live_history_count = connection.execute(
            "SELECT COUNT(*) FROM historical_usage WHERE source_id = 'app_live'"
        ).fetchone()[0]

    assert {row["id"] for row in source_rows} >= {
        "saf_reserves_2026",
        "saf_guided_activities_2026",
        "app_live",
    }
    assert len(source_rows) == 3
    assert len(usage_rows) == 5
    padel_row = next(
        row
        for row in usage_rows
        if row["raw_resource_name"] == "Pàdel/Padbol - Pista 2"
    )
    assert padel_row["space_id"] == "pistes-de-padel-pista-2"
    assert padel_row["raw_reservation_count"] == 7
    assert padel_row["capacity_mode"] == "resource_units"
    assert padel_row["people_count"] is None
    assert padel_row["occupied_units"] is None
    review_row = next(
        row
        for row in usage_rows
        if row["mapping_status"] == "manual_review"
    )
    assert review_row["space_id"] is None
    assert review_row["raw_resource_name"] == "Unmapped sports resource"
    assert review_row["raw_reservation_count"] == 3
    assert operational_count == 1
    assert app_live_history_count == 0


def test_individual_reserve_sheet_keeps_each_reservation_as_raw_volume(
    history_client, tmp_path
):
    workbook_path = tmp_path / "individual_reserves.xlsx"
    reservations = pd.DataFrame(
        [
            {
                "Recurs": "Pàdel/Padbol - Pista 2",
                "DataUs": "2026-04-06",
                "HoraInici": "18:30",
                "HoraFi": "19:30",
            },
            {
                "Recurs": "Fitness",
                "DataUs": "2026-04-06",
                "HoraInici": "19:45",
                "HoraFi": "21:00",
            },
            {
                "Recurs": "Espai Barbell (dl-dv)",
                "DataUs": "2026-04-06",
                "HoraInici": "17:00",
                "HoraFi": "18:00",
            },
        ]
    )
    with pd.ExcelWriter(workbook_path) as writer:
        reservations.to_excel(writer, sheet_name="Reserves", index=False)

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO spaces (id, name, type, capacity, reservable)
            VALUES ('espai-barbell', 'Espai Barbell', 'other', 25, 1)
            """
        )

    summary = process_historical_data.process_workbook(workbook_path)

    assert summary["raw_rows"] == 3
    with database.get_connection() as connection:
        rows = connection.execute(
            """
            SELECT raw_resource_name, raw_reservation_count, people_count,
                   occupied_units, capacity_units_snapshot, service_id,
                   space_id, mapping_status
            FROM historical_usage
            WHERE source_id = 'saf_reserves_2026'
            ORDER BY raw_resource_name
            """
        ).fetchall()

    padel_row = next(
        row for row in rows
        if row["raw_resource_name"] == "Pàdel/Padbol - Pista 2"
    )
    assert padel_row["raw_reservation_count"] == 1
    assert padel_row["people_count"] is None
    assert padel_row["occupied_units"] is None
    assert padel_row["capacity_units_snapshot"] == 1
    assert all(row["raw_reservation_count"] == 1 for row in rows)
    review_row = next(
        row for row in rows
        if row["raw_resource_name"] == "Espai Barbell (dl-dv)"
    )
    assert review_row["mapping_status"] == "manual_review"
    assert review_row["space_id"] == "espai-barbell"
    assert review_row["service_id"] is None


def test_actual_guided_session_columns_preserve_people_metrics(
    history_client,
):
    frame = pd.DataFrame(
        [
            {
                "session_id": "ga-test-1",
                "session_date": "2026-04-01",
                "room": "sala 1",
                "start_time": "12:00",
                "end_time": "12:50",
                "capacity": 35,
                "peak_enrolled": 25,
                "peak_occupancy_pct": 71,
            },
            {
                "session_id": "ga-test-2",
                "session_date": "2026-04-01",
                "room": "sala 4",
                "start_time": "18:00",
                "end_time": "18:50",
                "capacity": 30,
                "peak_enrolled": 21,
                "peak_occupancy_pct": 70,
            },
        ]
    )
    with database.get_connection() as connection:
        rows = process_historical_data.normalize_guided_activity_rows(
            frame,
            source_checksum="guided-test-checksum",
            connection=connection,
        )

    mapped, manual_review = rows
    assert mapped["raw_resource_name"] == "sala 1"
    assert mapped["space_id"] == "sales-activitats-dirigides-sala-1"
    assert mapped["people_count"] == 25
    assert mapped["capacity_people_snapshot"] == 35
    assert mapped["occupancy_ratio"] == 0.71
    assert mapped["raw_reservation_count"] is None
    assert manual_review["mapping_status"] == "manual_review"
    assert manual_review["raw_resource_name"] == "sala 4"
    assert manual_review["people_count"] == 21


def test_historical_quality_report_measures_row_and_volume_coverage(
    history_client, tmp_path
):
    workbook_path = tmp_path / "synthetic_saf.xlsx"
    create_synthetic_workbook(workbook_path)
    process_historical_data.process_workbook(workbook_path)

    report = get_historical_import_quality_report()

    assert report["raw_rows"] == 5
    assert report["raw_reservation_volume"] == 21
    assert report["unique_raw_resources"] == 5
    assert report["mapped_resources"] == 3
    assert report["manual_review_resources"] == [
        "Unmapped sports resource"
    ]
    assert report["ignored_resources"] == ["Total"]
    assert report["mapped_reservation_volume"] == 16
    assert report["coverage_by_rows_percentage"] == 60.0
    assert report["coverage_by_reservation_volume_percentage"] == 76.19
    assert report["padel_pista_2"] == {
        "space_id": "pistes-de-padel-pista-2",
        "linked": True,
        "virtual": True,
        "historical_rows": 1,
        "reservation_volume": 7.0,
        "recovered": True,
    }
    assert report["service_summary"]["pool-25m"] == {
        "mapped_resources": 1,
        "expected_resources": 8,
        "historical_resources": 1,
    }
    assert report["service_summary"]["padel"]["expected_resources"] == 4
    assert report["service_summary"]["football"]["physical_fields"] == 0
    assert report["service_summary"]["football"][
        "documented_subdivisions"
    ] == []
    assert report["service_summary"]["guided-activities"][
        "classified_locations"
    ] == 1


def test_service_historical_functions_keep_resources_separate(
    monkeypatch,
):
    historical = pd.DataFrame(
        [
            (FITNESS_SPACE_ID, "2026-04-07", 1, "18:30", 90),
            (FITNESS_SPACE_ID, "2026-04-14", 1, "18:30", 100),
            (FITNESS_SPACE_ID, "2026-04-07", 1, "19:45", 20),
            (FITNESS_SPACE_ID, "2026-04-14", 1, "19:45", 30),
            (TENNIS_SPACE_ID, "2026-04-07", 1, "18:30", 1),
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
        lambda: historical.copy(),
    )

    service_data = historical_service.prepare_service_data("fitness", 1)
    fitness_occupancy = historical_service.get_service_historical_occupancy(
        "fitness",
        1,
        "18:30",
    )
    heatmap = historical_service.get_service_historical_heatmap(
        "fitness",
        "2026-04-07",
        "2026-04-07",
    )
    alternative = historical_service.get_service_best_alternative(
        "fitness",
        1,
        "18:30",
    )
    quietest = historical_service.get_service_quietest_slot("fitness", 1)
    court_occupancy = historical_service.get_service_historical_occupancy(
        "tennis",
        1,
        "18:30",
    )

    assert set(service_data["service_id"]) == {"fitness"}
    assert set(service_data["space_id"]) == {FITNESS_SPACE_ID}
    assert fitness_occupancy["aggregate"] is False
    assert fitness_occupancy["resources"][0]["occupancy_score"] == 100
    assert heatmap["aggregate"] is False
    assert heatmap["resources"][0]["space_id"] == FITNESS_SPACE_ID
    assert alternative["aggregate"] is False
    assert quietest["resources"][0]["slot"]["start"] == "19:45"
    assert court_occupancy["aggregate"] is False
    assert len(court_occupancy["resources"]) == 5
    assert {
        item["space_id"] for item in court_occupancy["resources"]
    } == {
        "tennis-tennis-1",
        "tennis-tennis-2",
        "tennis-tennis-3",
        "tennis-tennis-4",
        "tennis-tennis-5",
    }
    assert "occupancy_score" not in court_occupancy
