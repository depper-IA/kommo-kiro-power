"""Entry point for the kommo-mcp server."""

from __future__ import annotations

import asyncio
import logging
import sys

from .mcp_server import create_app

logger = logging.getLogger("kommo_mcp")


def main() -> None:
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


async def _async_main() -> None:
    """Async main loop — runs MCP over stdio."""
    from mcp.server.stdio import stdio_server

    app = create_app()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    main()
