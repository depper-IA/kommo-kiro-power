"""MCP outputSchema definitions for every tool.

Kommo payloads vary per account, so every schema is permissive: key fields are
typed and described, nullable fields accept null, `additionalProperties` stays
open and `required` only lists keys that are always present.

Tools that return arrays are wrapped as {"items": [...]}. Paginated variants
(`page` argument set) keep their {items, page, limit, has_next} shape.
"""

from __future__ import annotations

from typing import Any

Schema = dict[str, Any]


def _prop(kind: str, description: str, nullable: bool = False) -> Schema:
    return {"type": [kind, "null"] if nullable else kind, "description": description}


def _int(description: str, nullable: bool = False) -> Schema:
    return _prop("integer", description, nullable)


def _str(description: str, nullable: bool = False) -> Schema:
    return _prop("string", description, nullable)


def _bool(description: str) -> Schema:
    return _prop("boolean", description)


def _obj(
    description: str, properties: dict[str, Schema] | None = None, required: tuple[str, ...] = ()
) -> Schema:
    schema: Schema = {
        "type": "object",
        "description": description,
        "properties": properties or {},
        "additionalProperties": True,
    }
    if required:
        schema["required"] = list(required)
    return schema


def _array(description: str, items: Schema | None = None, nullable: bool = False) -> Schema:
    schema: Schema = {"type": ["array", "null"] if nullable else "array", "description": description}
    if items is not None:
        schema["items"] = items
    return schema


_LINKS = _obj("HAL links as returned by Kommo (self, next, ...).")
_CUSTOM_FIELDS = _array(
    "Custom field values in Kommo format: objects with field_id, field_code and values.",
    _obj("One custom field with its values."),
    nullable=True,
)
_STAMPS: dict[str, Schema] = {
    "created_at": _int("Creation time, Unix seconds.", True),
    "updated_at": _int("Last update time, Unix seconds.", True),
    "created_by": _int("ID of the user who created it.", True),
    "updated_by": _int("ID of the user who last updated it.", True),
}
_OWNER: dict[str, Schema] = {
    "responsible_user_id": _int("ID of the responsible Kommo user.", True),
    "group_id": _int("ID of the responsible user's group.", True),
    "account_id": _int("Kommo account ID.", True),
}


def _embedded(description: str, **collections: Schema) -> Schema:
    return _obj(description, {k: _array(f"Embedded {k}.", v) for k, v in collections.items()})


TAG = _obj(
    "A Kommo tag.",
    {
        "id": _int("Tag ID."),
        "name": _str("Tag name.", True),
        "color": _str("Tag color, or null.", True),
    },
)
STAGE = _obj(
    "A pipeline stage (status).",
    {
        "id": _int("Stage ID."),
        "name": _str("Stage name.", True),
        "sort": _int("Sort order.", True),
        "is_editable": _prop("boolean", "Whether the stage can be edited.", True),
        "pipeline_id": _int("Parent pipeline ID.", True),
        "color": _str("Hex color.", True),
        "type": _int("0 for regular stages, 1 for unsorted.", True),
        "account_id": _int("Kommo account ID.", True),
    },
)
PIPELINE = _obj(
    "A sales pipeline.",
    {
        "id": _int("Pipeline ID."),
        "name": _str("Pipeline name.", True),
        "sort": _int("Sort order.", True),
        "is_main": _prop("boolean", "Whether this is the main pipeline.", True),
        "is_unsorted_on": _prop("boolean", "Whether the Incoming leads stage is enabled.", True),
        "is_archive": _prop("boolean", "Whether the pipeline is archived.", True),
        "account_id": _int("Kommo account ID.", True),
        "_embedded": _embedded("Embedded resources.", statuses=STAGE),
    },
)
LEAD = _obj(
    "A Kommo lead. Fields beyond those listed (embedded contacts, companies, etc.) may appear. "
    "Write operations may return only id, name, updated_at and request_id.",
    {
        "id": _int("Lead ID."),
        "name": _str("Lead name.", True),
        "price": _int("Lead budget.", True),
        "status_id": _int("Current stage ID.", True),
        "pipeline_id": _int("Pipeline ID.", True),
        "loss_reason_id": _int("Loss reason ID, or null.", True),
        "closed_at": _int("Closing time, Unix seconds, or null.", True),
        "closest_task_at": _int("Next task deadline, Unix seconds, or null.", True),
        "is_deleted": _prop("boolean", "Whether the lead is deleted.", True),
        "custom_fields_values": _CUSTOM_FIELDS,
        "_links": _LINKS,
        "_embedded": _embedded("Embedded tags, contacts and companies.", tags=TAG),
        **_STAMPS,
        **_OWNER,
    },
)
CONTACT = _obj(
    "A Kommo contact. Phone and email live in custom_fields_values.",
    {
        "id": _int("Contact ID."),
        "name": _str("Full name.", True),
        "first_name": _str("First name.", True),
        "last_name": _str("Last name.", True),
        "closest_task_at": _int("Next task deadline, Unix seconds, or null.", True),
        "custom_fields_values": _CUSTOM_FIELDS,
        "_links": _LINKS,
        "_embedded": _embedded("Embedded tags and companies.", tags=TAG),
        **_STAMPS,
        **_OWNER,
    },
)
COMPANY = _obj(
    "A Kommo company.",
    {
        "id": _int("Company ID."),
        "name": _str("Company name.", True),
        "closest_task_at": _int("Next task deadline, Unix seconds, or null.", True),
        "custom_fields_values": _CUSTOM_FIELDS,
        "_links": _LINKS,
        "_embedded": _embedded("Embedded tags and leads.", tags=TAG),
        **_STAMPS,
        **_OWNER,
    },
)
TASK = _obj(
    "A Kommo task.",
    {
        "id": _int("Task ID."),
        "text": _str("Task description.", True),
        "entity_id": _int("ID of the entity the task is attached to.", True),
        "entity_type": _str("Entity type, e.g. leads.", True),
        "task_type_id": _int("Task type ID (1 is follow-up).", True),
        "complete_till": _int("Deadline, Unix seconds.", True),
        "is_completed": _prop("boolean", "Whether the task is completed.", True),
        "duration": _int("Duration in seconds.", True),
        "result": {"description": "Completion result (object or array), may be empty."},
        "_links": _LINKS,
        **_STAMPS,
        **_OWNER,
    },
)
NOTE = _obj(
    "A timeline note.",
    {
        "id": _int("Note ID."),
        "entity_id": _int("ID of the entity the note is attached to.", True),
        "note_type": _str("Note type, e.g. common.", True),
        "params": _obj("Note parameters, e.g. {text}."),
        "_links": _LINKS,
        **_STAMPS,
        **_OWNER,
    },
)
CUSTOM_FIELD = _obj(
    "A custom field definition.",
    {
        "id": _int("Field ID."),
        "name": _str("Field name.", True),
        "type": _str("Field type, e.g. text, select.", True),
        "code": _str("System field code, or null.", True),
        "sort": _int("Sort order.", True),
        "entity_type": _str("Entity the field belongs to.", True),
        "is_api_only": _prop("boolean", "Whether the field is API only.", True),
        "enums": _array("Options for select-like fields.", _obj("One option."), nullable=True),
        "_links": _LINKS,
        "account_id": _int("Kommo account ID.", True),
    },
)
CHAT_TEMPLATE = _obj(
    "A chat message template.",
    {
        "id": _int("Template ID."),
        "name": _str("Template name.", True),
        "content": _str("Template text.", True),
        "type": _str("Channel type.", True),
        "status": _str("Approval status.", True),
    },
)


def single(entity: Schema, description: str) -> Schema:
    """Output of a tool that returns one entity object."""
    return {**entity, "description": description}


def listing(entity: Schema, description: str, paginated: bool = False) -> Schema:
    """Output of a list tool: {"items": [...]} plus paging keys when `page` is used."""
    properties: dict[str, Schema] = {"items": _array("Returned entities.", entity)}
    if paginated:
        properties["page"] = _int("Page number returned (only when `page` was requested).")
        properties["limit"] = _int("Page size used (only when `page` was requested).")
        properties["has_next"] = _bool("True when another page exists (only when paginated).")
        description += " With `page` set, also page, limit and has_next."
    return _obj(description, properties, required=("items",))


BULK_UPDATE = _obj(
    "Kommo bulk update response: the updated leads (usually id, name, updated_at) under _embedded.",
    {
        "_total_items": _int("Number of leads updated."),
        "_embedded": _embedded("Updated leads.", leads=LEAD),
        "_links": _LINKS,
    },
)
CHAT_MESSAGE = _obj(
    "Kommo response to POST /talks/{talk_id}/send_message, passed through unchanged."
)

COMPLEX_LEAD = _obj(
    "Result of POST /leads/complex for the created (or merged) lead.",
    {
        "id": _int("Lead ID."),
        "contact_id": _int("ID of the created or linked contact.", nullable=True),
        "company_id": _int("ID of the created or linked company.", nullable=True),
        "request_id": _array("Request IDs sent for this lead.", _str("Request ID.")),
        "merged": _bool("True when Kommo merged the lead into an existing duplicate."),
    },
    required=("id",),
)

OUTPUT_SCHEMAS: dict[str, Schema] = {
    "list_leads": listing(LEAD, "Leads, as {items: [lead, ...]}."),
    "get_lead": single(LEAD, "The lead with contacts, tags and custom fields."),
    "create_lead": single(LEAD, "The created lead (id, name and request_id at minimum)."),
    "update_lead": single(LEAD, "The updated lead as returned by Kommo."),
    "delete_lead": single(LEAD, "The lead marked as deleted, as returned by Kommo."),
    "move_lead_stage": single(LEAD, "The lead after the stage change."),
    "bulk_update_leads": BULK_UPDATE,
    "create_lead_complex": COMPLEX_LEAD,
    "add_tag": single(LEAD, "The lead after the tag was added."),
    "remove_tag": single(LEAD, "The lead after the tag was removed (unchanged if absent)."),
    "list_tags": listing(TAG, "Tags, as {items: [tag, ...]}."),
    "create_task": single(TASK, "The created task."),
    "list_tasks": listing(TASK, "Tasks, as {items: [task, ...]}.", paginated=True),
    "add_note": single(NOTE, "The created note."),
    "send_chat_message": CHAT_MESSAGE,
    "list_chat_templates": listing(CHAT_TEMPLATE, "Chat templates, as {items: [...]}."),
    "list_contacts": listing(CONTACT, "Contacts, as {items: [contact, ...]}.", paginated=True),
    "get_contact": single(CONTACT, "The contact with tags and custom fields."),
    "create_contact": single(CONTACT, "The created contact (id, name and request_id at minimum)."),
    "update_contact": single(CONTACT, "The updated contact as returned by Kommo."),
    "list_pipelines": listing(PIPELINE, "Pipelines, as {items: [pipeline, ...]}."),
    "create_pipeline": single(PIPELINE, "The created pipeline."),
    "update_pipeline": single(PIPELINE, "The updated pipeline."),
    "list_stages": listing(STAGE, "Stages of the pipeline, as {items: [stage, ...]}."),
    "create_stage": single(STAGE, "The created stage."),
    "update_stage": single(STAGE, "The updated stage."),
    "list_custom_fields": listing(CUSTOM_FIELD, "Custom fields, as {items: [field, ...]}."),
    "create_custom_field": single(CUSTOM_FIELD, "The created custom field."),
    "create_company": single(COMPANY, "The created company."),
    "list_companies": listing(COMPANY, "Companies, as {items: [company, ...]}.", paginated=True),
}


def to_structured(result: Any) -> dict[str, Any]:
    """Wrap a handler result as MCP structuredContent (always a JSON object)."""
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"items": result}
    return {"result": result}
