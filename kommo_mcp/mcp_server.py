"""
Kommo MCP Server
================
Defines the MCP server and registers all tools.
"""

from __future__ import annotations

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
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        from .tools import handle_tool_call

        try:
            result = await handle_tool_call(client, name, arguments)
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            logger.error(f"Error executing {name}: {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    return app
