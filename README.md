# Hackathon Agent Monorepo

Production-ready AI agent monorepo for Google Cloud Run with asynchronous I/O, hierarchical LangGraph delegation, MCP integration, and Redis-backed hybrid RAG.

## Architecture Blueprint

```text
hackathon-agent-monorepo/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── state.py
│   │   │   ├── supervisor.py
│   │   │   └── teams/
│   │   │       ├── research/
│   │   │       │   ├── graph.py
│   │   │       │   ├── state.py
│   │   │       │   └── agents.py
│   │   │       └── tool_ops/
│   │   │           ├── graph.py
│   │   │           └── agents.py
│   │   ├── mcp/
│   │   │   ├── client.py
│   │   │   └── adapter.py
│   │   ├── skills/
│   │   │   └── code_executor.py
│   │   ├── rag/
│   │   │   ├── retrieval.py
│   │   │   ├── re_ranker.py
│   │   │   └── vector_store.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── checkpointer.py
│   │   │   └── database.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── main_view.py
│   └── Dockerfile
├── infrastructure/
│   ├── setup_redis.sh
│   └── deploy_gcp.sh
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

## What Is Implemented

- Async FastAPI backend with Server-Sent Events streaming on POST /chat/stream
- LangGraph supervisor that delegates to two subgraphs:
  - research (hybrid retrieval and summarization)
  - tool_ops (local async code execution skill)
- MCP integration:
  - async JSON-RPC client for external MCP server connections
  - adapter converting MCP JSON tool definitions into LangChain tools
- RAG stack:
  - RedisVL vector + BM25 retrieval strategy
  - simulated reranker pass over merged candidates
- Persistence:
  - AsyncRedisSaver checkpointer for durable graph memory across restarts
- Cloud Run-ready Docker (multi-stage backend image exposing port 8080)

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- uv
- gcloud CLI (for deploy target)

## Environment Setup

1. Copy environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit .env with your Redis endpoint, MCP host/port, and GCP deployment values.

## Local Development

### Option A: Docker Compose

```bash
make up
```

Services:
- Backend API: http://localhost:8080
- Frontend console: http://localhost:8081
- Redis Stack: redis://localhost:6379

### Option B: Backend only (uv)

```bash
cd backend
uv venv
uv pip install -e .
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Or from repo root:

```bash
make dev
```

## Makefile Commands

- make up: build and start all services with Docker Compose
- make dev: run FastAPI backend in hot-reload mode with uv
- make deploy: deploy backend container to Google Cloud Run using infrastructure/deploy_gcp.sh

## API Streaming Contract

Endpoint:

- POST /chat/stream

Request body:

```json
{
  "message": "Research current redis hybrid search patterns",
  "thread_id": "optional-thread-id"
}
```

SSE event types:

- trace: supervisor/subgraph execution events from LangGraph astream_events()
- final: final response payload with thread_id
- error: stream-time exception payload

## Deployment

Deploy to Cloud Run:

```bash
make deploy
```

The deploy script:
- builds backend image
- pushes image to gcr.io
- deploys Cloud Run service on port 8080
- passes runtime env vars for Redis and MCP settings

## Notes for Hackathon Teams

- The supervisor currently uses intent keywords for deterministic routing between subgraphs.
- Reranking is intentionally simulated to keep dependencies light and demo behavior explicit.
- Replace hash-based query embeddings with your production embedding model before launch.
