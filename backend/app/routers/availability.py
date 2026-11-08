from typing import Any

from fastapi import APIRouter, Query

from app.common import ApiError, success
from app.services.availability_service import (
    get_day_availability,
    get_service_week_availability,
    get_week_availability,
)
from app.services.historical_service import (
    get_historical_heatmap,
    get_service_historical_heatmap,
)
from app.services.schedule_service import (
    parse_date,
    parse_date_range,
)


router = APIRouter(prefix="/api/v1")


@router.get("/availability")
def availability(
    space_id: str = Query(...),
    date_value: str = Query(..., alias="date"),
):
    return success(
        get_day_availability(space_id, parse_date(date_value))
    )


@router.get("/availability/week")
def availability_week(
    space_id: str = Query(...),
    date_from: str = Query(..., alias="from"),
    date_to: str = Query(..., alias="to"),
):
    start_date = parse_date(date_from, "from")
    end_date = parse_date(date_to, "to")
    return success(get_week_availability(space_id, start_date, end_date))


@router.get("/services/{service_id}/availability/week")
def service_availability_week(
    service_id: str,
    date_from: str = Query(..., alias="from"),
    date_to: str = Query(..., alias="to"),
):
    start_date = parse_date(date_from, "from")
    end_date = parse_date(date_to, "to")
    return success(
        get_service_week_availability(service_id, start_date, end_date)
    )


@router.get("/availability/heatmap")
def get_availability_heatmap(
    space_id: str | None = None,
    service_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    if space_id is not None and service_id is not None:
        raise ApiError(
            "INVALID_FILTER",
            "Provide either space_id or service_id, not both.",
        )
    if service_id is not None:
        try:
            service_heatmap = get_service_historical_heatmap(
                service_id=service_id,
                date_from=start,
                date_to=end,
                aggregate=True,
            )
        except ValueError as exc:
            raise ApiError(
                "INVALID_SERVICE",
                "The requested service is not configured for historical forecasts.",
                404,
            ) from exc
        return success(service_heatmap)
    days = get_historical_heatmap(
        date_from=start,
        date_to=end,
        space_id=space_id,
    )
    return success({"space_id": space_id, "days": days})
