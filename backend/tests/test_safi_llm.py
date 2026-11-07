import json
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient

from app import main
from app.database import database
from app.routers import safi
from app.services import llm_service


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "safi-llm.db")
    return TestClient(main.app)


def test_safi_chat_llm_uses_forecast_tool_and_returns_grounded_source(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("UTH_KEY", "test-token")
    tool_response = {
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "get_occupancy_forecast",
                    "arguments": json.dumps(
                        {
                            "service": "fitness",
                            "date": "2026-11-10",
                            "start": "18:30",
                        }
                    ),
                },
            }
        ]
    }
    final_response = {
        "content": "Aquesta franja té una ocupació històrica alta."
    }

    with make_client(tmp_path, monkeypatch) as client:
        with (
            patch.object(
                llm_service,
                "call_ornith",
                side_effect=[tool_response, final_response],
            ) as call_ornith,
            patch.object(
                llm_service,
                "get_historical_occupancy",
                return_value={
                    "occupancy_score": 90,
                    "occupancy_level": "very_high",
                    "samples": 12,
                    "start_time": "18:30",
                },
            ),
            patch.object(
                llm_service,
                "get_best_alternative",
                return_value=None,
            ),
        ):
            response = client.post(
                "/api/v1/safi/chat-llm",
                json={
                    "user_id": "demo-user",
                    "message": "Quina ocupació hi ha al fitness?",
                },
            )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data == {
        "message": "Aquesta franja té una ocupació històrica alta.",
        "sources": [
            {
                "type": "historical_occupancy",
                "space_id": "sala-fitnes-sala-cardio",
            }
        ],
        "can_answer": True,
        "provider": "uab-ornith",
    }
    assert call_ornith.call_count == 2
    assert call_ornith.call_args_list[0].args[0][1]["role"] == "user"


def test_safi_chat_llm_does_not_return_unverified_provider_text(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("UTH_KEY", "test-token")
    with make_client(tmp_path, monkeypatch) as client:
        with patch.object(
            llm_service,
            "call_ornith",
            return_value={"content": "La piscina és tranquil·la."},
        ):
            response = client.post(
                "/api/v1/safi/chat-llm",
                json={"user_id": "demo-user", "message": "Hola"},
            )

    assert response.status_code == 200
    assert response.json()["data"]["can_answer"] is False
    assert response.json()["data"]["sources"] == []
    assert response.json()["data"]["message"] == llm_service.UNKNOWN_MESSAGE


def test_safi_chat_llm_returns_unknown_when_historical_data_is_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("UTH_KEY", "test-token")
    tool_response = {
        "tool_calls": [
            {
                "id": "call-1",
                "function": {
                    "name": "get_occupancy_forecast",
                    "arguments": json.dumps(
                        {
                            "service": "fitness",
                            "date": "2026-11-10",
                            "start": "18:30",
                        }
                    ),
                },
            }
        ]
    }

    with make_client(tmp_path, monkeypatch) as client:
        with (
            patch.object(
                llm_service,
                "call_ornith",
                return_value=tool_response,
            ) as call_ornith,
            patch.object(
                llm_service,
                "get_historical_occupancy",
                return_value={
                    "occupancy_score": None,
                    "occupancy_level": "unknown",
                    "samples": 0,
                    "start_time": None,
                },
            ),
        ):
            response = client.post(
                "/api/v1/safi/chat-llm",
                json={
                    "user_id": "demo-user",
                    "message": "Quina ocupació hi ha al fitness?",
                },
            )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["can_answer"] is False
    assert data["sources"] == []
    assert data["message"] == llm_service.UNKNOWN_MESSAGE
    call_ornith.assert_called_once()


def test_missing_llm_configuration_does_not_affect_deterministic_chat(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("UTH_KEY", raising=False)
    with make_client(tmp_path, monkeypatch) as client:
        unavailable = client.post(
            "/api/v1/safi/chat-llm",
            json={"user_id": "demo-user", "message": "Pregunta"},
        )
        with patch.object(
            safi,
            "chat",
            return_value={
                "message": llm_service.UNKNOWN_MESSAGE,
                "sources": [],
                "can_answer": False,
            },
        ):
            deterministic = client.post(
                "/api/v1/safi/chat",
                json={"user_id": "demo-user", "message": "Pregunta"},
            )

    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "LLM_UNAVAILABLE"
    assert deterministic.status_code == 200
    assert deterministic.json()["success"] is True


def test_llm_timeout_returns_unavailable_without_leaking_provider_details(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("UTH_KEY", "test-token")
    with make_client(tmp_path, monkeypatch) as client:
        with patch.object(
            llm_service.httpx,
            "post",
            side_effect=httpx.TimeoutException("provider timeout"),
        ):
            response = client.post(
                "/api/v1/safi/chat-llm",
                json={"user_id": "demo-user", "message": "Pregunta"},
            )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "LLM_UNAVAILABLE"
    assert "provider timeout" not in response.text


def test_invalid_provider_tool_call_returns_llm_error(tmp_path, monkeypatch):
    monkeypatch.setenv("UTH_KEY", "test-token")
    with make_client(tmp_path, monkeypatch) as client:
        with patch.object(
            llm_service,
            "call_ornith",
            return_value={
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_occupancy_forecast",
                            "arguments": "{}",
                        }
                    }
                ]
            },
        ):
            response = client.post(
                "/api/v1/safi/chat-llm",
                json={"user_id": "demo-user", "message": "Pregunta"},
            )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_ERROR"


def test_reservations_tool_uses_user_id_from_backend_request(
    monkeypatch,
):
    result = {
        "available": True,
        "user_id": "demo-user",
        "reservations": [],
    }
    with patch.object(
        llm_service,
        "get_user_reservation_context",
        return_value=result,
    ) as get_context:
        actual = llm_service.execute_tool(
            "get_user_reservations",
            {},
            "demo-user",
        )

    assert actual is result
    get_context.assert_called_once_with(
        user_id="demo-user",
        date_from=None,
        date_to=None,
        space_id=None,
    )


def test_ornith_adapter_uses_configured_key_and_chat_completion_protocol(
    monkeypatch,
):
    monkeypatch.setenv("UTH_KEY", "test-token")
    response = Mock()
    response.json.return_value = {
        "choices": [{"message": {"content": "Resposta"}}]
    }
    messages = [{"role": "user", "content": "Pregunta"}]
    with patch.object(
        llm_service.httpx,
        "post",
        return_value=response,
    ) as post:
        message = llm_service.call_ornith(messages, llm_service.TOOLS)

    assert message == {"content": "Resposta"}
    response.raise_for_status.assert_called_once_with()
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args == (llm_service.ORNITH_ENDPOINT,)
    assert kwargs["headers"] == {"Authorization": "Bearer test-token"}
    assert kwargs["json"]["model"] == "ornith"
    assert kwargs["json"]["messages"] == messages
    assert kwargs["json"]["tools"] == llm_service.TOOLS
    assert kwargs["timeout"] == 30.0


def test_forecast_tool_rejects_court_services_without_historical_lookup():
    with patch.object(llm_service, "get_historical_occupancy") as historical:
        result = llm_service.execute_tool(
            "get_occupancy_forecast",
            {
                "service": "padel",
                "date": "2026-11-10",
                "start": "18:30",
            },
            "demo-user",
        )

    assert result["available"] is False
    assert "not available" in result["reason"]
    historical.assert_not_called()


def test_availability_tool_uses_shared_valid_slot_service():
    with patch.object(
        llm_service,
        "get_slot_availability",
        return_value={
            "start": "18:30",
            "end": "19:45",
            "available": True,
            "remaining_capacity": 1,
        },
    ) as get_slot:
        result = llm_service.execute_tool(
            "get_booking_availability",
            {
                "service": "fitness",
                "date": "2026-11-10",
                "start": "18:30",
            },
            "demo-user",
        )

    assert result["available"] is True
    get_slot.assert_called_once_with(
        "sala-fitnes-sala-cardio",
        llm_service.parse_date("2026-11-10"),
        "18:30",
        "19:45",
        include_forecast=False,
    )
