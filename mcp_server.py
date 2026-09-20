import sys
import json
from pathlib import Path
from mcp.server import MCPServer
from typing import Optional

# Bootstrap paths
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from config import CFG
from tools.retrieve_evidence import EvidenceRetriever
from tools.analyze_corpus import CorpusAnalyzer
from tools.explore_graph import GraphExplorer

app = MCPServer("sciagent-mcp")

@app.tool()
def retrieve_evidence(query: str, k: Optional[int] = None, topic_filter: Optional[str] = None) -> str:
    """Retrieve passages, figures, and tables from the indexed papers."""
    retriever = EvidenceRetriever(CFG)
    args = {"query": query}
    if k is not None: args["k"] = k
    if topic_filter is not None: args["topic_filter"] = topic_filter
    result = retriever.retrieve(**args)
    return json.dumps(result, indent=2)

@app.tool()
def analyze_corpus(operation: str, topic_filter: Optional[str] = None) -> str:
    """Statistics over corpus metadata.
    Operations: 'stats', 'timeline', 'cluster', 'compare_topics'
    """
    analyzer = CorpusAnalyzer(CFG)
    args = {"operation": operation}
    if topic_filter is not None: args["topic_filter"] = topic_filter
    result = analyzer.analyze(**args)
    return json.dumps(result, indent=2)

@app.tool()
def explore_graph(entity_id: str, depth: Optional[int] = None) -> str:
    """Explore the knowledge graph neighbourhood around a specific paper, chunk, topic, or figure."""
    explorer = GraphExplorer(CFG)
    args = {"entity_id": entity_id}
    if depth is not None: args["depth"] = depth
    result = explorer.explore(**args)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    app.run()
