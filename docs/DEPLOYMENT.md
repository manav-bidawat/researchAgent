# MCP, Neo4j, and containers

The research corpus keeps two complementary data structures. FAISS is the retrieval
index for semantic passage search. Neo4j is a projection of the same corpus for
relationship traversal: papers connect to topics, chunks, figures, and the adjacent
chunks that surround a passage in its source paper.

## MCP server

[`src/mcp_server.py`](../src/mcp_server.py) is a standard MCP server built with the
official Python SDK. It exposes these tools:

| MCP capability | Purpose |
|---|---|
| `retrieve_evidence` | semantic retrieval over the FAISS corpus, with citations and evidence gating |
| `analyze_corpus` | reproducible aggregate statistics, timelines, clusters, and topic comparisons |
| `explore_knowledge_graph` | Neo4j traversal from a paper id, chunk id, topic, or figure id |
| `sciagent://corpus/summary` | MCP resource with current corpus statistics |

For a local MCP host, activate the project environment and start the server over
stdio:

```bash
python -m mcp_server
```

The host owns stdin and stdout, so do not send ordinary terminal output to the server
while it is running. A host configuration can launch it directly with absolute paths:

```json
{
  "mcpServers": {
    "research-agent": {
      "command": "/absolute/path/to/researchAgent/.venv/bin/python",
      "args": ["/absolute/path/to/researchAgent/src/mcp_server.py"]
    }
  }
}
```

For a remote service, use the current Streamable HTTP transport:

```bash
python -m mcp_server --transport streamable-http --host 0.0.0.0 --port 8001
```

Clients connect to `http://host:8001/mcp`.

## Neo4j graph projection

Set these environment variables (or use the Compose defaults):

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=choose-a-password
NEO4J_DATABASE=neo4j
```

After indexing a corpus, project it into Neo4j:

```bash
python main.py graph sync
```

When the Neo4j variables are configured, normal `main.py index` runs and the
agent's `search_literature` tool also refresh the graph. The sync only upserts
corpus-owned nodes and relationships; it does not erase annotations added directly
to Neo4j.

## Docker Compose

Copy `.env.example` to `.env`, set `OPENROUTER_API_KEY`, and choose a
`NEO4J_PASSWORD`. Then start the browser app and Neo4j:

```bash
docker compose up --build
```

The UI is at `http://localhost:8000`; Neo4j Browser is at
`http://localhost:7474`. Corpus files are bind-mounted from `./data`, and Neo4j uses
the persistent `neo4j-data` volume.

Start the Streamable HTTP MCP service as well:

```bash
docker compose --profile mcp up --build
```

It listens at `http://localhost:8001/mcp`. Run `docker compose exec app python main.py
graph sync` to project an existing local index after the database first starts.

## Kubernetes

The manifests under [`deploy/kubernetes`](../deploy/kubernetes) deploy the MCP server
and Neo4j into the `research-agent` namespace. Build and publish the repository image,
then replace `ghcr.io/your-org/research-agent:latest` in
[`mcp-server.yaml`](../deploy/kubernetes/mcp-server.yaml).

Create the required secret before applying the manifests. `NEO4J_AUTH` is the exact
`username/password` value consumed by the Neo4j container.

```bash
kubectl create namespace research-agent
kubectl -n research-agent create secret generic research-agent-secrets \
  --from-literal=OPENROUTER_API_KEY='...' \
  --from-literal=NEO4J_PASSWORD='choose-a-password' \
  --from-literal=NEO4J_AUTH='neo4j/choose-a-password'
kubectl apply -k deploy/kubernetes
```

The `research-agent-data` PVC holds the corpus. It begins empty, so run an indexing
job or `python main.py index ...` against that volume before the MCP retrieval tool can
answer questions. The deployment deliberately has one MCP replica because the supplied
PVC is `ReadWriteOnce`; use shared `ReadWriteMany` storage before scaling replicas.
