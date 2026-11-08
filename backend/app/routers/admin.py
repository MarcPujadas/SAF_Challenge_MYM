from typing import Any

from fastapi import APIRouter, Query

from app.common import ApiError, success
from app.services.admin_analytics_service import (
    get_cancellation_analytics,
    get_occupancy_by_weekday,
    get_occupancy_slot_rankings,
    get_occupancy_trend,
    get_safi_impact,
    get_space_utilization,
)
from app.services.admin_service import (
    get_admin_occupancy,
    get_admin_reservation_rows,
    get_admin_stats,
    get_admin_summary,
)
from app.services.recommendation_analytics_service import get_recommendation_stats
from app.services.schedule_service import parse_date_range


router = APIRouter(prefix="/api/v1")


@router.get("/admin/summary")
def admin_summary() -> dict[str, Any]:
    return success(get_admin_summary())


@router.get("/admin/stats")
def admin_stats() -> dict[str, Any]:
    return success(get_admin_stats())


@router.get("/admin/reservations")
def admin_reservations() -> dict[str, Any]:
    return success(get_admin_reservation_rows())


@router.get("/admin/occupancy")
def admin_occupancy(
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    space_id: str | None = None,
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    return success(get_admin_occupancy(start, end, space_id))


@router.get("/admin/recommendations/stats")
def admin_recommendation_stats(
    space_id: str | None = None,
    service_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    return success(
        {
            "period": {"from": start, "to": end},
            "space_id": space_id,
            "service_id": service_id,
            **get_recommendation_stats(
                space_id,
                start,
                end,
                service_id=service_id,
            ),
        }
    )


@router.get("/admin/analytics/occupancy-by-weekday")
def occupancy_by_weekday(
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    return success(
        {
            "period": {"from": start, "to": end},
            "spaces": get_occupancy_by_weekday(space_id, start, end),
        }
    )


@router.get("/admin/analytics/occupancy-slots")
def occupancy_slots(
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    return success(
        {
            "period": {"from": start, "to": end},
            "spaces": get_occupancy_slot_rankings(space_id, start, end),
        }
    )


@router.get("/admin/analytics/utilization")
def utilization(
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    return success(
        {
            "period": {"from": start, "to": end},
            "spaces": get_space_utilization(space_id, start, end),
        }
    )


@router.get("/admin/analytics/occupancy-trend")
def occupancy_trend(
    group_by: str = Query(default="week"),
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    if group_by not in {"week", "month"}:
        raise ApiError("INVALID_GROUP_BY", "'group_by' must be 'week' or 'month'.")
    start, end = parse_date_range(date_from, date_to)
    return success(
        {
            "period": {"from": start, "to": end},
            "group_by": group_by,
            "series": get_occupancy_trend(group_by, space_id, start, end),
        }
    )


@router.get("/admin/analytics/cancellations")
def cancellations(
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    return success(
        {
            "period": {"from": start, "to": end},
            "spaces": get_cancellation_analytics(space_id, start, end),
        }
    )


@router.get("/admin/analytics/safi-impact")
def safi_impact(
    space_id: str | None = None,
    service_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    impact = get_safi_impact(
        space_id,
        start,
        end,
        service_id=service_id,
    )
    return success(
        {
            "period": {"from": start, "to": end},
            "service_id": service_id,
            "services" if service_id is not None else "spaces": impact,
        }
    )
