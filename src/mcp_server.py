"""MCP server exposing the research corpus to compatible hosts.

Run ``python -m mcp_server`` for local stdio, or use ``--transport streamable-http``
for a deployable HTTP endpoint. Only stderr is used for server diagnostics: stdout is
reserved for the MCP wire protocol in stdio mode.
"""

from __future__ import annotations

import argparse
import json
import threading
from typing import Any, Dict, List, Optional

from mcp.server import MCPServer

from config import CFG
from graph.neo4j_store import GraphStore
from tools.analyze_corpus import CorpusAnalyzer
from tools.retrieve_evidence import EvidenceRetriever

mcp = MCPServer(
    "research-agent",
    instructions=(
        "Search the local scientific-paper corpus before answering factual questions. "
        "Use analyze_corpus for aggregate corpus statistics and explore_knowledge_graph "
        "for paper, topic, chunk, and figure relationships."
    ),
)

_runtime_lock = threading.Lock()
_retriever: Optional[EvidenceRetriever] = None
_analyzer: Optional[CorpusAnalyzer] = None
_graph: Optional[GraphStore] = None


def _runtime() -> tuple[EvidenceRetriever, CorpusAnalyzer, GraphStore]:
    """Create expensive local models only when an MCP tool first needs them."""
    global _retriever, _analyzer, _graph
    with _runtime_lock:
        if _retriever is None:
            CFG.paths.ensure()
            _retriever = EvidenceRetriever(CFG)
        if _analyzer is None:
            _analyzer = CorpusAnalyzer(CFG)
        if _graph is None:
            _graph = GraphStore(CFG)
        return _retriever, _analyzer, _graph


@mcp.tool()
def retrieve_evidence(
    query: str,
    k: Optional[int] = None,
    topic_filter: Optional[str] = None,
    chunk_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Retrieve cited paper passages, figures, and tables relevant to a query."""
    retriever, _, _ = _runtime()
    # MCP calls are independent requests, unlike calls inside one AgentLoop conversation.
    # Resetting prevents a previous client from suppressing this client's evidence.
    with _runtime_lock:
        retriever.reset()
        return retriever.retrieve(query, k=k, topic_filter=topic_filter, chunk_types=chunk_types)


@mcp.tool()
def analyze_corpus(
    operation: str,
    topic_filter: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute reproducible corpus statistics, timelines, clusters, or topic comparisons."""
    _, analyzer, _ = _runtime()
    return analyzer.analyze(operation, topic_filter=topic_filter, params=params)


@mcp.tool()
def explore_knowledge_graph(entity_id: str, depth: int = 1) -> Dict[str, Any]:
    """Traverse Neo4j relationships around a paper id, chunk id, topic, or figure id."""
    _, _, graph = _runtime()
    return graph.neighbourhood(entity_id, depth)


@mcp.resource("sciagent://corpus/summary")
def corpus_summary() -> str:
    """Current corpus counts, without loading the embedding or reranking models."""
    _, analyzer, _ = _runtime()
    return json.dumps(analyzer.analyze("stats"), ensure_ascii=False)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Research Agent MCP server")
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args(argv)
    options: Dict[str, Any] = {"transport": args.transport}
    if args.transport == "streamable-http":
        options.update(host=args.host, port=args.port, streamable_http_path="/mcp")
    mcp.run(**options)


if __name__ == "__main__":
    main()
