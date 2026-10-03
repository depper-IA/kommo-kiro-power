"""Every tool declares an object outputSchema and returns matching structuredContent."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import jsonschema
import mcp.types as types
import pytest

import kommo_mcp.mcp_server as mcp_server
from kommo_mcp import kommo_client
from kommo_mcp.kommo_client import KommoClient
from kommo_mcp.tools import get_tool_definitions

TOOLS = {t.name: t for t in get_tool_definitions()}

LEAD = {
    "id": 101,
    "name": "Acme deal",
    "price": 5000,
    "responsible_user_id": 7,
    "group_id": 0,
    "status_id": 142,
    "pipeline_id": 9,
    "loss_reason_id": None,
    "created_by": 7,
    "updated_by": 7,
    "created_at": 1767225600,
    "updated_at": 1767229200,
    "closed_at": None,
    "closest_task_at": None,
    "is_deleted": False,
    "custom_fields_values": None,
    "score": None,
    "account_id": 555,
    "labor_cost": None,
    "_links": {"self": {"href": "https://x.kommo.com/api/v4/leads/101"}},
    "_embedded": {"tags": [{"id": 3, "name": "vip", "color": None}], "companies": []},
}
LEAD_MIN = {"id": 101, "name": "Acme deal", "updated_at": 1767229200, "request_id": "0"}
CONTACT = {
    "id": 201,
    "name": "Jane Doe",
    "first_name": "Jane",
    "last_name": "Doe",
    "responsible_user_id": 7,
    "group_id": 0,
    "created_by": 7,
    "updated_by": 7,
    "created_at": 1767225600,
    "updated_at": 1767229200,
    "closest_task_at": None,
    "custom_fields_values": [
        {
            "field_id": 1,
            "field_name": "Phone",
            "field_code": "PHONE",
            "field_type": "multitext",
            "values": [{"value": "+15550001111", "enum_id": 5, "enum_code": "WORK"}],
        }
    ],
    "account_id": 555,
    "_embedded": {"tags": [], "companies": []},
}
COMPANY = {"id": 301, "name": "Acme Inc", "responsible_user_id": 7, "created_at": 1767225600}
STAGE = {
    "id": 142,
    "name": "Qualified",
    "sort": 20,
    "is_editable": True,
    "pipeline_id": 9,
    "type": 0,
    "color": "#fffeb2",
    "account_id": 555,
}
PIPELINE = {
    "id": 9,
    "name": "Sales",
    "sort": 1,
    "is_main": True,
    "is_unsorted_on": False,
    "is_archive": False,
    "account_id": 555,
    "_embedded": {"statuses": [STAGE]},
}
TASK = {
    "id": 401,
    "created_by": 7,
    "updated_by": 7,
    "created_at": 1767225600,
    "updated_at": 1767225600,
    "responsible_user_id": 7,
    "group_id": 0,
    "entity_id": 101,
    "entity_type": "leads",
    "duration": 0,
    "is_completed": False,
    "task_type_id": 1,
    "text": "Call back",
    "result": [],
    "complete_till": 1767312000,
    "account_id": 555,
}
NOTE = {
    "id": 501,
    "entity_id": 101,
    "created_by": 7,
    "updated_by": 7,
    "created_at": 1767225600,
    "updated_at": 1767225600,
    "responsible_user_id": 7,
    "group_id": 0,
    "note_type": "common",
    "params": {"text": "Spoke with customer"},
    "account_id": 555,
}
TAG = {"id": 3, "name": "vip", "color": None}
FIELD = {
    "id": 601,
    "name": "Source",
    "type": "select",
    "account_id": 555,
    "code": None,
    "sort": 510,
    "is_api_only": False,
    "enums": [{"id": 1, "value": "Web", "sort": 0}],
    "group_id": None,
    "required_statuses": [],
    "is_deletable": True,
    "is_predefined": False,
    "entity_type": "leads",
    "remind": None,
}
TEMPLATE = {"id": 701, "name": "Welcome", "content": "Hi!", "type": "whatsapp", "status": "approved"}
TALK = {"talk_id": 801, "chat_id": "c1", "contact_id": 201, "entity_id": 101, "entity_type": "lead", "is_in_work": True}


def emb(key: str, items: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {"_page": 1, "_links": {"self": {"href": "x"}}, "_embedded": {key: items}, **extra}


def respond(method: str, endpoint: str, body: Any) -> Any:
    """Realistic Kommo API v4 bodies, keyed by method and endpoint."""
    if method == "GET":
        if endpoint == "/leads":
            return emb("leads", [LEAD])
        if endpoint == "/leads/tags":
            return emb("tags", [TAG])
        if endpoint == "/leads/pipelines":
            return emb("pipelines", [PIPELINE])
        if endpoint.endswith("/statuses"):
            return emb("statuses", [STAGE])
        if endpoint.endswith("/custom_fields"):
            return emb("custom_fields", [FIELD])
        if endpoint in ("/contacts/tags", "/companies/tags"):
            return emb("tags", [TAG])
        if endpoint == "/contacts":
            return emb("contacts", [CONTACT])
        if endpoint == "/companies":
            return emb("companies", [COMPANY])
        if endpoint == "/tasks":
            return emb("tasks", [TASK])
        if endpoint == "/chats/templates":
            return emb("chat_templates", [TEMPLATE])
        if endpoint == "/talks":
            return emb("talks", [TALK])
        if endpoint.startswith("/leads/"):
            return LEAD
        if endpoint.startswith("/contacts/"):
            return CONTACT
    if method == "POST":
        created = {
            "/leads": ("leads", LEAD_MIN),
            "/leads/tags": ("tags", TAG),
            "/contacts": ("contacts", {"id": 201, "name": "Jane Doe", "request_id": "0"}),
            "/companies": ("companies", {"id": 301, "name": "Acme Inc", "request_id": "0"}),
            "/tasks": ("tasks", TASK),
            "/leads/pipelines": ("pipelines", {"id": 9, "name": "Sales", "sort": 99}),
            "/leads/custom_fields": ("custom_fields", FIELD),
        }
        if endpoint == "/leads/complex":
            return [{"id": 101, "contact_id": 201, "company_id": 301, "request_id": ["0"], "merged": False}]
        if endpoint in created:
            key, item = created[endpoint]
            return emb(key, [item])
        if endpoint.endswith("/notes"):
            return emb("notes", [NOTE])
        if endpoint.endswith("/statuses"):
            return emb("statuses", [STAGE])
        if endpoint.endswith("/send_message"):
            return {"success": True}
    if method == "PATCH":
        if endpoint == "/leads":
            return emb("leads", [LEAD_MIN, {**LEAD_MIN, "id": 102}], _total_items=2)
        if endpoint.startswith("/leads/pipelines/") and "/statuses/" in endpoint:
            return STAGE
        if endpoint.startswith("/leads/pipelines/"):
            return {k: v for k, v in PIPELINE.items() if k != "_embedded"}
        if endpoint.startswith("/leads/"):
            return LEAD_MIN
        if endpoint.startswith("/contacts/"):
            return {"id": 201, "name": "Jane Doe", "updated_at": 1767229200}
    raise AssertionError(f"unrouted {method} {endpoint}")


class FakeKommo(KommoClient):
    def __init__(self) -> None:
        super().__init__()

    async def get(self, endpoint: str, **kwargs: Any) -> Any:
        return respond("GET", endpoint, None)

    async def post(self, endpoint: str, json: Any, **kwargs: Any) -> Any:
        return respond("POST", endpoint, json)

    async def patch(self, endpoint: str, json: Any, **kwargs: Any) -> Any:
        return respond("PATCH", endpoint, json)


class BrokenKommo(KommoClient):
    def __init__(self) -> None:
        super().__init__()

    async def get(self, endpoint: str, **kwargs: Any) -> Any:
        raise ValueError("HTTP 404 GET /leads/1: not found")


CASES: list[tuple[str, dict[str, Any]]] = [
    ("list_leads", {"limit": 10}),
    ("get_lead", {"lead_id": 101}),
    ("create_lead", {"name": "Acme deal"}),
    ("update_lead", {"lead_id": 101, "fields": {"name": "Acme deal"}}),
    ("delete_lead", {"lead_id": 101}),
    ("move_lead_stage", {"lead_id": 101, "stage_id": 142}),
    ("bulk_update_leads", {"leads_updates": [{"id": 101, "fields": {"price": 1}}]}),
    ("create_lead_complex", {"name": "Acme deal", "contact_name": "Jane"}),
    ("add_tag", {"lead_id": 101, "tag_name": "vip"}),
    ("remove_tag", {"lead_id": 101, "tag_name": "vip"}),
    ("list_tags", {}),
    ("list_tags", {"entity_type": "contacts"}),
    ("create_task", {"lead_id": 101, "text": "Call back", "due_date": 1767312000}),
    ("list_tasks", {}),
    ("list_tasks", {"page": 1, "limit": 10}),
    ("add_note", {"lead_id": 101, "text": "Spoke with customer"}),
    ("send_chat_message", {"lead_id": 101, "text": "hi"}),
    ("list_chat_templates", {}),
    ("list_contacts", {}),
    ("list_contacts", {"page": 1}),
    ("get_contact", {"contact_id": 201}),
    ("create_contact", {"name": "Jane Doe"}),
    ("update_contact", {"contact_id": 201, "fields": {"name": "Jane Doe"}}),
    ("list_pipelines", {}),
    ("create_pipeline", {"name": "Sales"}),
    ("update_pipeline", {"pipeline_id": 9, "name": "Sales"}),
    ("list_stages", {"pipeline_id": 9}),
    ("create_stage", {"pipeline_id": 9, "name": "Qualified"}),
    ("update_stage", {"pipeline_id": 9, "stage_id": 142, "name": "Qualified"}),
    ("list_custom_fields", {}),
    ("create_custom_field", {"entity_type": "leads", "field_type": "select", "name": "Source"}),
    ("create_company", {"name": "Acme Inc"}),
    ("list_companies", {}),
    ("list_companies", {"page": 1}),
]


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    kommo_client._cache.clear()


def _call(client_cls: type[KommoClient], name: str, args: dict[str, Any]) -> types.CallToolResult:
    mcp_server.KommoClient = client_cls  # type: ignore[misc]
    app = mcp_server.create_app()
    req = types.CallToolRequest(
        method="tools/call", params=types.CallToolRequestParams(name=name, arguments=args)
    )
    return asyncio.run(app.request_handlers[types.CallToolRequest](req)).root


@pytest.fixture(autouse=True)
def _restore_client() -> Any:
    original = mcp_server.KommoClient
    yield
    mcp_server.KommoClient = original


def test_cases_cover_every_tool() -> None:
    assert {name for name, _ in CASES} == set(TOOLS)


@pytest.mark.parametrize("tool", TOOLS.values(), ids=lambda t: t.name)
def test_every_tool_has_object_output_schema(tool: types.Tool) -> None:
    schema = tool.outputSchema
    assert schema is not None, "missing outputSchema"
    assert schema["type"] == "object"
    assert schema.get("additionalProperties", True) is not False
    assert (schema.get("description") or "").strip()
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(("name", "args"), CASES, ids=lambda v: v if isinstance(v, str) else "")
def test_structured_content_matches_schema_and_text_is_unchanged(
    name: str, args: dict[str, Any]
) -> None:
    result = _call(FakeKommo, name, args)
    assert result.isError is False, result.content
    assert result.structuredContent is not None
    jsonschema.validate(result.structuredContent, TOOLS[name].outputSchema)

    text = result.content[0].text
    raw = json.loads(text)
    assert text == json.dumps(raw, ensure_ascii=False, indent=2)
    expected = {"items": raw} if isinstance(raw, list) else raw
    assert result.structuredContent == expected


def test_plain_list_is_wrapped_in_items() -> None:
    result = _call(FakeKommo, "list_leads", {})
    assert result.structuredContent == {"items": [LEAD]}


def test_paginated_dict_keeps_its_shape() -> None:
    result = _call(FakeKommo, "list_tasks", {"page": 1, "limit": 10})
    assert result.structuredContent == {
        "items": [TASK],
        "page": 1,
        "limit": 10,
        "has_next": False,
    }


def test_text_is_byte_identical_to_legacy_dump() -> None:
    result = _call(FakeKommo, "get_lead", {"lead_id": 101})
    assert result.content[0].text == json.dumps(LEAD, ensure_ascii=False, indent=2)


def test_exception_returns_is_error_with_message() -> None:
    result = _call(BrokenKommo, "get_lead", {"lead_id": 1})
    assert result.isError is True
    assert result.content[0].text == "Error: HTTP 404 GET /leads/1: not found"


def test_unknown_tool_is_error() -> None:
    result = _call(FakeKommo, "nope", {})
    assert result.isError is True
    assert "Tool not found" in result.content[0].text
