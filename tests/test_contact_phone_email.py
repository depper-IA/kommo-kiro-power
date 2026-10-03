"""Phone/email must be sent via Kommo system field_code, never dropped silently."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kommo_mcp.kommo_client import KommoClient, cache_invalidate


@pytest.fixture(autouse=True)
def _clear_field_cache() -> None:
    cache_invalidate("custom_fields_contacts")


class FakeClient(KommoClient):
    """KommoClient with HTTP calls recorded instead of sent."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str, Any]] = []

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("GET", endpoint, kwargs.get("params")))
        # Account with no PHONE/EMAIL custom fields listed.
        return {"_embedded": {"custom_fields": []}}

    async def post(self, endpoint: str, json: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("POST", endpoint, json))
        return {"_embedded": {"contacts": [{"id": 1}], "leads": [{"id": 2}]}}


def _posted(client: FakeClient) -> list[tuple[str, str, Any]]:
    return [c for c in client.calls if c[0] == "POST"]


def test_create_contact_sends_phone_and_email_by_field_code() -> None:
    client = FakeClient()
    asyncio.run(client.create_contact("Jane", phone="+15551234567", email="jane@example.com"))
    method, endpoint, body = _posted(client)[0]
    assert endpoint == "/contacts"
    assert body[0]["custom_fields_values"] == [
        {"field_code": "PHONE", "values": [{"value": "+15551234567", "enum_code": "WORK"}]},
        {"field_code": "EMAIL", "values": [{"value": "jane@example.com", "enum_code": "WORK"}]},
    ]


def test_create_contact_needs_no_custom_field_lookup() -> None:
    client = FakeClient()
    asyncio.run(client.create_contact("Jane", phone="+15551234567"))
    assert not [c for c in client.calls if c[0] == "GET"]


def test_create_contact_keeps_caller_custom_fields() -> None:
    client = FakeClient()
    extra = {"field_id": 77, "values": [{"value": "x"}]}
    asyncio.run(client.create_contact("Jane", email="jane@example.com", custom_fields=[extra]))
    cfv = _posted(client)[0][2][0]["custom_fields_values"]
    assert cfv[0] == extra
    assert cfv[1]["field_code"] == "EMAIL"


def test_create_contact_without_phone_email_sends_no_custom_fields() -> None:
    client = FakeClient()
    asyncio.run(client.create_contact("Jane"))
    assert "custom_fields_values" not in _posted(client)[0][2][0]


def test_create_lead_complex_sends_contact_phone_and_email_by_field_code() -> None:
    client = FakeClient()
    asyncio.run(
        client.create_lead_complex(
            "Deal",
            contact_name="Jane",
            contact_phone="+15551234567",
            contact_email="jane@example.com",
        )
    )
    method, endpoint, body = _posted(client)[0]
    assert endpoint == "/leads/complex"
    contact = body[0]["_embedded"]["contacts"][0]
    assert contact["custom_fields_values"] == [
        {"field_code": "PHONE", "values": [{"value": "+15551234567", "enum_code": "WORK"}]},
        {"field_code": "EMAIL", "values": [{"value": "jane@example.com", "enum_code": "WORK"}]},
    ]
    assert not [c for c in client.calls if c[0] == "GET"]
