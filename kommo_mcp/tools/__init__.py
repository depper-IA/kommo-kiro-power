"""
Kommo MCP Tools
===============
Centralizes tool definitions and routing.
"""

from __future__ import annotations

import json
from typing import Any

import mcp.types as types

from ..kommo_client import KommoClient
from .contacts import get_contact_tools, handle_contact_tool
from .leads import get_lead_tools, handle_lead_tool
from .pipelines import get_pipeline_tools, handle_pipeline_tool
from .schemas import OUTPUT_SCHEMAS, to_structured

__all__ = ["execute_tool", "get_tool_definitions", "handle_tool_call", "to_structured"]


def get_tool_definitions() -> list[types.Tool]:
    """Combine all tool definitions from modules."""
    tools = []
    tools.extend(get_lead_tools())
    tools.extend(get_contact_tools())
    tools.extend(get_pipeline_tools())
    return [t.model_copy(update={"outputSchema": OUTPUT_SCHEMAS[t.name]}) for t in tools]


async def execute_tool(client: KommoClient, name: str, args: dict[str, Any]) -> Any:
    """Route the call to the correct handler and return the raw result."""
    result = await handle_lead_tool(client, name, args)
    if result is None:
        result = await handle_contact_tool(client, name, args)
    if result is None:
        result = await handle_pipeline_tool(client, name, args)

    if result is None:
        raise ValueError(f"Tool not found: {name}")
    return result


async def handle_tool_call(client: KommoClient, name: str, args: dict[str, Any]) -> str:
    """Route the call to the correct handler and return JSON result."""
    return json.dumps(await execute_tool(client, name, args), ensure_ascii=False, indent=2)
