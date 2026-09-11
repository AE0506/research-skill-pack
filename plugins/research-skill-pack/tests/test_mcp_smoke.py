from __future__ import annotations

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


async def _list_tools() -> list[str]:
    server = StdioServerParameters(
        command="bash",
        args=["./scripts/research-state-mcp"],
        cwd=PLUGIN_ROOT,
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.list_tools()
            return [tool.name for tool in response.tools]


def test_research_state_mcp_discovers_all_public_tools() -> None:
    assert asyncio.run(_list_tools()) == [
        "inspect_research_project",
        "validate_canonical_change",
        "commit_canonical_change",
    ]
