"""Contact management tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient


def get_contact_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_contacts",
            description="Search contacts by name, phone, or email.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (name, phone, or email)"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        types.Tool(
            name="get_contact",
            description="Get a contact by ID with all custom fields.",
            inputSchema={
                "type": "object",
                "required": ["contact_id"],
                "properties": {"contact_id": {"type": "integer"}},
            },
        ),
        types.Tool(
            name="create_contact",
            description="Create a new contact with name, phone, and email.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Contact full name"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "email": {"type": "string", "description": "Email address"},
                },
            },
        ),
        types.Tool(
            name="update_contact",
            description="Update fields on an existing contact.",
            inputSchema={
                "type": "object",
                "required": ["contact_id", "fields"],
                "properties": {
                    "contact_id": {"type": "integer"},
                    "fields": {"type": "object", "description": "Fields to update"},
                },
            },
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
