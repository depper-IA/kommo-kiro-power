"""Contact management tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient

CONTACT_ID = (
    "Kommo contact ID (integer). Obtain it from list_contacts or from the create_contact result."
)


def get_contact_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_contacts",
            description=(
                "Search or list contacts. Read-only. Returns one page of contact objects, at most "
                "`limit` (capped at 100), with no further pagination. Pass `query` to match by name, "
                "phone, or email; omit it to list recent contacts. Use get_contact for one contact's "
                "full details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Free-text search matched by Kommo against name, phone, and email, "
                            "e.g. \"Jane\" or \"+15551234567\". Omit to list without filtering."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum contacts to return. Default 50, capped at 100.",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="List contacts",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="get_contact",
            description=(
                "Fetch one contact by ID. Read-only. Returns the contact with embedded tags and "
                "custom_fields_values (phone, email, and others). Use list_contacts to find the ID."
            ),
            inputSchema={
                "type": "object",
                "required": ["contact_id"],
                "properties": {"contact_id": {"type": "integer", "description": CONTACT_ID}},
            },
            annotations=types.ToolAnnotations(
                title="Get contact",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_contact",
            description=(
                "Create one contact. Not idempotent: it does not check for duplicates, so search "
                "with list_contacts first. Phone and email are sent as Kommo's built-in PHONE and "
                "EMAIL fields (WORK values). Returns the created contact. To create a lead and "
                "contact together, use create_lead_complex."
            ),
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Contact full name."},
                    "phone": {
                        "type": "string",
                        "description": "Phone number, ideally international, e.g. +15551234567.",
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address, e.g. jane@example.com.",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Create contact",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="update_contact",
            description=(
                "Update fields on an existing contact by sending `fields` as the body of a Kommo "
                "API v4 PATCH /contacts/{id}. Returns the updated contact. Provided values "
                "overwrite existing ones; omitted fields are untouched."
            ),
            inputSchema={
                "type": "object",
                "required": ["contact_id", "fields"],
                "properties": {
                    "contact_id": {"type": "integer", "description": CONTACT_ID},
                    "fields": {
                        "type": "object",
                        "description": (
                            "Raw Kommo v4 contact fields to change, passed through unchanged. Common "
                            "keys: name, first_name, last_name, responsible_user_id, "
                            "custom_fields_values (array of {field_id, values: [{value, enum_code}]}; "
                            "field IDs from list_custom_fields). "
                            "Example: {\"name\": \"Jane Roe\"}."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Update contact",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
    ]


async def handle_contact_tool(client: KommoClient, name: str, args: dict[str, Any]) -> Any | None:
    """Handle contact-related tool calls."""
    if name == "list_contacts":
        return await client.list_contacts(args.get("query"), args.get("limit", 50))
    if name == "get_contact":
        return await client.get_contact(args["contact_id"])
    if name == "create_contact":
        return await client.create_contact(
            args["name"], args.get("phone"), args.get("email")
        )
    if name == "update_contact":
        return await client.update_contact(args["contact_id"], args["fields"])
    return None
