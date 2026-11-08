from __future__ import annotations

from contextlib import closing
from datetime import date, timedelta
from typing import Any

from app.common import ApiError
from app.database.database import get_connection
from app.services.catalog_service import get_space
from app.services.historical_service import get_historical_occupancy
from app.services.schedule_service import (
    build_slots,
    minutes_to_time,
    overlaps,
    time_to_minutes,
)


def _require_reservable_space(space_id: str):
    space = get_space(space_id)
    if not bool(space["reservable"]):
        raise ApiError("INVALID_SPACE", "This space is not reservable.")
    return space


def _confirmed_intervals(
    space_id: str,
    date_value: str,
) -> list[tuple[int, int]]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT start, end
            FROM reservations
            WHERE space_id = ? AND date = ? AND status = 'confirmed'
            """,
            (space_id, date_value),
        ).fetchall()
    return [
        (time_to_minutes(row["start"]), time_to_minutes(row["end"]))
        for row in rows
    ]


def _slot_capacity(
    space: Any,
    start: int,
    end: int,
    intervals: list[tuple[int, int]],
) -> dict[str, Any]:
    overlapping_reservations = sum(
        overlaps(start, end, reserved_start, reserved_end)
        for reserved_start, reserved_end in intervals
    )
    remaining_capacity = max(
        int(space["capacity"]) - overlapping_reservations,
        0,
    )
    return {
        "start": minutes_to_time(start),
        "end": minutes_to_time(end),
        "available": remaining_capacity > 0,
        "remaining_capacity": remaining_capacity,
    }


def get_slot_availability(
    space_id: str,
    date_value: date,
    start: str,
    end: str,
    *,
    include_forecast: bool = True,
) -> dict[str, Any]:
    space = _require_reservable_space(space_id)
    start_minutes = time_to_minutes(start)
    end_minutes = time_to_minutes(end)
    if (start_minutes, end_minutes) not in build_slots(
        space["id"],
        space["type"],
        date_value.weekday(),
    ):
        raise ApiError(
            "INVALID_TIME",
            "The requested time does not match a valid reservation slot.",
        )
    slot = _slot_capacity(
        space,
        start_minutes,
        end_minutes,
        _confirmed_intervals(space_id, date_value.isoformat()),
    )
    if include_forecast:
        historical = get_historical_occupancy(
            space_id=space_id,
            weekday=date_value.weekday(),
            start_time=start,
        )
        slot["occupancy_level"] = historical["occupancy_level"]
        slot["occupancy_score"] = historical["occupancy_score"]
    return slot


def get_day_availability(
    space_id: str,
    date_value: date,
) -> dict[str, Any]:
    space = _require_reservable_space(space_id)
    intervals = _confirmed_intervals(space_id, date_value.isoformat())
    slots = [
        _slot_capacity(space, start, end, intervals)
        for start, end in build_slots(
            space["id"],
            space["type"],
            date_value.weekday(),
        )
    ]
    for slot in slots:
        historical = get_historical_occupancy(
            space_id=space_id,
            weekday=date_value.weekday(),
            start_time=slot["start"],
        )
        slot["occupancy_level"] = historical["occupancy_level"]
        slot["occupancy_score"] = historical["occupancy_score"]
    return {
        "space_id": space_id,
        "date": date_value.isoformat(),
        "slots": slots,
    }


def get_week_availability(
    space_id: str,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    if start_date > end_date:
        raise ApiError(
            "INVALID_DATE_RANGE",
            "'from' must be on or before 'to'.",
        )
    space = _require_reservable_space(space_id)
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT date, start, end
            FROM reservations
            WHERE
                space_id = ?
                AND date >= ?
                AND date <= ?
                AND status = 'confirmed'
            ORDER BY date, start
            """,
            (space_id, start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

    intervals_by_date: dict[str, list[tuple[int, int]]] = {}
    for row in rows:
        intervals_by_date.setdefault(row["date"], []).append(
            (time_to_minutes(row["start"]), time_to_minutes(row["end"]))
        )

    days = []
    current_date = start_date
    while current_date <= end_date:
        date_string = current_date.isoformat()
        intervals = intervals_by_date.get(date_string, [])
        slots = [
            _slot_capacity(space, start, end, intervals)
            for start, end in build_slots(
                space["id"],
                space["type"],
                current_date.weekday(),
            )
        ]
        days.append({"date": date_string, "slots": slots})
        current_date += timedelta(days=1)

    return {
        "space_id": space_id,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "days": days,
    }


def get_service_week_availability(
    service_id: str,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    if start_date > end_date:
        raise ApiError(
            "INVALID_DATE_RANGE",
            "'from' must be on or before 'to'.",
        )

    with closing(get_connection()) as connection:
        service = connection.execute(
            "SELECT id, reservable FROM services WHERE id = ?",
            (service_id,),
        ).fetchone()
        if service is None:
            raise ApiError(
                "INVALID_SERVICE",
                "The requested service does not exist.",
                404,
            )
        if not bool(service["reservable"]):
            raise ApiError(
                "INVALID_SERVICE",
                "The requested service is not reservable.",
            )
        resources = connection.execute(
            """
            SELECT
                link.space_id,
                link.capacity_mode,
                link.reservation_capacity,
                link.person_capacity,
                link.display_order,
                spaces.name AS space_name,
                spaces.type AS space_type,
                spaces.capacity,
                spaces.reservable
            FROM service_spaces AS link
            JOIN spaces ON spaces.id = link.space_id
            WHERE link.service_id = ?
                AND link.is_active = 1
                AND spaces.reservable = 1
            ORDER BY link.display_order, link.space_id
            """,
            (service_id,),
        ).fetchall()
        reservations = connection.execute(
            """
            SELECT space_id, date, start, end, participants_count
            FROM reservations
            WHERE service_id = ?
                AND date >= ?
                AND date <= ?
                AND status = 'confirmed'
            ORDER BY date, start
            """,
            (service_id, start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

    if not resources:
        raise ApiError(
            "INVALID_SERVICE",
            "The requested service has no reservable spaces.",
        )
    capacity_modes = {row["capacity_mode"] for row in resources}
    if len(capacity_modes) != 1:
        raise ApiError(
            "INVALID_SERVICE_CONFIGURATION",
            "The service has inconsistent capacity modes.",
        )

    reservations_by_resource_date: dict[
        tuple[str, str], list[tuple[int, int, int]]
    ] = {}
    for reservation in reservations:
        reservations_by_resource_date.setdefault(
            (reservation["space_id"], reservation["date"]), []
        ).append(
            (
                time_to_minutes(reservation["start"]),
                time_to_minutes(reservation["end"]),
                int(reservation["participants_count"] or 1),
            )
        )

    days = []
    current_date = start_date
    while current_date <= end_date:
        date_string = current_date.isoformat()
        weekday = current_date.weekday()
        resource_slots = {
            row["space_id"]: set(
                build_slots(row["space_id"], row["space_type"], weekday)
            )
            for row in resources
        }
        all_slots = sorted(set().union(*resource_slots.values()))
        slots = []
        for start_minutes, end_minutes in all_slots:
            slot_resources = []
            available_units = 0
            remaining_people_capacity = 0
            is_unit_capacity = resources[0]["capacity_mode"] == "resource_units"
            for resource in resources:
                space_id = resource["space_id"]
                if (start_minutes, end_minutes) not in resource_slots[space_id]:
                    continue
                intervals = reservations_by_resource_date.get(
                    (space_id, date_string), []
                )
                used_reservations = sum(
                    overlaps(start_minutes, end_minutes, start, end)
                    for start, end, _ in intervals
                )
                used_people = sum(
                    participants
                    for start, end, participants in intervals
                    if overlaps(start_minutes, end_minutes, start, end)
                )
                if is_unit_capacity:
                    capacity = int(
                        resource["reservation_capacity"]
                        if resource["reservation_capacity"] is not None
                        else resource["capacity"]
                    )
                    remaining = max(capacity - used_reservations, 0)
                    available_units += int(remaining > 0)
                else:
                    capacity = int(
                        resource["person_capacity"]
                        if resource["person_capacity"] is not None
                        else resource["capacity"]
                    )
                    remaining = max(capacity - used_people, 0)
                    remaining_people_capacity += remaining
                slot_resources.append(
                    {
                        "space_id": space_id,
                        "available": remaining > 0,
                    }
                )

            total_units = len(slot_resources) if is_unit_capacity else None
            slots.append(
                {
                    "start": minutes_to_time(start_minutes),
                    "end": minutes_to_time(end_minutes),
                    "available": (
                        available_units > 0
                        if is_unit_capacity
                        else remaining_people_capacity > 0
                    ),
                    "capacity_mode": (
                        "unit" if is_unit_capacity else "people"
                    ),
                    "available_units": (
                        available_units if is_unit_capacity else None
                    ),
                    "total_units": total_units,
                    "remaining_people_capacity": (
                        None
                        if is_unit_capacity
                        else remaining_people_capacity
                    ),
                    "spaces": slot_resources,
                }
            )
        days.append({"date": date_string, "slots": slots})
        current_date += timedelta(days=1)

    return {
        "service_id": service_id,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "capacity_mode": (
            "unit"
            if resources[0]["capacity_mode"] == "resource_units"
            else "people"
        ),
        "days": days,
    }
