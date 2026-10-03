"""Lead management tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient

LEAD_ID = "Kommo lead ID (integer). Obtain it from list_leads or from the create_lead result."

CUSTOM_FIELDS_VALUES = {
    "type": "array",
    "description": (
        "Lead custom field values in Kommo API v4 format: a list of objects, each addressing a "
        "field by `field_id` (from list_custom_fields) or by system `field_code`, plus "
        "`values`: [{value}] (select-type fields also take enum_id or enum_code). "
        "Example: [{\"field_id\": 123456, \"values\": [{\"value\": \"Website\"}]}]."
    ),
    "items": {
        "type": "object",
        "required": ["values"],
        "properties": {
            "field_id": {
                "type": "integer",
                "description": "Custom field ID from list_custom_fields. Use this or field_code.",
            },
            "field_code": {
                "type": "string",
                "description": "Field system code, e.g. UTM_SOURCE. Use this or field_id.",
            },
            "values": {
                "type": "array",
                "description": "One or more values to store, each as {value} (plus enum_id/enum_code).",
                "items": {"type": "object"},
            },
        },
    },
}


def get_lead_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_leads",
            description=(
                "List leads, optionally filtered by pipeline and stage. Read-only. Returns an array "
                "of lead objects with embedded contacts and tags, up to `limit` items (follows "
                "Kommo pagination when limit exceeds 50). To fetch custom fields for one lead, "
                "use get_lead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {
                        "type": "integer",
                        "description": "Only leads in this pipeline. Get IDs from list_pipelines.",
                    },
                    "stage_id": {
                        "type": "integer",
                        "description": (
                            "Only leads in this stage. Ignored unless pipeline_id is also set. "
                            "Get IDs from list_stages."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of leads to return. Default 50.",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="List leads",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="get_lead",
            description=(
                "Fetch one lead by ID. Read-only. Returns the full lead object including embedded "
                "contacts, tags, and custom_fields_values. Use list_leads instead to browse or "
                "find lead IDs."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id"],
                "properties": {"lead_id": {"type": "integer", "description": LEAD_ID}},
            },
            annotations=types.ToolAnnotations(
                title="Get lead",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_lead",
            description=(
                "Create one lead in Kommo. Not idempotent: each call creates a new lead. Tag names "
                "that do not exist yet are created automatically. Returns the created lead object. "
                "To create the contact and company in the same call, use create_lead_complex."
            ),
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Lead name (title of the deal)."},
                    "price": {
                        "type": "number",
                        "description": "Deal value in the account currency, e.g. 1500.",
                    },
                    "pipeline_id": {
                        "type": "integer",
                        "description": (
                            "Pipeline to create the lead in. Get IDs from list_pipelines. "
                            "Omit to use the account default."
                        ),
                    },
                    "stage_id": {
                        "type": "integer",
                        "description": (
                            "Stage (status) to place the lead in. Get IDs from list_stages. "
                            "Omit for the first stage of the pipeline."
                        ),
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tag names to attach, e.g. [\"vip\", \"web\"]. Created if missing.",
                    },
                    "responsible_user_id": {
                        "type": "integer",
                        "description": "Kommo user ID to assign as owner. Omit for the default user.",
                    },
                    "custom_fields_values": CUSTOM_FIELDS_VALUES,
                },
            },
            annotations=types.ToolAnnotations(
                title="Create lead",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="update_lead",
            description=(
                "Update fields on an existing lead by sending `fields` as the body of a Kommo API v4 "
                "PATCH /leads/{id}. Returns the updated lead. Overwrites the given values; omitted "
                "fields are untouched. For a stage change prefer move_lead_stage; for several leads "
                "use bulk_update_leads."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "fields"],
                "properties": {
                    "lead_id": {"type": "integer", "description": LEAD_ID},
                    "fields": {
                        "type": "object",
                        "description": (
                            "Raw Kommo v4 lead fields to change, passed through unchanged. Common keys: "
                            "name (string), price (integer), status_id (stage ID), pipeline_id, "
                            "responsible_user_id, custom_fields_values (array of "
                            "{field_id, values: [{value}]}), _embedded.tags (full replacement list of "
                            "{id}). Example: {\"name\": \"Acme renewal\", \"price\": 2000}."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Update lead",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="delete_lead",
            description=(
                "Delete a lead. Sends PATCH /leads/{id} with is_deleted=true, so the lead is "
                "soft-deleted rather than removed through a hard-delete call. Destructive: the "
                "lead disappears from normal lists. Confirm the lead_id with get_lead first."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id"],
                "properties": {"lead_id": {"type": "integer", "description": LEAD_ID}},
            },
            annotations=types.ToolAnnotations(
                title="Delete lead",
                readOnlyHint=False,
                destructiveHint=True,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="move_lead_stage",
            description=(
                "Move a lead to another stage by setting its status_id (and optionally pipeline_id). "
                "Returns the updated lead. Use this instead of update_lead for pipeline moves. "
                "Pass pipeline_id when moving to a stage in a different pipeline."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "stage_id"],
                "properties": {
                    "lead_id": {"type": "integer", "description": LEAD_ID},
                    "stage_id": {
                        "type": "integer",
                        "description": "Target stage ID. Get IDs from list_stages.",
                    },
                    "pipeline_id": {
                        "type": "integer",
                        "description": (
                            "Target pipeline ID. Only needed when the stage belongs to a "
                            "different pipeline than the lead's current one."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Move lead to stage",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="bulk_update_leads",
            description=(
                "Update many leads in a single PATCH /leads request. Each item merges its `fields` "
                "with the lead `id` and uses the same field keys as update_lead. Returns the Kommo "
                "response for the batch. Use update_lead for a single lead."
            ),
            inputSchema={
                "type": "object",
                "required": ["leads_updates"],
                "properties": {
                    "leads_updates": {
                        "type": "array",
                        "description": (
                            "Updates to apply, one per lead. Example: "
                            "[{\"id\": 123, \"fields\": {\"status_id\": 456}}]."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer", "description": LEAD_ID},
                                "fields": {
                                    "type": "object",
                                    "description": (
                                        "Raw Kommo v4 lead fields to change for this lead "
                                        "(see update_lead)."
                                    ),
                                },
                            },
                            "required": ["id", "fields"],
                        },
                    }
                },
            },
            annotations=types.ToolAnnotations(
                title="Bulk update leads",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_lead_complex",
            description=(
                "Create a lead together with a new contact and/or company in one request "
                "(POST /leads/complex). Not idempotent; Kommo may merge a duplicate (merged=true). "
                "Returns {id, contact_id, company_id, merged}. Contact phone and email are sent as Kommo's "
                "built-in PHONE and EMAIL fields. Use create_lead if no contact or company is "
                "needed."
            ),
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Lead name (title of the deal)."},
                    "pipeline_id": {
                        "type": "integer",
                        "description": "Pipeline for the lead. Get IDs from list_pipelines.",
                    },
                    "stage_id": {
                        "type": "integer",
                        "description": "Stage for the lead. Get IDs from list_stages.",
                    },
                    "contact_name": {
                        "type": "string",
                        "description": (
                            "Name of a new contact to create. Phone and email are ignored "
                            "unless this is set."
                        ),
                    },
                    "contact_phone": {
                        "type": "string",
                        "description": "Contact phone number, e.g. +15551234567.",
                    },
                    "contact_email": {
                        "type": "string",
                        "description": "Contact email address.",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Name of a new company to create and attach.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tag names to attach to the lead. Created if missing.",
                    },
                    "custom_fields_values": CUSTOM_FIELDS_VALUES,
                },
            },
            annotations=types.ToolAnnotations(
                title="Create lead with contact and company",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="add_tag",
            description=(
                "Attach a tag to a lead by name. Creates the tag if it does not exist. Reads the "
                "lead's current tags and writes back the full list plus the new one, so existing "
                "tags are kept. Safe to repeat. Returns the updated lead. See list_tags for "
                "existing tag names."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "tag_name"],
                "properties": {
                    "lead_id": {"type": "integer", "description": LEAD_ID},
                    "tag_name": {
                        "type": "string",
                        "description": "Exact tag name (case-sensitive), e.g. \"vip\".",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Add tag to lead",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="remove_tag",
            description=(
                "Detach a tag from a lead by name. Reads the lead's tags and writes back the list "
                "without that tag; other tags are kept. The tag itself is not deleted from the "
                "account. If no tag with that name exists, nothing changes and the lead is "
                "returned as is. Safe to repeat. Returns the updated lead."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "tag_name"],
                "properties": {
                    "lead_id": {"type": "integer", "description": LEAD_ID},
                    "tag_name": {
                        "type": "string",
                        "description": "Exact tag name (case-sensitive) to detach, e.g. \"vip\".",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Remove tag from lead",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_tags",
            description=(
                "List tags defined in the account for one entity type (up to 250). Read-only. "
                "Returns tag objects with id and name. Use it to check exact tag names before "
                "add_tag or remove_tag."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["lead", "leads", "contact", "contacts", "company", "companies"],
                        "default": "lead",
                        "description": (
                            "Which tag set to list: leads, contacts or companies (singular forms "
                            "accepted). Default \"lead\"."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="List tags",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_task",
            description=(
                "Create a follow-up task (type 1) attached to a lead. Not idempotent: each call "
                "creates a new task. Returns the created task. Use list_tasks to review existing "
                "tasks and add_note for non-actionable remarks."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "text", "due_date"],
                "properties": {
                    "lead_id": {"type": "integer", "description": LEAD_ID},
                    "text": {"type": "string", "description": "Task description shown in Kommo."},
                    "due_date": {
                        "type": "integer",
                        "description": "Deadline as a Unix timestamp in seconds, e.g. 1767225600.",
                    },
                    "responsible_user_id": {
                        "type": "integer",
                        "description": "Kommo user ID responsible for the task. Omit for the default.",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Create task",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_tasks",
            description=(
                "List tasks, optionally for one lead or only overdue ones. Read-only. Returns an "
                "array (Kommo default page size unless `limit` is set, max 250); pass `page` for "
                "paginated output with a has_next flag. Overdue means deadline at or before now "
                "and not completed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "integer",
                        "description": "Only tasks attached to this lead. Omit for all tasks.",
                    },
                    "filter_overdue": {
                        "type": "boolean",
                        "default": False,
                        "description": "If true, only uncompleted tasks whose deadline has passed.",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 250,
                        "description": "Tasks per page, max 250. Omit for Kommo's default (50).",
                    },
                    "page": {
                        "type": "integer",
                        "minimum": 1,
                        "description": (
                            "1-based page number. Omit for a plain array (first page). When set, "
                            "returns {items, page, limit, has_next}; request page+1 while "
                            "has_next is true."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="List tasks",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="add_note",
            description=(
                "Add a plain text (common) note to a lead's timeline. Not idempotent: repeated calls "
                "add duplicate notes. Notes are internal and are not sent to the customer; use "
                "send_chat_message for that. Returns the created note."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "text"],
                "properties": {
                    "lead_id": {"type": "integer", "description": LEAD_ID},
                    "text": {"type": "string", "description": "Note content (plain text)."},
                },
            },
            annotations=types.ToolAnnotations(
                title="Add note to lead",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="send_chat_message",
            description=(
                "Send an outgoing chat message to the customer in a lead's conversation. Finds a "
                "conversation (talk) whose entity is this lead and posts to it; fails with an error "
                "if the lead has none. The message is delivered externally and cannot be recalled "
                "by this server, and repeated calls send duplicates. Use add_note for internal notes."
            ),
            inputSchema={
                "type": "object",
                "required": ["lead_id", "text"],
                "properties": {
                    "lead_id": {
                        "type": "integer",
                        "description": (
                            "ID of a lead that already has an active conversation. "
                            "Get it from list_leads."
                        ),
                    },
                    "text": {"type": "string", "description": "Message text sent to the customer."},
                },
            },
            annotations=types.ToolAnnotations(
                title="Send chat message",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_chat_templates",
            description=(
                "List the account's chat message templates. Read-only. Returns template objects "
                "as provided by Kommo. This server cannot send a template; it only lists them "
                "(send_chat_message sends plain text)."
            ),
            inputSchema={"type": "object", "properties": {}},
            annotations=types.ToolAnnotations(
                title="List chat templates",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
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
        return await client.list_tasks(
            args.get("lead_id"),
            args.get("filter_overdue", False),
            args.get("limit"),
            args.get("page"),
        )
    if name == "add_note":
        return await client.add_note(args["lead_id"], args["text"])
    if name == "send_chat_message":
        return await client.send_chat_message(args["lead_id"], args["text"])
    if name == "list_chat_templates":
        return await client.list_chat_templates()
    return None
