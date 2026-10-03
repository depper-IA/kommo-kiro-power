"""
Kommo MCP Server
================
Defines the MCP server and registers all tools.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import mcp.types as types
from mcp.server import Server

from .kommo_client import KommoClient

logger = logging.getLogger("kommo_mcp.server")


def create_app() -> Server:
    """Create and configure the MCP server instance."""
    app = Server("kommo-crm")
    client = KommoClient()

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        from .tools import get_tool_definitions

        return get_tool_definitions()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
        from .tools import execute_tool, to_structured

        try:
            result = await execute_tool(client, name, arguments)
        except Exception as e:
            logger.error(f"Error executing {name}: {e}", exc_info=True)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Error: {e}")],
                isError=True,
            )
        text = json.dumps(result, ensure_ascii=False, indent=2)
        return [types.TextContent(type="text", text=text)], to_structured(result)

    return app
