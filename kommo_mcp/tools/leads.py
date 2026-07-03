"""Lead management tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient


def get_lead_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_leads",
            description="List leads with optional filters by pipeline and stage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {"type": "integer", "description": "Filter by pipeline ID"},
                    "stage_id": {"type": "integer", "description": "Filter by stage ID"},
                    "limit": {"type": "integer", "default": 50, "description": "Max leads to return"},
                },
            },
        ),
        types.Tool(
            name="get_lead",
            description="Get a complete lead by ID with contacts, tags, and custom fields.",
            inputSchema={
                "type": "object",
                "required": ["lead_id"],
                "properties": {"lead_id": {"type": "integer", "description": "The lead ID"}},
            },
        ),
        types.Tool(
            name="create_lead",
            description="Create a new lead in Kommo.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Lead name"},
                    "price": {"type": "number", "description": "Deal value"},
                    "pipeline_id": {"type": "integer", "description": "Target pipeline ID"},
                    "stage_id": {"type": "integer", "description": "Target stage ID"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tag names"},
                    "responsible_user_id": {"type": "integer", "description": "Assigned user ID"},
                },
            },
        ),
        types.Tool(
            name="update_lead",
            description="Update fields on an existing lead.",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "fields"],
                "properties": {
                    "lead_id": {"type": "integer", "description": "The lead ID"},
                    "fields": {"type": "object", "description": "Fields to update"},
                },
            },
        ),
        types.Tool(
            name="delete_lead",
            description="Delete (soft-delete) a lead.",
            inputSchema={
                "type": "object",
                "required": ["lead_id"],
                "properties": {"lead_id": {"type": "integer", "description": "The lead ID"}},
            },
        ),
        types.Tool(
            name="move_lead_stage",
            description="Move a lead to a different pipeline stage.",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "stage_id"],
                "properties": {
                    "lead_id": {"type": "integer", "description": "The lead ID"},
                    "stage_id": {"type": "integer", "description": "Target stage ID"},
                    "pipeline_id": {"type": "integer", "description": "Target pipeline ID (optional if same pipeline)"},
                },
            },
        ),
        types.Tool(
            name="bulk_update_leads",
            description="Bulk update multiple leads in one request.",
            inputSchema={
                "type": "object",
                "required": ["leads_updates"],
                "properties": {
                    "leads_updates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "fields": {"type": "object"},
                            },
                            "required": ["id", "fields"],
                        },
                        "description": "Array of {id, fields} objects",
                    }
                },
            },
        ),
        types.Tool(
            name="create_lead_complex",
            description="Create a lead with associated contact and company in one call.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Lead name"},
                    "pipeline_id": {"type": "integer"},
                    "stage_id": {"type": "integer"},
                    "contact_name": {"type": "string", "description": "Contact full name"},
                    "contact_phone": {"type": "string", "description": "Contact phone number"},
                    "contact_email": {"type": "string", "description": "Contact email"},
                    "company_name": {"type": "string", "description": "Company name"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        types.Tool(
            name="add_tag",
            description="Add a tag to a lead (creates the tag if it doesn't exist).",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "tag_name"],
                "properties": {
                    "lead_id": {"type": "integer"},
                    "tag_name": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="remove_tag",
            description="Remove a tag from a lead.",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "tag_name"],
                "properties": {
                    "lead_id": {"type": "integer"},
                    "tag_name": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="list_tags",
            description="List all available tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "default": "lead", "description": "Entity type (lead, contact, company)"},
                },
            },
        ),
        types.Tool(
            name="create_task",
            description="Create a task associated with a lead.",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "text", "due_date"],
                "properties": {
                    "lead_id": {"type": "integer"},
                    "text": {"type": "string", "description": "Task description"},
                    "due_date": {"type": "integer", "description": "Due date as Unix timestamp"},
                    "responsible_user_id": {"type": "integer"},
                },
            },
        ),
        types.Tool(
            name="list_tasks",
            description="List tasks, optionally filtered by lead.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "filter_overdue": {"type": "boolean", "default": False},
                },
            },
        ),
        types.Tool(
            name="add_note",
            description="Add a text note to a lead.",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "text"],
                "properties": {
                    "lead_id": {"type": "integer"},
                    "text": {"type": "string", "description": "Note content"},
                },
            },
        ),
        types.Tool(
            name="send_chat_message",
            description="Send a chat message to a lead's active conversation.",
            inputSchema={
                "type": "object",
                "required": ["lead_id", "text"],
                "properties": {
                    "lead_id": {"type": "integer"},
                    "text": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="list_chat_templates",
            description="List available chat message templates.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def handle_lead_tool(client: KommoClient, name: str, args: dict[str, Any]) -> Any | None:
    """Handle lead-related tool calls."""
    if name == "list_leads":
        return await client.list_leads(**args)
    if name == "get_lead":
        return await client.get_lead(args["lead_id"])
    if name == "create_lead":
        return await client.create_lead(**args)
    if name == "update_lead":
        return await client.update_lead(args["lead_id"], args["fields"])
    if name == "delete_lead":
        return await client.delete_lead(args["lead_id"])
    if name == "move_lead_stage":
        return await client.move_lead_stage(
            args["lead_id"], args["stage_id"], args.get("pipeline_id")
        )
    if name == "bulk_update_leads":
        return await client.bulk_update_leads(args["leads_updates"])
    if name == "create_lead_complex":
        return await client.create_lead_complex(**args)
    if name == "add_tag":
        return await client.add_tag(args["lead_id"], args["tag_name"])
    if name == "remove_tag":
        return await client.remove_tag(args["lead_id"], args["tag_name"])
    if name == "list_tags":
        return await client.list_tags(args.get("entity_type", "lead"))
    if name == "create_task":
        return await client.create_task(
            args["lead_id"], args["text"], args["due_date"], args.get("responsible_user_id")
        )
    if name == "list_tasks":
        return await client.list_tasks(args.get("lead_id"), args.get("filter_overdue", False))
    if name == "add_note":
        return await client.add_note(args["lead_id"], args["text"])
    if name == "send_chat_message":
        return await client.send_chat_message(args["lead_id"], args["text"])
    if name == "list_chat_templates":
        return await client.list_chat_templates()
    return None
