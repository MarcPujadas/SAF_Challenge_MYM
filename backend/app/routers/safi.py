from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.common import ApiError, success
from app.services.llm_service import (
    LLMProtocolError,
    LLMUnavailableError,
    chat_with_ornith,
)
from app.services.safi_service import advice, advice_service, chat


router = APIRouter(prefix="/api/v1")


class SAFiAdviceRequest(BaseModel):
    space_id: str | None = None
    service_id: str | None = None
    date: str
    start: str


class SAFiChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("/safi/advice")
def get_safi_advice(payload: SAFiAdviceRequest) -> dict[str, Any]:
    if (payload.space_id is None) == (payload.service_id is None):
        raise ApiError(
            "INVALID_FILTER",
            "Provide either service_id or space_id.",
        )
    try:
        if payload.service_id is not None:
            result = advice_service(
                payload.service_id,
                payload.date,
                payload.start,
            )
        else:
            result = advice(payload.space_id, payload.date, payload.start)
    except ValueError as exc:
        raise ApiError("INVALID_TIME", str(exc)) from exc
    return success(result)


@router.post("/safi/chat")
def chat_with_safi(payload: SAFiChatRequest) -> dict[str, Any]:
    return success(chat(payload.message))


@router.post("/safi/chat-llm")
def chat_with_safi_llm(payload: SAFiChatRequest) -> dict[str, Any]:
    try:
        result = chat_with_ornith(payload.message, payload.user_id)
    except LLMUnavailableError as exc:
        raise ApiError(
            "LLM_UNAVAILABLE",
            "SAFi LLM service is unavailable.",
            503,
        ) from exc
    except LLMProtocolError as exc:
        raise ApiError(
            "LLM_ERROR",
            "SAFi LLM returned an invalid response.",
            502,
        ) from exc
    return success(result)
