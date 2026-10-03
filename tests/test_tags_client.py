"""Tag endpoints must follow Kommo API v4: /{leads|contacts|companies}/tags."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kommo_mcp.kommo_client import KommoClient


class FakeClient(KommoClient):
    """KommoClient with HTTP calls recorded instead of sent."""

    def __init__(self, existing_tags: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self.calls: list[tuple[str, str, Any]] = []
        self.existing_tags = existing_tags or []

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(("GET", endpoint, params))
        if endpoint.startswith("/leads/") and not endpoint.endswith("/tags"):
            return {"id": 1, "_embedded": {"tags": [{"id": 7, "name": "vip"}]}}
        return {"_embedded": {"tags": self.existing_tags}}

    async def post(self, endpoint: str, json: Any = None) -> dict[str, Any]:
        self.calls.append(("POST", endpoint, json))
        return {"_embedded": {"tags": [{"id": 99, "name": json[0]["name"]}]}}

    async def patch(self, endpoint: str, json: Any = None) -> dict[str, Any]:
        self.calls.append(("PATCH", endpoint, json))
        return {"id": 1}


@pytest.mark.parametrize(
    ("entity_type", "path"),
    [
        ("lead", "/leads/tags"),
        ("leads", "/leads/tags"),
        ("contact", "/contacts/tags"),
        ("contacts", "/contacts/tags"),
        ("company", "/companies/tags"),
        ("companies", "/companies/tags"),
    ],
)
def test_list_tags_uses_plural_entity_path(entity_type: str, path: str) -> None:
    client = FakeClient()
    asyncio.run(client.list_tags(entity_type))
    assert client.calls[0][:2] == ("GET", path)


def test_list_tags_rejects_unknown_entity_type() -> None:
    with pytest.raises(ValueError):
        asyncio.run(FakeClient().list_tags("deals"))


def test_add_tag_looks_up_by_name_on_leads_tags() -> None:
    client = FakeClient(existing_tags=[{"id": 5, "name": "hot"}])
    asyncio.run(client.add_tag(1, "hot"))
    method, endpoint, params = client.calls[0]
    assert (method, endpoint) == ("GET", "/leads/tags")
    assert params["filter[name]"] == "hot"
    assert not any(c[0] == "POST" for c in client.calls)


def test_add_tag_creates_missing_tag_on_leads_tags() -> None:
    client = FakeClient(existing_tags=[])
    asyncio.run(client.add_tag(1, "new"))
    assert ("POST", "/leads/tags", [{"name": "new"}]) in client.calls


def test_remove_tag_never_creates_a_tag() -> None:
    client = FakeClient(existing_tags=[])
    asyncio.run(client.remove_tag(1, "missing"))
    assert not any(c[0] == "POST" for c in client.calls)
