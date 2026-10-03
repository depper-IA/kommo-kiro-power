"""Pipeline and stage management tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient

PIPELINE_ID = "Kommo pipeline ID (integer). Obtain it from list_pipelines."
ENTITY_TYPES = "leads, contacts, or companies"


def get_pipeline_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_pipelines",
            description=(
                "List all sales pipelines in the account. Read-only. Returns pipeline objects "
                "(id, name, sort, embedded stages as provided by Kommo). Results are cached for "
                "10 minutes, so very recent changes may not show. Start here to obtain the "
                "pipeline_id and stage IDs used by most lead tools."
            ),
            inputSchema={"type": "object", "properties": {}},
            annotations=types.ToolAnnotations(
                title="List pipelines",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_pipeline",
            description=(
                "Create a new sales pipeline with the given name (sort order 99). Not idempotent: "
                "each call creates another pipeline. Returns the created pipeline. Add stages "
                "afterwards with create_stage. Clears the pipelines cache."
            ),
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Pipeline name, e.g. \"Enterprise\"."}
                },
            },
            annotations=types.ToolAnnotations(
                title="Create pipeline",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="update_pipeline",
            description=(
                "Rename an existing pipeline. Only the name can be changed with this tool. "
                "Returns the updated pipeline. Safe to repeat. Clears the pipelines cache. "
                "To change a stage use update_stage."
            ),
            inputSchema={
                "type": "object",
                "required": ["pipeline_id", "name"],
                "properties": {
                    "pipeline_id": {"type": "integer", "description": PIPELINE_ID},
                    "name": {"type": "string", "description": "New pipeline name."},
                },
            },
            annotations=types.ToolAnnotations(
                title="Rename pipeline",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_stages",
            description=(
                "List the stages (statuses) of one pipeline. Read-only. Returns stage objects with "
                "id, name, sort, color, and is_editable. Results are cached for 10 minutes. Use the "
                "stage IDs with list_leads, create_lead, and move_lead_stage."
            ),
            inputSchema={
                "type": "object",
                "required": ["pipeline_id"],
                "properties": {"pipeline_id": {"type": "integer", "description": PIPELINE_ID}},
            },
            annotations=types.ToolAnnotations(
                title="List stages",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_stage",
            description=(
                "Add a stage to a pipeline. It is placed after the pipeline's existing editable "
                "stages (sort is computed automatically). Not idempotent: each call creates "
                "another stage. Returns the created stage. Clears the stage and pipeline caches."
            ),
            inputSchema={
                "type": "object",
                "required": ["pipeline_id", "name"],
                "properties": {
                    "pipeline_id": {"type": "integer", "description": PIPELINE_ID},
                    "name": {"type": "string", "description": "Stage name, e.g. \"Negotiation\"."},
                    "color": {
                        "type": "string",
                        "description": (
                            "Hex color sent to Kommo as-is, e.g. #4CAF50. Optional; Kommo may "
                            "restrict it to its own palette."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Create stage",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="update_stage",
            description=(
                "Change a stage's name, sort order, or color. Only the provided fields are sent; "
                "supply at least one of name, sort, or color. Returns the updated stage. Safe to "
                "repeat. Clears the stage and pipeline caches. Get IDs from list_stages."
            ),
            inputSchema={
                "type": "object",
                "required": ["pipeline_id", "stage_id"],
                "properties": {
                    "pipeline_id": {"type": "integer", "description": PIPELINE_ID},
                    "stage_id": {
                        "type": "integer",
                        "description": "Stage ID within that pipeline. Obtain it from list_stages.",
                    },
                    "name": {"type": "string", "description": "New stage name."},
                    "sort": {
                        "type": "integer",
                        "description": "New sort position; lower values appear first (e.g. 10, 20).",
                    },
                    "color": {
                        "type": "string",
                        "description": "New hex color, e.g. #4CAF50, sent to Kommo as-is.",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Update stage",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_custom_fields",
            description=(
                "List custom field definitions for leads, contacts, or companies. Read-only. "
                "Returns field objects with id, name, code, type, and enum options. Cached for 1 "
                "hour. Use the field IDs in custom_fields_values when calling update_lead or "
                "update_contact."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "default": "leads",
                        "description": f"Entity whose fields to list: {ENTITY_TYPES}. Default \"leads\".",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="List custom fields",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_custom_field",
            description=(
                "Create a custom field on leads, contacts, or companies. Not idempotent: "
                "each call creates another field, so check list_custom_fields first. Returns the "
                "created field. Clears the custom-field cache for that entity. Provide enum_values "
                "for select-type fields."
            ),
            inputSchema={
                "type": "object",
                "required": ["entity_type", "field_type", "name"],
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "description": f"Entity to add the field to: {ENTITY_TYPES}.",
                    },
                    "field_type": {
                        "type": "string",
                        "description": (
                            "Kommo field type sent as-is, e.g. text, numeric, select, multiselect, "
                            "date, url, checkbox."
                        ),
                    },
                    "name": {"type": "string", "description": "Field display name."},
                    "enum_values": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Option labels for select or multiselect fields, in display order, "
                            "e.g. [\"Low\", \"High\"]. Ignored by other types."
                        ),
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="Create custom field",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="create_company",
            description=(
                "Create a company record with a name only. Not idempotent: duplicates are not "
                "checked, so look with list_companies first. Returns the created company. To "
                "create a company alongside a new lead, use create_lead_complex."
            ),
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Company name, e.g. \"Acme Inc\"."},
                },
            },
            annotations=types.ToolAnnotations(
                title="Create company",
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=True,
            ),
        ),
        types.Tool(
            name="list_companies",
            description=(
                "List companies. Read-only. Returns one page of company objects, at most `limit` "
                "(capped at 100), with no name search and no further pagination."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum companies to return. Default 50, capped at 100.",
                    },
                },
            },
            annotations=types.ToolAnnotations(
                title="List companies",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=True,
            ),
        ),
    ]


async def handle_pipeline_tool(client: KommoClient, name: str, args: dict[str, Any]) -> Any | None:
    """Handle pipeline/stage/field/company tool calls."""
    if name == "list_pipelines":
        return await client.list_pipelines()
    if name == "create_pipeline":
        return await client.create_pipeline(args["name"])
    if name == "update_pipeline":
        return await client.update_pipeline(args["pipeline_id"], args["name"])
    if name == "list_stages":
        return await client.list_stages(args["pipeline_id"])
    if name == "create_stage":
        return await client.create_stage(args["pipeline_id"], args["name"], args.get("color"))
    if name == "update_stage":
        return await client.update_stage(
            args["pipeline_id"],
            args["stage_id"],
            args.get("name"),
            args.get("sort"),
            args.get("color"),
        )
    if name == "list_custom_fields":
        return await client.list_custom_fields(args.get("entity_type", "leads"))
    if name == "create_custom_field":
        return await client.create_custom_field(
            args["entity_type"], args["field_type"], args["name"], args.get("enum_values")
        )
    if name == "create_company":
        return await client.create_company(args["name"])
    if name == "list_companies":
        return await client.list_companies(args.get("limit", 50))
    return None
