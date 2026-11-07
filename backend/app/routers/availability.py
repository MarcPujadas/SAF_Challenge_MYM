from typing import Any

from fastapi import APIRouter, Query

from app.common import success
from app.services.availability_service import (
    get_day_availability,
    get_week_availability,
)
from app.services.historical_service import get_historical_heatmap
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


@router.get("/availability/heatmap")
def get_availability_heatmap(
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
) -> dict[str, Any]:
    start, end = parse_date_range(date_from, date_to)
    days = get_historical_heatmap(
        date_from=start,
        date_to=end,
        space_id=space_id,
    )
    return success({"space_id": space_id, "days": days})
