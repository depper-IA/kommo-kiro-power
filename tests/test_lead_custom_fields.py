"""create_lead / create_lead_complex must expose and forward custom_fields_values."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kommo_mcp.kommo_client import KommoClient
from kommo_mcp.tools import get_tool_definitions, handle_tool_call

CFV = [
    {"field_id": 123, "values": [{"value": "Website"}]},
    {"field_code": "SOURCE", "values": [{"value": "ads", "enum_code": "X"}]},
]


class FakeClient(KommoClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str, Any]] = []

    async def post(self, endpoint: str, json: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("POST", endpoint, json))
        if endpoint == "/leads/complex":
            return [{"id": 1, "contact_id": 2, "company_id": 3, "request_id": ["0"], "merged": False}]
        return {"_embedded": {"leads": [{"id": 1}]}}


@pytest.mark.parametrize(
    ("tool", "endpoint"), [("create_lead", "/leads"), ("create_lead_complex", "/leads/complex")]
)
def test_tool_call_forwards_custom_fields_values(tool: str, endpoint: str) -> None:
    client = FakeClient()
    asyncio.run(handle_tool_call(client, tool, {"name": "Deal", "custom_fields_values": CFV}))
    _, ep, body = client.calls[0]
    assert ep == endpoint
    assert body[0]["custom_fields_values"] == CFV


@pytest.mark.parametrize("tool", ["create_lead", "create_lead_complex"])
def test_legacy_custom_fields_kwarg_still_works(tool: str) -> None:
    client = FakeClient()
    method = getattr(client, tool)
    asyncio.run(method("Deal", custom_fields=CFV))
    assert client.calls[0][2][0]["custom_fields_values"] == CFV


@pytest.mark.parametrize("tool", ["create_lead", "create_lead_complex"])
def test_no_custom_fields_means_no_key(tool: str) -> None:
    client = FakeClient()
    asyncio.run(handle_tool_call(client, tool, {"name": "Deal"}))
    assert "custom_fields_values" not in client.calls[0][2][0]


@pytest.mark.parametrize("tool", ["create_lead", "create_lead_complex"])
def test_schema_declares_custom_fields_values(tool: str) -> None:
    spec = next(t for t in get_tool_definitions() if t.name == tool)
    prop = spec.inputSchema["properties"]["custom_fields_values"]
    assert prop["type"] == "array"
    item_props = prop["items"]["properties"]
    assert {"field_id", "field_code", "values"} <= set(item_props)
    desc = prop["description"]
    assert "field_id" in desc and "field_code" in desc and "list_custom_fields" in desc
    assert "values" in prop["items"]["required"]
