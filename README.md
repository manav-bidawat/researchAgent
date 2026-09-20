# Agentic Research Assistant Over Scientific Literature

This project is an advanced, multi-agent AI system designed to autonomously perform deep research on scientific literature from arXiv. By utilizing large language models (LLMs) and vector databases, the agent plans queries, ingests PDFs, parses complex structures including rendering figures, and subsequently evaluates retrieved evidence to answer complex queries.

## Key Features & Capabilities

- **Autonomous Document Retrieval & Extraction:** Integrates with the arXiv API to programmatically search, fetch, and deduplicate papers. Leverages PyMuPDF to extract text, and dynamically renders figures. A specialized vision model (LLM) captions and describes figures to embed visual context alongside text.
- **Advanced RAG Pipeline:** Employs a sophisticated two-stage retrieval methodology:
  1. A Bi-Encoder performs a wide-pool search (k=40) over a FAISS vector index.
  2. A Cross-Encoder reranks candidates to provide the top-5 highly relevant contexts, gated by an empirically tuned relevance threshold to ensure accuracy and abstention capabilities (reducing hallucination).
- **Knowledge Graph Integration:** Augments the vector store with a robust, Neo4j-backed graph database representation, mapping relationships between Papers, Chunks, Topics, and Figures. This allows GraphRAG-style traversals and intricate metadata analysis.
- **Model Context Protocol (MCP):** Implements an official MCP Server interface, wrapping core reasoning and retrieval mechanisms (`retrieve_evidence`, `analyze_corpus`, `explore_graph`) to be extensible and consumable by standard MCP-compatible clients.
- **Automated Verification & Fact-Checking:** An NLI (Natural Language Inference) model critically reviews drafted responses to check for contradictions against source material, guaranteeing grounded, accurately cited answers.
- **Docker Containerization:** Fully containerized architecture using Docker and Docker Compose. Easily spin up the application environment alongside the Neo4j Graph database with zero manual configuration.

## Architecture & System Design

The system divides operation into two phases: **Indexing** (heavy compute, runs once per topic) and **Inference** (fast and iterative).

```
index "<topic>"
  arXiv query planned by LLM → search & download PDFs
  → PyMuPDF text & vision model figure descriptions
  → section-aware chunks → Bi-Encoder Embeddings 
  → FAISS Vector Store + Neo4j Knowledge Graph

ask "<question>"
  agent loop ── dynamically selects tools for multi-step reasoning
       ├─ retrieve_evidence: bi-encoder → cross-encoder rerank → relevance gate
       ├─ search_literature: mid-question literature expansion
       ├─ analyze_corpus: ML metadata analysis (timeline, KMeans clustering)
       ├─ inspect_figure: attaches multimodal evidence directly into LLM context
       ├─ explore_graph: traverses Neo4j graph paths
       └─ check_evidence_consistency: NLI validation for contradictions & groundedness
```

### Design Principles
- **No Agent Framework Dependency:** The control loop is intentionally handcrafted directly against provider APIs to remove abstraction layers, providing fine-grained control over prompt engineering, state management, and tool dispatching.
- **Empirical Thresholding:** Every configuration, from cross-encoder cutoffs to semantic chunk sizes (445 tokens), is data-backed and tuned against a holdout dataset.

## Setup & Deployment

Tested on **Python 3.10+**.

### Containerized Deployment (Recommended)
Launch the entire system, including the web interface and Neo4j database, using Docker:
```bash
docker-compose up --build
```
This automatically maps required volumes and starts the server at `http://127.0.0.1:8000`.

### Manual Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` in the repository root:
```env
OPENROUTER_API_KEY=sk-or-...      # Required for LLM reasoning and vision processing
OPENROUTER_APP_NAME=sciagent
```

## Usage

### Indexing a Topic
Process and store scientific papers for a particular topic:
```bash
python main.py index "sparse mixture-of-experts routing in transformer models"
```
The agent will build embeddings into FAISS and synchronize the Knowledge Graph with Neo4j.

### Running the Inference Agent
```bash
python main.py ask "What load-balancing losses do these papers use for MoE routing?" --show-tools
```
The system will display trace logs, LLM internal thoughts, and tool dispatch latencies before presenting a cited response.

### Model Context Protocol (MCP) Server
To integrate the AI's research capabilities into standard MCP clients, start the MCP server:
```bash
python mcp_server.py
```
This exposes `retrieve_evidence`, `analyze_corpus`, and `explore_graph` as standard tools.

### UI Dashboard
For a visual demonstration of the trace and real-time execution, run:
```bash
python web/server.py
```
Visit `http://127.0.0.1:8000` to interact with the agent natively.

## Evaluation & Metrics

Our rigorous evaluation harness runs across a custom tuning and held-out dataset, tracking:
- **Fact Coverage & Groundedness:** Ensuring zero hallucinations through NLI consistency checking.
- **MRR (Mean Reciprocal Rank):** Validating the impact of cross-encoder reranking versus baseline bi-encoder cosine similarity.
- **Abstention Accuracy:** The agent successfully learns to say "I don't know" when relevance gates drop below tuned thresholds.

## License & Documentation
For deep dives into design patterns and constraints, refer to:
- `docs/ARCHITECTURE.md`
- `docs/TOOLS.md`
- `docs/EVALUATION.md`
