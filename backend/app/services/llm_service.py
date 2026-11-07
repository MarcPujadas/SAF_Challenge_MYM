from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

import httpx

from app.common import ApiError
from app.config.services import SERVICE_BY_ID
from app.services.availability_service import get_slot_availability
from app.services.historical_service import (
    get_historical_occupancy,
    occupancy_level,
)
from app.services.recommendation_service import (
    get_best_alternative,
    get_quietest_slot,
)
from app.services.reservation_service import get_user_reservation_context
from app.services.schedule_service import (
    minutes_to_time,
    parse_date,
    time_to_minutes,
)
from app.services.validation import WEEKDAYS_CA


ORNITH_ENDPOINT = (
    "https://dcc-llm-gw.uab.cat/uabthehack/v1/chat/completions"
)
ORNITH_MODEL = "ornith"
ORNITH_TIMEOUT_SECONDS = 30.0
UNKNOWN_MESSAGE = "No ho sé amb les dades disponibles."


class LLMUnavailableError(Exception):
    pass


class LLMProtocolError(Exception):
    pass


def _tool(name: str, description: str, properties: dict, required: list[str]):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


_SERVICE_PROPERTY = {
    "type": "string",
    "enum": list(SERVICE_BY_ID),
}
TOOLS = [
    _tool(
        "get_occupancy_forecast",
        "Consulta la previsió d'ocupació històrica d'un servei, dia i hora opcionals.",
        {
            "service": _SERVICE_PROPERTY,
            "date": {"type": "string", "format": "date"},
            "start": {"type": "string", "pattern": "^([01]\\d|2[0-3]):[0-5]\\d$"},
        },
        ["service", "date"],
    ),
    _tool(
        "get_booking_availability",
        "Consulta la disponibilitat actual d'un slot vàlid a SQLite.",
        {
            "service": _SERVICE_PROPERTY,
            "date": {"type": "string", "format": "date"},
            "start": {"type": "string", "pattern": "^([01]\\d|2[0-3]):[0-5]\\d$"},
        },
        ["service", "date", "start"],
    ),
    _tool(
        "get_user_reservations",
        "Consulta les reserves confirmades de l'usuari del request.",
        {
            "service": _SERVICE_PROPERTY,
            "date_from": {"type": "string", "format": "date"},
            "date_to": {"type": "string", "format": "date"},
        },
        [],
    ),
]


SYSTEM_PROMPT = (
    "Ets SAFi, l'assistent del Servei d'Activitat Física de la UAB. "
    "Respon en català, de manera breu. Per a qualsevol afirmació factual "
    "sobre ocupació, disponibilitat, serveis o reserves, consulta les eines "
    "i limita't als seus resultats. No dedueixis disponibilitat actual de "
    "l'ocupació històrica ni a l'inrevés. No inventis dades. Si les eines "
    "no retornen informació suficient, respon exactament que no ho saps amb "
    "les dades disponibles. No creïs ni cancel·lis reserves."
)


def _unavailable(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def _service(service_id: Any):
    if not isinstance(service_id, str):
        return None
    return SERVICE_BY_ID.get(service_id)


def get_occupancy_forecast(
    service_id: str,
    date_value: str,
    start: str | None = None,
) -> dict[str, Any]:
    service = _service(service_id)
    if service is None:
        return _unavailable("Unsupported service.")
    requested_date = parse_date(date_value)
    weekday = requested_date.weekday()
    result: dict[str, Any] = {
        "available": True,
        "service_id": service.service_id,
        "service_name": service.name,
        "space_id": service.space_id,
        "date": requested_date.isoformat(),
        "weekday": WEEKDAYS_CA[weekday],
        "forecast_type": "historical_prediction",
        "real_time": False,
    }

    try:
        if start is None:
            quietest = get_quietest_slot(service.space_id, weekday)
            if quietest is None:
                return _unavailable(
                    "No historical occupancy data available."
                )
            score = quietest["occupancy_score"]
            result["quietest_slot"] = {
                "start": quietest["start"],
                "occupancy_score": score,
                "occupancy_level": occupancy_level(score),
                "samples": quietest["samples"],
            }
            return result

        requested = get_historical_occupancy(
            space_id=service.space_id,
            weekday=weekday,
            start_time=start,
        )
    except FileNotFoundError:
        return _unavailable("No historical occupancy data available.")

    if requested["occupancy_score"] is None:
        return _unavailable("No historical occupancy data available.")

    try:
        alternative = get_best_alternative(
            space_id=service.space_id,
            weekday=weekday,
            preferred_start=start,
        )
    except FileNotFoundError:
        alternative = None
    if (
        alternative is not None
        and alternative["occupancy_score"] >= requested["occupancy_score"]
    ):
        alternative = None
    result.update(
        {
            "requested_start": start,
            "matched_start": requested["start_time"],
            "occupancy_score": requested["occupancy_score"],
            "occupancy_level": requested["occupancy_level"],
            "samples": requested["samples"],
            "better_alternative": alternative,
        }
    )
    return result


def get_booking_availability(
    service_id: str,
    date_value: str,
    start: str,
) -> dict[str, Any]:
    service = _service(service_id)
    if service is None:
        return _unavailable("Unsupported service.")
    requested_date = parse_date(date_value)
    start_minutes = time_to_minutes(start)
    end = minutes_to_time(
        start_minutes + service.slot_duration_minutes
    )
    slot = get_slot_availability(
        service.space_id,
        requested_date,
        start,
        end,
        include_forecast=False,
    )
    return {
        "available": True,
        "service_id": service.service_id,
        "service_name": service.name,
        "space_id": service.space_id,
        "date": requested_date.isoformat(),
        **slot,
        "source": "current_reservations_database",
    }


def get_user_reservations(
    user_id: str,
    service_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    space_id = None
    if service_id is not None:
        service = _service(service_id)
        if service is None:
            return _unavailable("Unsupported service.")
        space_id = service.space_id
    return get_user_reservation_context(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        space_id=space_id,
    )


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    try:
        if name == "get_occupancy_forecast":
            service_id = arguments.get("service")
            date_value = arguments.get("date")
            if not isinstance(service_id, str) or not isinstance(date_value, str):
                return _unavailable("Missing service or date.")
            start = arguments.get("start")
            if start is not None and not isinstance(start, str):
                return _unavailable("Invalid start time.")
            return get_occupancy_forecast(service_id, date_value, start)

        if name == "get_booking_availability":
            service_id = arguments.get("service")
            date_value = arguments.get("date")
            start = arguments.get("start")
            if not all(isinstance(value, str) for value in (service_id, date_value, start)):
                return _unavailable("Missing service, date or start time.")
            return get_booking_availability(service_id, date_value, start)

        if name == "get_user_reservations":
            service_id = arguments.get("service")
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")
            if service_id is not None and not isinstance(service_id, str):
                return _unavailable("Invalid service.")
            if date_from is not None and not isinstance(date_from, str):
                return _unavailable("Invalid date_from.")
            if date_to is not None and not isinstance(date_to, str):
                return _unavailable("Invalid date_to.")
            return get_user_reservations(
                user_id,
                service_id,
                date_from,
                date_to,
            )
    except ApiError as exc:
        return _unavailable(exc.message)
    return _unavailable("Unknown tool.")


def call_ornith(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("UTH_KEY")
    if not api_key:
        raise LLMUnavailableError("The LLM service is not configured.")

    body: dict[str, Any] = {
        "model": ORNITH_MODEL,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools is not None:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    try:
        response = httpx.post(
            ORNITH_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout=ORNITH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMUnavailableError("The LLM service is unavailable.") from exc

    try:
        payload = response.json()
        message = payload["choices"][0]["message"]
        if not isinstance(message, dict):
            raise TypeError("Invalid message.")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMProtocolError("The LLM response is invalid.") from exc
    return message


def _tool_source(name: str, result: dict[str, Any]) -> dict[str, Any]:
    source_type = {
        "get_occupancy_forecast": "historical_occupancy",
        "get_booking_availability": "current_reservations_database",
        "get_user_reservations": "current_reservations_database",
    }[name]
    source: dict[str, Any] = {"type": source_type}
    if result.get("space_id") is not None:
        source["space_id"] = result["space_id"]
    elif result.get("reservations"):
        source["space_ids"] = sorted(
            {item["space_id"] for item in result["reservations"]}
        )
    return source


def chat_with_ornith(message: str, user_id: str) -> dict[str, Any]:
    today = date.today()
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                f"{SYSTEM_PROMPT} Avui és {today.isoformat()} "
                f"({WEEKDAYS_CA[today.weekday()]})."
            ),
        },
        {"role": "user", "content": message},
    ]
    assistant_message = call_ornith(messages, TOOLS)
    tool_calls = assistant_message.get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        return {
            "message": UNKNOWN_MESSAGE,
            "sources": [],
            "can_answer": False,
            "provider": "uab-ornith",
        }

    messages.append(assistant_message)
    sources = []
    has_usable_data = False
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            raise LLMProtocolError("The LLM tool call is invalid.")
        call_id = tool_call.get("id")
        function = tool_call.get("function")
        if not isinstance(call_id, str) or not isinstance(function, dict):
            raise LLMProtocolError("The LLM tool call is invalid.")
        name = function.get("name")
        raw_arguments = function.get("arguments")
        if not isinstance(name, str) or not isinstance(raw_arguments, str):
            raise LLMProtocolError("The LLM tool call is invalid.")
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            arguments = {}
            name = ""
        if not isinstance(arguments, dict):
            arguments = {}
            name = ""
        result = execute_tool(name, arguments, user_id)
        if result.get("forecast_type") or result.get("source"):
            has_usable_data = True
        if name in {
            "get_occupancy_forecast",
            "get_booking_availability",
            "get_user_reservations",
        }:
            sources.append(_tool_source(name, result))
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

    if not has_usable_data:
        return {
            "message": UNKNOWN_MESSAGE,
            "sources": [],
            "can_answer": False,
            "provider": "uab-ornith",
        }

    final_message = call_ornith(messages)
    content = final_message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMProtocolError("The LLM response is empty.")
    unique_sources = list(
        {
            (
                source["type"],
                source.get("space_id"),
                tuple(source.get("space_ids", [])),
            ): source
            for source in sources
        }.values()
    )
    return {
        "message": content.strip(),
        "sources": unique_sources,
        "can_answer": True,
        "provider": "uab-ornith",
    }
