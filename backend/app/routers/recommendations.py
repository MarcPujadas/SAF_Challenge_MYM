from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.common import ApiError, success
from app.services.catalog_service import supports_safi_recommendations
from app.services.recommendation_service import (
    recommend,
    recommend_service,
)
from app.services.recommendation_tracking_service import (
    save_recommendation,
    save_recommendation_action,
)
from app.services.validation import validate_date_time


router = APIRouter(prefix="/api/v1")


class RecommendationRequest(BaseModel):
    space_id: str | None = None
    service_id: str | None = None
    date: str
    preferred_start: str
    preferred_end: str


class RecommendationActionRequest(BaseModel):
    action: str


@router.post("/recommendations")
def create_recommendation(
    payload: RecommendationRequest,
) -> dict[str, Any]:
    try:
        parsed_date, start_minutes = validate_date_time(
            payload.date,
            payload.preferred_start,
        )
        _, end_minutes = validate_date_time(
            payload.date,
            payload.preferred_end,
        )
        if end_minutes <= start_minutes:
            raise ValueError("preferred_end must be later than preferred_start.")

        if payload.service_id is not None and payload.space_id is not None:
            raise ApiError(
                "INVALID_FILTER",
                "Provide either service_id or space_id, not both.",
            )
        if payload.service_id is None and payload.space_id is None:
            raise ApiError(
                "INVALID_FILTER",
                "service_id or space_id is required.",
            )

        if payload.service_id is not None:
            result = recommend_service(
                payload.service_id,
                parsed_date.isoformat(),
                payload.preferred_start,
                payload.preferred_end,
            )
            if not result.get("recommendation_available", True):
                result["recommendation_id"] = None
                return success(result)
        elif not supports_safi_recommendations(payload.space_id):
            weekday_names = (
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            )
            return success(
                {
                    "recommendation_id": None,
                    "requested_slot": {
                        "start": payload.preferred_start,
                        "occupancy_score": None,
                        "occupancy_level": "unknown",
                    },
                    "recommended_slot": None,
                    "message": (
                        "SAFi recommendations are not available "
                        "for court spaces."
                    ),
                    "confidence": "low",
                    "basis": {
                        "space_id": payload.space_id,
                        "weekday": weekday_names[parsed_date.weekday()],
                        "historical_period": None,
                    },
                    "recommendation_available": False,
                    "unavailable_reason": "unsupported_space_type",
                }
            )

        else:
            result = recommend(
                payload.space_id,
                parsed_date.isoformat(),
                payload.preferred_start,
                payload.preferred_end,
            )
    except ValueError as exc:
        raise ApiError("INVALID_TIME", str(exc)) from exc

    if result["requested_slot"]["occupancy_score"] is None:
        raise ApiError(
            "OCCUPANCY_DATA_UNAVAILABLE",
            "No hi ha dades d'ocupació disponibles per a aquesta consulta.",
            404,
        )

    recommended_slot = result["recommended_slot"]
    recommendation_id = save_recommendation(
        user_id="demo-user",
        space_id=payload.space_id,
        date=parsed_date.isoformat(),
        requested_start=result["requested_slot"]["start"],
        recommended_start=(
            recommended_slot["start"]
            if recommended_slot is not None
            else None
        ),
        requested_score=result["requested_slot"]["occupancy_score"],
        recommended_score=(
            recommended_slot["occupancy_score"]
            if recommended_slot is not None
            else None
        ),
        service_id=payload.service_id,
    )
    result["recommendation_id"] = recommendation_id
    return success(result)


@router.post("/recommendations/{recommendation_id}/action")
def register_recommendation_action(
    recommendation_id: str,
    payload: RecommendationActionRequest,
) -> dict[str, Any]:
    save_recommendation_action(recommendation_id, payload.action)
    return success(
        {"recommendation_id": recommendation_id, "action": payload.action}
    )
