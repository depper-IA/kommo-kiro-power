"""create_lead_complex and send_chat_message must follow the documented Kommo API.

Response shapes come from the Kommo reference:
- POST /api/v4/leads/complex returns a bare array of {id, contact_id, company_id, request_id, merged}.
- GET /api/v4/talks filters by filter[entity_id][] + filter[entity_type]; talks expose talk_id.
- POST /api/v4/talks/{talk_id}/send_message takes {"text": ...}.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kommo_mcp.kommo_client import KommoClient

COMPLEX_RESPONSE = [
    {"id": 9774766, "contact_id": 12117258, "company_id": 12117260, "request_id": ["0"], "merged": False}
]


class FakeClient(KommoClient):
    def __init__(self, talks: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self.calls: list[tuple[str, str, Any]] = []
        self.talks = talks if talks is not None else []

    async def get(self, endpoint: str, **kwargs: Any) -> Any:
        self.calls.append(("GET", endpoint, kwargs.get("params")))
        if endpoint == "/talks":
            return {"_embedded": {"talks": self.talks}} if self.talks else {}
        return {}

    async def post(self, endpoint: str, json: Any, **kwargs: Any) -> Any:
        self.calls.append(("POST", endpoint, json))
        if endpoint == "/leads/complex":
            return COMPLEX_RESPONSE
        return {"success": True}


def test_create_lead_complex_returns_first_item_of_array_response() -> None:
    client = FakeClient()
    result = asyncio.run(client.create_lead_complex("Deal", contact_name="Jane"))
    assert result == COMPLEX_RESPONSE[0]


def test_send_chat_message_filters_talks_by_lead_entity() -> None:
    client = FakeClient(talks=[{"talk_id": 801, "entity_id": 42, "entity_type": "lead"}])
    asyncio.run(client.send_chat_message(42, "Hello"))
    method, endpoint, params = client.calls[0]
    assert (method, endpoint) == ("GET", "/talks")
    assert params["filter[entity_id][]"] == 42
    assert params["filter[entity_type]"] == "leads"
    assert "filter[lead_id]" not in params


def test_send_chat_message_posts_to_send_message_with_talk_id() -> None:
    client = FakeClient(talks=[{"talk_id": 801, "entity_id": 42, "entity_type": "lead"}])
    result = asyncio.run(client.send_chat_message(42, "Hello"))
    assert client.calls[-1] == ("POST", "/talks/801/send_message", {"text": "Hello"})
    assert result == {"success": True}


def test_send_chat_message_refuses_talk_of_another_lead() -> None:
    client = FakeClient(talks=[{"talk_id": 801, "entity_id": 7, "entity_type": "lead"}])
    with pytest.raises(ValueError, match="No active conversation"):
        asyncio.run(client.send_chat_message(42, "Hello"))
    assert not [c for c in client.calls if c[0] == "POST"]


def test_send_chat_message_without_talks_raises() -> None:
    client = FakeClient(talks=[])
    with pytest.raises(ValueError, match="No active conversation"):
        asyncio.run(client.send_chat_message(42, "Hello"))
