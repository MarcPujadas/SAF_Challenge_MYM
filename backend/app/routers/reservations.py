from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.common import success
from app.services.reservation_service import (
    cancel_reservation as cancel_reservation_service,
    create_reservation as create_reservation_service,
    list_user_reservations,
)


router = APIRouter(prefix="/api/v1")


class ReservationCreate(BaseModel):
    user_id: str
    space_id: str
    date: str
    start: str
    end: str


@router.post("/reservations")
def create_reservation(payload: ReservationCreate) -> dict[str, Any]:
    return success(
        create_reservation_service(
            payload.user_id,
            payload.space_id,
            payload.date,
            payload.start,
            payload.end,
        )
    )


@router.get("/reservations")
def get_reservations(user_id: str = Query(...)) -> dict[str, Any]:
    return success(list_user_reservations(user_id))


@router.delete("/reservations/{reservation_id}")
def cancel_reservation(reservation_id: str) -> dict[str, Any]:
    return success(cancel_reservation_service(reservation_id))
