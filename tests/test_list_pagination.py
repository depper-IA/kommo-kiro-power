"""list_contacts / list_companies / list_tasks must support Kommo page/limit pagination."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kommo_mcp.kommo_client import KommoClient
from kommo_mcp.tools import get_tool_definitions, handle_tool_call


class FakeClient(KommoClient):
    def __init__(self, response: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.calls: list[tuple[str, Any]] = []
        self.response = response if response is not None else {}

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((endpoint, kwargs.get("params")))
        return self.response


CASES = [
    ("list_contacts", "/contacts", "contacts"),
    ("list_companies", "/companies", "companies"),
    ("list_tasks", "/tasks", "tasks"),
]


def _page_response(key: str, has_next: bool) -> dict[str, Any]:
    body: dict[str, Any] = {"_page": 2, "_embedded": {key: [{"id": 1}, {"id": 2}]}}
    body["_links"] = {"self": {"href": "x"}}
    if has_next:
        body["_links"]["next"] = {"href": "https://x.kommo.com/api/v4/y?page=3"}
    return body


@pytest.mark.parametrize(("method", "endpoint", "key"), CASES)
def test_default_call_still_returns_plain_list(method: str, endpoint: str, key: str) -> None:
    client = FakeClient({"_embedded": {key: [{"id": 1}]}})
    result = asyncio.run(getattr(client, method)())
    assert result == [{"id": 1}]
    assert "page" not in (client.calls[0][1] or {})


@pytest.mark.parametrize(("method", "endpoint", "key"), CASES)
def test_page_is_sent_and_envelope_reports_next(method: str, endpoint: str, key: str) -> None:
    client = FakeClient(_page_response(key, has_next=True))
    result = asyncio.run(getattr(client, method)(limit=250, page=2))
    ep, params = client.calls[0]
    assert ep == endpoint
    assert params["page"] == 2
    assert params["limit"] == 250
    assert result == {"items": [{"id": 1}, {"id": 2}], "page": 2, "limit": 250, "has_next": True}


@pytest.mark.parametrize(("method", "endpoint", "key"), CASES)
def test_last_page_has_no_next(method: str, endpoint: str, key: str) -> None:
    client = FakeClient(_page_response(key, has_next=False))
    result = asyncio.run(getattr(client, method)(page=2))
    assert result["has_next"] is False


@pytest.mark.parametrize(("method", "endpoint", "key"), CASES)
def test_empty_page_returns_empty_items(method: str, endpoint: str, key: str) -> None:
    client = FakeClient({})  # Kommo answers 204 (parsed as {}) past the last page
    result = asyncio.run(getattr(client, method)(page=9))
    assert result == {"items": [], "page": 9, "limit": 50, "has_next": False}


@pytest.mark.parametrize(("method", "endpoint", "key"), CASES)
def test_limit_capped_at_250(method: str, endpoint: str, key: str) -> None:
    client = FakeClient({})
    asyncio.run(getattr(client, method)(limit=1000, page=1))
    assert client.calls[0][1]["limit"] == 250


@pytest.mark.parametrize(("method", "endpoint", "key"), CASES)
def test_page_below_one_rejected(method: str, endpoint: str, key: str) -> None:
    with pytest.raises(ValueError, match="page"):
        asyncio.run(getattr(FakeClient(), method)(page=0))


def test_tasks_filters_kept_with_page() -> None:
    client = FakeClient({})
    asyncio.run(client.list_tasks(lead_id=5, filter_overdue=True, page=2))
    params = client.calls[0][1]
    assert params["filter[entity_id]"] == 5
    assert params["filter[is_completed]"] == 0
    assert params["page"] == 2


def test_contacts_query_kept_with_page() -> None:
    client = FakeClient({})
    asyncio.run(client.list_contacts("Jane", page=2))
    assert client.calls[0][1]["query"] == "Jane"


@pytest.mark.parametrize(("tool", "endpoint", "key"), CASES)
def test_tool_dispatch_forwards_page(tool: str, endpoint: str, key: str) -> None:
    client = FakeClient(_page_response(key, has_next=True))
    out = asyncio.run(handle_tool_call(client, tool, {"page": 2, "limit": 10}))
    assert '"has_next": true' in out
    assert client.calls[0][1]["page"] == 2
    assert client.calls[0][1]["limit"] == 10


@pytest.mark.parametrize("tool", [c[0] for c in CASES])
def test_schema_declares_page_and_limit(tool: str) -> None:
    spec = next(t for t in get_tool_definitions() if t.name == tool)
    props = spec.inputSchema["properties"]
    assert props["page"]["type"] == "integer"
    assert props["page"]["minimum"] == 1
    assert props["limit"]["maximum"] == 250
