# Hackathon Agent Monorepo

Production-grade AI agent platform scaffold for Google Cloud Run with async-first backend services, hierarchical LangGraph delegation, MCP tool integration, advanced RAG, RBAC admin observability, and hardened prompt-security controls.

## Exact Repository Layout

```text
hackathon-agent-monorepo/
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── deploy.yml
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── admin/
│   │   │       ├── metrics.py
│   │   │       └── evals.py
│   │   ├── agents/
│   │   │   ├── state.py
│   │   │   ├── supervisor.py
│   │   │   ├── micro_agents/
│   │   │   │   ├── guardrail_slm.py
│   │   │   │   └── summarizer_slm.py
│   │   │   └── teams/
│   │   │       ├── research/
│   │   │       │   ├── graph.py
│   │   │       │   ├── state.py
│   │   │       │   ├── agents.py
│   │   │       │   └── vision_agent.py
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
│   │   ├── evals/
│   │   │   ├── framework.py
│   │   │   └── test_set.py
│   │   ├── core/
│   │   │   ├── auth.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── checkpointer.py
│   │   │   └── rate_limit.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   ├── test_agents.py
│   │   ├── test_security.py
│   │   └── test_rag.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── views/
│   │       ├── user_chat.py
│   │       └── admin_dashboard.py
│   └── Dockerfile
├── infrastructure/
│   ├── docker-compose.yml
│   └── setup_redis.sh
├── Makefile
├── .pre-commit-config.yaml
├── .env.example
├── .gitignore
└── README.md
```

## Architecture Summary

- Async I/O end-to-end in backend request handling, graph execution, Redis operations, and tool integration.
- Hierarchical LangGraph delegation in `supervisor.py`, routing to `research` or `tool_ops` subgraphs.
- Guardrail SLM defense in `micro_agents/guardrail_slm.py` runs before delegation and blocks prompt injection, jailbreak, and system prompt extraction attempts.
- MCP integration in `mcp/client.py` and `mcp/adapter.py` transforms external MCP tools into LangChain tools.
- Advanced RAG pipeline:
  - Hybrid retrieval (dense + BM25) from RedisVL in `rag/retrieval.py` and `rag/vector_store.py`
  - Cross-encoder rerank from Top 15 to Top 3 in `rag/re_ranker.py`
  - Ragas-compatible evaluation runner in `evals/framework.py`
- RBAC-protected admin endpoints under `/admin/*` for token usage, delegation traces, and eval metrics.
- Native multimodality support for Base64 images in global state and `research/vision_agent.py`.
- Redis-backed budget protection through slowapi + async Redis counters.

## Quickstart

### 1. Environment

```bash
cp .env.example .env
```

Set at minimum:

- `JWT_SECRET_KEY`
- `REDIS_URL`
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCP_SERVICE_NAME`

### 2. DevContainers

Open this repo in VS Code and choose **Reopen in Container**. The container installs `uv` and backend dependencies from `backend/pyproject.toml`.

### 3. Local Development

```bash
make up
```

This launches:

- Backend at `http://localhost:8080`
- Frontend at `http://localhost:8081`
- Redis at `redis://localhost:6379`

Backend-only hot reload:

```bash
make dev
```

### 4. Quality Gates

Run formatters:

```bash
make format
```

Run tests:

```bash
make test
```

Run eval suite:

```bash
make evals
```

### 5. Deployment (CI/CD)

GitHub Actions workflow at `.github/workflows/deploy.yml` triggers on push to `main`.

Pipeline behavior:

1. Install dependencies with `uv`
2. Run `pytest`
3. Stop immediately if tests fail
4. Build and push backend image
5. Deploy image to Google Cloud Run if tests pass

Required GitHub configuration:

- `secrets.GCP_SA_KEY`
- `secrets.GCP_PROJECT_ID`
- `secrets.REDIS_URL`
- `secrets.JWT_SECRET_KEY`
- `vars.CLOUD_RUN_SERVICE`
- `vars.GCP_REGION`

## Security Notes

- Guardrail policy is fail-closed when heuristics detect attacks.
- Admin metrics and eval routes require JWT tokens with `role=admin`.
- Tool execution skill applies restrictive local policy checks before execution.
