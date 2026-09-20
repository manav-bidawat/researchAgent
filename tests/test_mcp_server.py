"""In-memory MCP smoke test: no subprocess, model download, or Neo4j required."""

import asyncio

from mcp import Client

from mcp_server import mcp


def test_server_advertises_the_corpus_tools():
    async def check():
        async with Client(mcp) as client:
            listed = await client.list_tools()
            return {tool.name for tool in listed.tools}

    assert asyncio.run(check()) == {
        "retrieve_evidence",
        "analyze_corpus",
        "explore_knowledge_graph",
    }
