# Hackathon Agent Monorepo

Production-grade AI agent platform scaffold for Google Cloud Run with async-first backend services, hierarchical LangGraph delegation, MCP tool integration, advanced RAG, classical-ML analytics, RBAC admin observability, and hardened prompt-security controls.

---

## Repository Layout

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
│   │   │   │   ├── profiler_slm.py
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
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   └── models/        # .pkl / .joblib artifacts
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
│   ├── scripts/
│   │   └── generate_initial_profiles.py
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

---

## Architecture Summary

| Layer | Responsibility |
|---|---|
| **Async I/O** | End-to-end `async`/`await` across request handling, graph execution, Redis operations, and tool integration. |
| **Hierarchical delegation** | `supervisor.py` routes to `research` or `tool_ops` subgraphs via LangGraph. |
| **Guardrail SLM** | `micro_agents/guardrail_slm.py` runs before delegation, blocking prompt injection, jailbreak, and system-prompt extraction attempts (fail-closed policy). |
| **Profiler SLM** | `micro_agents/profiler_slm.py` builds real-time conversational profiles (tone, financial literacy, frustrations) with LLM inference or deterministic heuristic fallback. |
| **Summarizer SLM** | `micro_agents/summarizer_slm.py` compresses conversation context for long-running threads. |
| **MCP integration** | `mcp/client.py` and `mcp/adapter.py` transform external MCP tools into LangChain-compatible tools. |
| **Advanced RAG** | Hybrid dense + BM25 retrieval from RedisVL → cross-encoder rerank from Top 15 to Top 3 → Ragas-compatible evaluation. |
| **Analytics engine** | Singleton `AnalyticsEngine` loads classical-ML artifacts (`.pkl` / `.joblib`) at startup and serves user insights (segmentation, financial health, churn risk). |
| **RBAC admin** | JWT-protected `/admin/*` endpoints expose token usage, delegation traces, and eval metrics. |
| **Multimodality** | Base64 image support in global state and `research/vision_agent.py`. |
| **Rate limiting** | Redis-backed budget protection via SlowAPI + async counters. |

---

## Quickstart

### 1. Environment

```bash
cp .env.example .env
```

For local testing without external API keys, the example configuration points every LLM role at a small Ollama model (`qwen2.5:1.5b-instruct`). The first Docker Compose run will download that model automatically.

Set at minimum:

| Variable | Purpose |
|---|---|
| `JWT_SECRET_KEY` | Signing key for admin JWT tokens |
| `REDIS_URL` | Redis connection string (default `redis://redis:6379/0`) |
| `GCP_PROJECT_ID` | Google Cloud project for deployment |
| `GCP_REGION` | Cloud Run target region |
| `GCP_SERVICE_NAME` | Cloud Run service name |

See [`.env.example`](.env.example) for the full list of configurable variables including model selection, RAG parameters, rate limits, analytics paths, and MCP connectivity.

### 2. DevContainers

Open this repo in VS Code and choose **Reopen in Container**. The container installs `uv` and backend dependencies from `backend/pyproject.toml`, including dev extras (pytest, ruff, pre-commit).

### 3. Local Development

```bash
make up
```

This launches via Docker Compose:

| Service | URL |
|---|---|
| Backend | `http://localhost:8080` |
| Frontend | `http://localhost:8081` |
| Redis | `redis://localhost:6379` |

Backend-only hot reload (no Docker):

```bash
make dev
```

### 4. Seed Data

Generate initial conversational profiles from simulated Havi logs:

```bash
cd backend && uv run python scripts/generate_initial_profiles.py
```

### 5. Quality Gates

| Command | Description |
|---|---|
| `make format` | Run Ruff linter (auto-fix) + formatter |
| `make test` | Run pytest suite |
| `make evals` | Run Ragas evaluation framework |

### 6. Deployment (CI/CD)

GitHub Actions workflow at `.github/workflows/deploy.yml` triggers on push to `main`.

**Pipeline stages:**

1. Spin up Redis service container
2. Install dependencies with `uv sync --extra dev`
3. Run `pytest` — pipeline fails fast on test failures
4. Authenticate to Google Cloud via service-account key
5. Build and push backend Docker image to GCR
6. Deploy image to Google Cloud Run

**Required GitHub configuration:**

| Type | Name |
|---|---|
| Secret | `GCP_SA_KEY` |
| Secret | `GCP_PROJECT_ID` |
| Secret | `REDIS_URL` |
| Secret | `JWT_SECRET_KEY` |
| Variable | `CLOUD_RUN_SERVICE` |
| Variable | `GCP_REGION` |

---

## Environment Variable Reference

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Hackathon Agent API` | Application title in FastAPI docs |
| `ENVIRONMENT` | `development` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `TESTING` | `false` | Skip Redis/vector-store init when `true` |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT signing secret |
| `GUARDRAIL_MODEL` | `gpt-4o-mini` | Model for guardrail SLM |
| `SUMMARIZER_MODEL` | `gpt-4o-mini` | Model for summarizer SLM |
| `PROFILER_MODEL` | `gpt-4o-mini` | Model for profiler SLM |
| `SUPERVISOR_ROUTER_MODEL` | `gpt-4o-mini` | Model for supervisor routing |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `REDIS_INDEX_NAME` | `hackathon_docs` | RedisVL index for RAG documents |
| `CHAT_RATE_LIMIT` | `20/minute` | SlowAPI rate limit for chat endpoint |
| `BUDGET_LIMIT_PER_WINDOW` | `20` | Max requests per budget window |
| `BUDGET_WINDOW_SECONDS` | `60` | Budget window duration |
| `ANALYTICS_MODELS_DIR` | `app/analytics/models` | Path to ML model artifacts |
| `MCP_HOST` | `localhost` | MCP server host |
| `MCP_PORT` | `8765` | MCP server port |
| `RAG_DENSE_TOP_K` | `15` | Dense retrieval candidates |
| `RAG_FINAL_TOP_K` | `3` | Final documents after reranking |
| `MAX_GLOBAL_ITERATIONS` | `5` | Max supervisor graph iterations |

---

## Security Notes

- **Fail-closed guardrail** — heuristic-based prompt security blocks suspicious requests before they reach the LLM.
- **RBAC enforcement** — admin metrics and eval routes require JWT tokens with `role=admin`.
- **Sandboxed execution** — the code executor skill applies restrictive local policy checks before running any tool output.
- **Rate limiting** — async Redis-backed counters prevent budget exhaustion at the API layer.

---

## Tech Stack

| Category | Technology |
|---|---|
| Runtime | Python 3.11, `async`/`await` |
| Framework | FastAPI + Uvicorn |
| Agent orchestration | LangGraph, LangChain Core |
| LLM gateway | LiteLLM |
| Vector store | RedisVL (dense + BM25 hybrid) |
| Reranking | sentence-transformers cross-encoder |
| Evaluation | Ragas |
| Analytics | scikit-learn, joblib |
| Auth | python-jose (JWT) |
| Rate limiting | SlowAPI |
| Checkpointing | langgraph-checkpoint-redis |
| Package management | uv + hatchling |
| Linting | Ruff |
| CI/CD | GitHub Actions → Google Cloud Run |
| Containers | Docker, Docker Compose |
| Dev environment | VS Code DevContainers |
