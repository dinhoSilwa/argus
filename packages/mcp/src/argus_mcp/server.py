from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from argus_mcp.tools import context, memory, scaffold, validate

server = Server("argus")

_tools: list[types.Tool] = [
    *context.TOOLS,
    *memory.TOOLS,
    *scaffold.TOOLS,
    *validate.TOOLS,
]

Handler = Callable[[dict[str, Any]], Coroutine[Any, Any, str]]

_handlers: dict[str, Handler] = {
    **context.HANDLERS,  # type: ignore[arg-type]
    **memory.HANDLERS,  # type: ignore[arg-type]
    **scaffold.HANDLERS,  # type: ignore[arg-type]
    **validate.HANDLERS,  # type: ignore[arg-type]
}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return _tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    handler = _handlers.get(name)
    if handler is None:
        text = f"[ERRO] tool desconhecida: {name}"
    else:
        text = await handler(arguments or {})
    return [types.TextContent(type="text", text=text)]


def main() -> None:
    async def _run() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_run())
