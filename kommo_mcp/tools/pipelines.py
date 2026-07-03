"""Pipeline and stage management tools."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient


def get_pipeline_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_pipelines",
            description="List all pipelines with their stages.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="create_pipeline",
            description="Create a new pipeline.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string", "description": "Pipeline name"}},
            },
        ),
        types.Tool(
            name="update_pipeline",
            description="Rename an existing pipeline.",
            inputSchema={
                "type": "object",
                "required": ["pipeline_id", "name"],
                "properties": {
                    "pipeline_id": {"type": "integer"},
                    "name": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="list_stages",
            description="List all stages in a pipeline.",
            inputSchema={
                "type": "object",
                "required": ["pipeline_id"],
                "properties": {"pipeline_id": {"type": "integer"}},
            },
        ),
        types.Tool(
            name="create_stage",
            description="Create a new stage in a pipeline.",
            inputSchema={
                "type": "object",
                "required": ["pipeline_id", "name"],
                "properties": {
                    "pipeline_id": {"type": "integer"},
                    "name": {"type": "string", "description": "Stage name"},
                    "color": {"type": "string", "description": "Hex color (e.g. #4CAF50)"},
                },
            },
        ),
        types.Tool(
            name="update_stage",
            description="Update a stage's name, sort order, or color.",
            inputSchema={
                "type": "object",
                "required": ["pipeline_id", "stage_id"],
                "properties": {
                    "pipeline_id": {"type": "integer"},
                    "stage_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "sort": {"type": "integer"},
                    "color": {"type": "string"},
                },
            },
        ),
        types.Tool(
            name="list_custom_fields",
            description="List custom fields for an entity type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "default": "leads", "description": "Entity type: leads, contacts, companies"},
                },
            },
        ),
        types.Tool(
            name="create_custom_field",
            description="Create a custom field on an entity type.",
            inputSchema={
                "type": "object",
                "required": ["entity_type", "field_type", "name"],
                "properties": {
                    "entity_type": {"type": "string", "description": "leads, contacts, or companies"},
                    "field_type": {"type": "string", "description": "text, numeric, select, multiselect, date, url, checkbox"},
                    "name": {"type": "string", "description": "Field name"},
                    "enum_values": {"type": "array", "items": {"type": "string"}, "description": "Values for select/multiselect fields"},
                },
            },
        ),
        types.Tool(
            name="create_company",
            description="Create a new company.",
            inputSchema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Company name"},
                },
            },
        ),
        types.Tool(
            name="list_companies",
            description="List companies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 50},
                },
            },
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
