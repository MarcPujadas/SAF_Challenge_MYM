from contextlib import closing
from collections import Counter
import csv
from pathlib import Path
from typing import Iterable, Sequence

from app.common import ApiError
from app.config.service_spaces import (
    SERVICE_SPACE_MAPPINGS,
    ResourceMapping,
)
from app.config.resource_mapping import documented_subdivisions
from app.database.database import get_connection


UNSUPPORTED_SAFI_RECOMMENDATION_TYPES = {"court"}
MAPPED_DATABASE_SPACE_TYPES = {
    "fitness",
    "pool",
    "court",
    "activity_room",
}
PADEL_PISTA_2_ID = "pistes-de-padel-pista-2"
HISTORICAL_DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "historical_occupancy.csv"
)


def get_space(space_id: str):
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT id, name, type, capacity, reservable
            FROM spaces
            WHERE id = ?
            """,
            (space_id,),
        ).fetchone()

    if row is None:
        raise ApiError(
            "INVALID_SPACE",
            "The requested space does not exist.",
            404,
        )
    return row


def get_service_resources(
    service_id: str,
    *,
    include_inactive: bool = False,
) -> list[dict]:
    with closing(get_connection()) as connection:
        service = connection.execute(
            "SELECT id FROM services WHERE id = ?",
            (service_id,),
        ).fetchone()
        if service is None:
            raise ApiError(
                "INVALID_SERVICE",
                "The requested service does not exist.",
                404,
            )
        active_filter = "" if include_inactive else "AND link.is_active = 1"
        rows = connection.execute(
            f"""
            SELECT
                link.service_id,
                link.space_id,
                link.resource_label,
                link.person_capacity,
                link.reservation_capacity,
                link.capacity_mode,
                link.is_active,
                link.is_virtual,
                link.display_order,
                spaces.name AS space_name,
                spaces.type AS space_type,
                spaces.reservable
            FROM service_spaces AS link
            LEFT JOIN spaces ON spaces.id = link.space_id
            WHERE link.service_id = ? {active_filter}
            ORDER BY link.display_order, link.space_id
            """,
            (service_id,),
        ).fetchall()
    return [
        {
            "service_id": row["service_id"],
            "space_id": row["space_id"],
            "resource_label": row["resource_label"],
            "space_name": row["space_name"],
            "space_type": row["space_type"],
            "person_capacity": row["person_capacity"],
            "reservation_capacity": row["reservation_capacity"],
            "capacity_mode": row["capacity_mode"],
            "is_active": bool(row["is_active"]),
            "is_virtual": bool(row["is_virtual"]),
            "reservable": (
                bool(row["reservable"])
                if row["reservable"] is not None
                else False
            ),
            "display_order": row["display_order"],
        }
        for row in rows
    ]


def get_services_for_space(space_id: str) -> list[dict[str, str]]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT services.id, services.name, services.space_id
            FROM service_spaces
            JOIN services ON services.id = service_spaces.service_id
            WHERE service_spaces.space_id = ?
                AND service_spaces.is_active = 1
            ORDER BY services.name, services.id
            """,
            (space_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_representative_space(service_id: str):
    """Resolve the legacy services.space_id used by existing API clients."""
    with closing(get_connection()) as connection:
        service = connection.execute(
            "SELECT space_id FROM services WHERE id = ?",
            (service_id,),
        ).fetchone()
    if service is None:
        raise ApiError(
            "INVALID_SERVICE",
            "The requested service does not exist.",
            404,
        )
    return get_space(service["space_id"])


def get_catalog_scope(identifier: str) -> dict:
    with closing(get_connection()) as connection:
        service = connection.execute(
            "SELECT id, space_id FROM services WHERE id = ?",
            (identifier,),
        ).fetchone()
    if service is not None:
        resources = get_service_resources(identifier)
        return {
            "scope": "service",
            "service_id": identifier,
            "representative_space_id": service["space_id"],
            "space_ids": [resource["space_id"] for resource in resources],
        }

    space = get_space(identifier)
    return {
        "scope": "resource",
        "space_id": space["id"],
        "service_ids": [
            item["id"] for item in get_services_for_space(space["id"])
        ],
    }


def _read_historical_space_ids() -> tuple[set[str], bool]:
    if not HISTORICAL_DATA_PATH.exists():
        return set(), False
    with HISTORICAL_DATA_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as historical_file:
        return {
            row["space_id"]
            for row in csv.DictReader(historical_file)
            if row.get("space_id")
        }, True


def get_service_space_quality_report(
    *,
    historical_space_ids: Iterable[str] | None = None,
    resource_mappings: Sequence[ResourceMapping] | None = None,
) -> dict:
    mappings = tuple(
        SERVICE_SPACE_MAPPINGS
        if resource_mappings is None
        else resource_mappings
    )
    mapping_counts = Counter(
        (item.service_id, item.space_id)
        for item in mappings
    )
    expected_keys = set(mapping_counts)
    expected_space_ids = {item.space_id for item in mappings}
    definitions = {
        (item.service_id, item.space_id): item
        for item in mappings
    }
    if historical_space_ids is None:
        history_ids, historical_data_available = _read_historical_space_ids()
    else:
        history_ids = set(historical_space_ids)
        historical_data_available = True

    with closing(get_connection()) as connection:
        services = connection.execute(
            """
            SELECT
                services.id,
                services.space_id,
                spaces.id AS existing_space_id
            FROM services
            LEFT JOIN spaces ON spaces.id = services.space_id
            ORDER BY services.id
            """
        ).fetchall()
        spaces = connection.execute(
            """
            SELECT id, type
            FROM spaces
            ORDER BY id
            """
        ).fetchall()
        links = connection.execute(
            """
            SELECT service_id, space_id, is_active, is_virtual
            FROM service_spaces
            ORDER BY service_id, space_id
            """
        ).fetchall()

    service_ids = {row["id"] for row in services}
    database_space_ids = {row["id"] for row in spaces}
    mapped_service_ids = {item.service_id for item in mappings}
    links_by_key = {
        (row["service_id"], row["space_id"]): row
        for row in links
    }
    invalid_service_relations = [
        {
            "service_id": row["id"],
            "space_id": row["space_id"],
        }
        for row in services
        if row["existing_space_id"] is None
    ]
    representative_mapping_mismatches = [
        {
            "service_id": row["id"],
            "space_id": row["space_id"],
        }
        for row in services
        if (row["id"], row["space_id"]) not in expected_keys
    ]
    duplicate_resources = [
        {"service_id": service_id, "space_id": space_id, "count": count}
        for (service_id, space_id), count in sorted(mapping_counts.items())
        if count > 1
    ]
    missing_mapped_spaces = [
        item.space_id
        for item in mappings
        if item.space_id not in database_space_ids
        and not (
            item.allow_virtual
            and (link := links_by_key.get((item.service_id, item.space_id)))
            is not None
            and link["is_virtual"]
        )
    ]
    missing_relations = [
        {
            "service_id": item.service_id,
            "space_id": item.space_id,
        }
        for item in mappings
        if item.service_id in service_ids
        and (item.service_id, item.space_id) not in links_by_key
        and not (
            item.allow_virtual and item.space_id not in database_space_ids
        )
    ]
    invalid_physical_links = [
        {
            "service_id": row["service_id"],
            "space_id": row["space_id"],
        }
        for row in links
        if not row["is_virtual"] and row["space_id"] not in database_space_ids
    ]
    unexpected_links = [
        {
            "service_id": row["service_id"],
            "space_id": row["space_id"],
        }
        for row in links
        if (row["service_id"], row["space_id"]) not in expected_keys
    ]
    services_without_resources = sorted(
        service_id
        for service_id in service_ids | mapped_service_ids
        if service_id not in service_ids
        or not any(
            row["service_id"] == service_id and row["is_active"]
            for row in links
        )
    )
    expected_ids_by_type = {
        "fitness": {
            item.space_id for item in mappings if item.service_id == "fitness"
        },
        "pool": {
            item.space_id
            for item in mappings
            if item.service_id in {"pool-25m", "pool-16m"}
        },
        "court": {
            item.space_id
            for item in mappings
            if item.service_id in {"padel", "tennis", "squash", "football"}
        },
        "activity_room": {
            item.space_id
            for item in mappings
            if item.service_id == "guided-activities"
        },
    }
    unmapped_database_spaces = [
        row["id"]
        for row in spaces
        if row["type"] in MAPPED_DATABASE_SPACE_TYPES
        and row["id"] not in expected_ids_by_type.get(row["type"], set())
    ]
    padel_mapping = definitions.get(("padel", PADEL_PISTA_2_ID))
    padel_link = links_by_key.get(("padel", PADEL_PISTA_2_ID))
    padel_pista_2 = {
        "space_id": PADEL_PISTA_2_ID,
        "declared": padel_mapping is not None,
        "mapped": padel_link is not None,
        "virtual": bool(padel_link["is_virtual"]) if padel_link else None,
        "space_exists": PADEL_PISTA_2_ID in database_space_ids,
    }
    missing_special_resources = (
        []
        if padel_link is not None or "padel" not in service_ids
        else [PADEL_PISTA_2_ID]
    )
    historical_unmapped_resources = sorted(
        history_ids - expected_space_ids
    )

    issues = {
        "invalid_service_relations": invalid_service_relations,
        "missing_services": sorted(mapped_service_ids - service_ids),
        "representative_mapping_mismatches": (
            representative_mapping_mismatches
        ),
        "missing_mapped_spaces": sorted(set(missing_mapped_spaces)),
        "missing_relations": missing_relations,
        "invalid_physical_links": invalid_physical_links,
        "unexpected_links": unexpected_links,
        "unmapped_database_spaces": unmapped_database_spaces,
        "duplicate_resources": duplicate_resources,
        "services_without_resources": services_without_resources,
        "missing_special_resources": missing_special_resources,
        "historical_unmapped_resources": historical_unmapped_resources,
    }
    return {
        "valid": not any(issues.values()),
        "historical_data_available": historical_data_available,
        "service_count": len(services),
        "resource_mapping_count": len(links),
        "virtual_resources": [
            {
                "service_id": row["service_id"],
                "space_id": row["space_id"],
            }
            for row in links
            if row["is_virtual"]
        ],
        "padel_pista_2": padel_pista_2,
        "issues": issues,
    }


def get_historical_import_quality_report() -> dict:
    with closing(get_connection()) as connection:
        historical_rows = connection.execute(
            """
            SELECT
                usage.source_id,
                usage.service_id,
                usage.space_id,
                usage.raw_resource_name,
                usage.raw_reservation_count,
                usage.mapping_status
            FROM historical_usage AS usage
            JOIN data_sources AS sources
                ON sources.id = usage.source_id
                AND sources.checksum = usage.source_checksum
            """
        ).fetchall()
        services = connection.execute(
            """
            SELECT services.id
            FROM services
            LEFT JOIN service_spaces
                ON service_spaces.service_id = services.id
                AND service_spaces.is_active = 1
            GROUP BY services.id
            HAVING COUNT(service_spaces.space_id) = 0
            ORDER BY services.id
            """
        ).fetchall()
        spaces_without_service = connection.execute(
            """
            SELECT spaces.id
            FROM spaces
            LEFT JOIN service_spaces
                ON service_spaces.space_id = spaces.id
                AND service_spaces.is_active = 1
            GROUP BY spaces.id
            HAVING COUNT(service_spaces.service_id) = 0
            ORDER BY spaces.id
            """
        ).fetchall()
        service_links = connection.execute(
            """
            SELECT service_id, space_id, is_virtual
            FROM service_spaces
            WHERE is_active = 1
            ORDER BY service_id, display_order, space_id
            """
        ).fetchall()
        mapped_history_spaces = connection.execute(
            """
            SELECT DISTINCT space_id
            FROM historical_usage AS usage
            JOIN data_sources AS sources
                ON sources.id = usage.source_id
                AND sources.checksum = usage.source_checksum
            WHERE usage.mapping_status = 'mapped'
                AND usage.space_id IS NOT NULL
            """
        ).fetchall()

    raw_rows = len(historical_rows)
    raw_volume = sum(
        float(row["raw_reservation_count"])
        for row in historical_rows
        if row["raw_reservation_count"] is not None
    )
    mapped_rows = [
        row for row in historical_rows
        if row["mapping_status"] == "mapped"
    ]
    mapped_volume = sum(
        float(row["raw_reservation_count"])
        for row in mapped_rows
        if row["raw_reservation_count"] is not None
    )
    raw_resources = {
        row["raw_resource_name"]
        for row in historical_rows
        if row["raw_resource_name"]
    }
    resources_by_status = {
        status: {
            row["raw_resource_name"]
            for row in historical_rows
            if row["mapping_status"] == status
            and row["raw_resource_name"]
        }
        for status in ("mapped", "manual_review", "ignored")
    }
    historical_space_ids = {
        row["space_id"]
        for row in mapped_history_spaces
        if row["space_id"]
    }
    links_by_service: dict[str, set[str]] = {}
    physical_links_by_service: dict[str, set[str]] = {}
    for row in service_links:
        links_by_service.setdefault(row["service_id"], set()).add(
            row["space_id"]
        )
        if not row["is_virtual"]:
            physical_links_by_service.setdefault(row["service_id"], set()).add(
                row["space_id"]
            )
    raw_resources_by_service = {
        service_id: {
            row["raw_resource_name"]
            for row in mapped_rows
            if row["service_id"] == service_id
            and row["raw_resource_name"]
        }
        for service_id in {
            row["service_id"] for row in mapped_rows if row["service_id"]
        }
    }

    expected_by_service: dict[str, set[str]] = {}
    for mapping in SERVICE_SPACE_MAPPINGS:
        expected_by_service.setdefault(mapping.service_id, set()).add(
            mapping.space_id
        )
    service_summary = {}
    for service_id, expected_spaces in expected_by_service.items():
        mapped_spaces = links_by_service.get(service_id, set())
        service_summary[service_id] = {
            "mapped_resources": len(mapped_spaces),
            "expected_resources": len(expected_spaces),
            "historical_resources": len(
                mapped_spaces & historical_space_ids
            ),
        }
    service_summary["football"]["physical_fields"] = len(
        physical_links_by_service.get("football", set())
        & expected_by_service["football"]
    )
    service_summary["football"]["documented_subdivisions"] = (
        documented_subdivisions()
    )
    service_summary["guided-activities"]["classified_locations"] = len(
        raw_resources_by_service.get("guided-activities", set())
    )

    expected_minimums = {
        "tennis": 5,
        "padel": 4,
        "pool-25m": 8,
        "squash": 3,
        "football": 4,
    }
    gates = {
        service_id: {
            "mapped_resources": len(links_by_service.get(service_id, set())),
            "minimum_expected": minimum,
            "passed": len(links_by_service.get(service_id, set())) >= minimum,
        }
        for service_id, minimum in expected_minimums.items()
    }
    known_volume_rows = [
        row
        for row in historical_rows
        if row["raw_reservation_count"] is not None
    ]
    coverage_by_rows = (
        round(len(mapped_rows) / raw_rows * 100, 2)
        if raw_rows
        else None
    )
    coverage_by_volume = (
        round(mapped_volume / raw_volume * 100, 2)
        if raw_volume
        else None
    )
    all_mapped_spaces = {
        row["space_id"]
        for row in service_links
        if row["space_id"] and not row["is_virtual"]
    }
    return {
        "raw_rows": raw_rows,
        "raw_reservation_volume": raw_volume,
        "rows_with_known_reservation_volume": len(known_volume_rows),
        "unique_raw_resources": len(raw_resources),
        "mapped_resources": len(resources_by_status["mapped"]),
        "manual_review_resources": sorted(
            resources_by_status["manual_review"]
        ),
        "manual_review_resource_count": len(
            resources_by_status["manual_review"]
        ),
        "ignored_resources": sorted(resources_by_status["ignored"]),
        "ignored_resource_count": len(resources_by_status["ignored"]),
        "mapped_reservation_volume": mapped_volume,
        "coverage_by_rows_percentage": coverage_by_rows,
        "coverage_by_reservation_volume_percentage": coverage_by_volume,
        "spaces_without_historical": sorted(
            all_mapped_spaces - historical_space_ids
        ),
        "services_without_spaces": [row["id"] for row in services],
        "spaces_without_service": [
            row["id"] for row in spaces_without_service
        ],
        "service_summary": service_summary,
        "resource_gates": gates,
    }


def supports_safi_recommendations(space_id: str) -> bool:
    space = get_space(space_id)
    return space["type"] not in UNSUPPORTED_SAFI_RECOMMENDATION_TYPES


def list_spaces() -> list[dict]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, name, type, capacity, reservable
            FROM spaces
            ORDER BY name
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "capacity": row["capacity"],
            "reservable": bool(row["reservable"]),
        }
        for row in rows
    ]


def list_services() -> list[dict]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT
                services.id,
                services.name,
                services.description,
                services.space_id,
                CASE
                    WHEN services.reservable = 1
                        AND spaces.reservable = 1
                    THEN 1
                    ELSE 0
                END AS reservable
            FROM services
            LEFT JOIN spaces ON spaces.id = services.space_id
            ORDER BY services.name
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "space_id": row["space_id"],
            "reservable": bool(row["reservable"]),
        }
        for row in rows
    ]


def get_current_user() -> dict[str, str]:
    return {"id": "demo-user", "name": "Usuari Demo"}
