import pytest
from fastapi.testclient import TestClient

from app import main
from app.config.service_spaces import (
    SERVICE_SPACE_MAPPINGS,
    ResourceMapping,
)
from app.config.services import SERVICES
from app.database import database
from app.database.service_spaces import seed_service_spaces
from app.services.catalog_service import (
    get_catalog_scope,
    get_service_resources,
    get_service_space_quality_report,
    get_services_for_space,
)


PADEL_PISTA_2_ID = "pistes-de-padel-pista-2"


@pytest.fixture
def catalog_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "catalog.db")
    with TestClient(main.app) as client:
        with database.get_connection() as connection:
            for resource in SERVICE_SPACE_MAPPINGS:
                if resource.space_id == PADEL_PISTA_2_ID:
                    continue
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
                    VALUES (?, ?, ?, 10, 1)
                    """,
                    (
                        resource.space_id,
                        resource.label,
                        space_type,
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


def test_service_spaces_seed_is_idempotent_and_preserves_foreign_keys(
    catalog_client,
):
    with database.get_connection() as connection:
        initial_count = connection.execute(
            "SELECT COUNT(*) FROM service_spaces"
        ).fetchone()[0]
        seed_service_spaces(connection)
        repeated_count = connection.execute(
            "SELECT COUNT(*) FROM service_spaces"
        ).fetchone()[0]
        foreign_keys_enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert initial_count == len(SERVICE_SPACE_MAPPINGS)
    assert repeated_count == initial_count
    assert foreign_keys_enabled == 1


def test_catalog_contains_fitness_and_eight_pool_lanes(catalog_client):
    fitness = get_service_resources("fitness")
    pool_lanes = get_service_resources("pool-25m")

    assert len(fitness) == 1
    assert fitness[0]["space_id"] == "sala-fitnes-sala-cardio"
    assert fitness[0]["capacity_mode"] == "people"
    assert len(pool_lanes) == 8
    assert [resource["display_order"] for resource in pool_lanes] == list(
        range(1, 9)
    )
    assert all(resource["person_capacity"] == 10 for resource in pool_lanes)


def test_padel_mapping_includes_virtual_second_court(catalog_client):
    padel_resources = get_service_resources("padel")
    pista_2 = next(
        resource
        for resource in padel_resources
        if resource["space_id"] == PADEL_PISTA_2_ID
    )

    assert len(padel_resources) == 4
    assert pista_2["is_virtual"] is True
    assert pista_2["capacity_mode"] == "resource_units"
    assert pista_2["reservation_capacity"] == 1
    assert pista_2["person_capacity"] is None


def test_all_non_virtual_mapped_resources_exist_and_quality_report_passes(
    catalog_client,
):
    with database.get_connection() as connection:
        database_space_ids = {
            row["id"]
            for row in connection.execute("SELECT id FROM spaces").fetchall()
        }

    assert all(
        resource.space_id in database_space_ids or resource.allow_virtual
        for resource in SERVICE_SPACE_MAPPINGS
    )
    report = get_service_space_quality_report(
        historical_space_ids=(
            resource.space_id for resource in SERVICE_SPACE_MAPPINGS
        )
    )

    assert report["valid"] is True
    assert report["padel_pista_2"] == {
        "space_id": PADEL_PISTA_2_ID,
        "declared": True,
        "mapped": True,
        "virtual": True,
        "space_exists": False,
    }


def test_catalog_exposes_reverse_and_legacy_representative_mappings(
    catalog_client,
):
    space_services = get_services_for_space("piscina-25-metres-carrer-2")
    service_scope = get_catalog_scope("pool-25m")
    resource_scope = get_catalog_scope("piscina-25-metres-carrer-2")

    assert space_services[0]["id"] == "pool-25m"
    assert service_scope["scope"] == "service"
    assert service_scope["representative_space_id"] == (
        "piscina-25-metres-carrer-1"
    )
    assert len(service_scope["space_ids"]) == 8
    assert resource_scope["scope"] == "resource"
    assert resource_scope["service_ids"] == ["pool-25m"]


def test_invalid_mapping_is_reported_without_affecting_api(catalog_client):
    invalid_mapping = ResourceMapping(
        service_id="fitness",
        space_id="missing-physical-resource",
        label="Missing resource",
        display_order=1,
        capacity_mode="people",
    )
    report = get_service_space_quality_report(
        historical_space_ids={"historical-unmapped-resource"},
        resource_mappings=(invalid_mapping,),
    )

    assert report["valid"] is False
    assert "missing-physical-resource" in report["issues"][
        "missing_mapped_spaces"
    ]
    assert report["issues"]["historical_unmapped_resources"] == [
        "historical-unmapped-resource"
    ]
    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO spaces (id, name, type, capacity, reservable)
            VALUES ('unmapped-court', 'Unmapped court', 'court', 1, 1)
            """
        )
    updated_report = get_service_space_quality_report(
        historical_space_ids={"historical-unmapped-resource"},
        resource_mappings=(invalid_mapping,),
    )
    assert "unmapped-court" in updated_report["issues"][
        "unmapped_database_spaces"
    ]
    response = catalog_client.get("/api/v1/services")
    spaces_response = catalog_client.get("/api/v1/spaces")
    assert response.status_code == 200
    assert spaces_response.status_code == 200
    assert response.json()["success"] is True
    assert spaces_response.json()["success"] is True
    assert all("space_id" in item for item in response.json()["data"])
