# Havi × Hey Banco · Datathon 2026

> Asistente conversacional inteligente con personalización por clustering no supervisado.
> 
> **Havi** es un agente financiero multimodal que adapta su respuesta al segmento de cliente, 
> integrando RAG, guardrails de seguridad, análisis de riesgo y proyecciones de impacto en tiempo real.

---

## Demo rápida (local)

### Requisitos
- **Python** 3.11+
- **Node** 18+
- **Redis** (Docker o instalado)
- **OpenAI API key** (o compatible con LiteLLM)

### Setup en 3 comandos

```bash
# 1. Clonar
git clone https://github.com/sntsemilio/hackathon-agent-monorepo
cd hackathon-agent-monorepo

# 2. Configurar secretos
cp .env.example .env
# Edita .env con tu OPENAI_API_KEY (o ANTHROPIC_API_KEY, etc.)

# 3. Levantar todo
chmod +x start_local.sh
./start_local.sh
```

Accede a:
- **Chat**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Admin Observability**: http://localhost:5173/admin (integrado en el frontend)

---

## Arquitectura

### Backend (Python 3.11 + FastAPI + LangGraph + LiteLLM)

```
┌─────────────────────────────────────┐
│     /chat/stream (SSE)              │
│     Real-time agent execution       │
└──────────────┬──────────────────────┘
               │
       ┌───────▼────────┐
       │   Supervisor   │  ← Routes requests
       └───┬────────┬───┘
           │        │
    ┌──────▼──┐  ┌──▼───────┐
    │ Research│  │ Tool Ops  │  LangGraph Teams
    │ Team    │  │ Team      │
    └────┬────┘  └──┬───────┘
         │          │
    ┌────▼──────────▼────┐
    │  Micro-agents      │
    │  ├─ Guardrail SLM  │
    │  ├─ Profiler SLM   │
    │  ├─ Summarizer SLM │
    │  └─ Ficha Injector │
    └────┬───────────────┘
         │
    ┌────▼──────────────┐
    │  External APIs    │
    │  ├─ LiteLLM       │
    │  ├─ RAG (Redis)   │
    │  └─ MCP Tools     │
    └───────────────────┘
```

#### Flujo de seguridad
1. **Guardrail SLM** bloquea injection/jailbreak (fail-closed)
2. **Profiler SLM** infiere segmento y riesgo del usuario
3. **Supervisor** delega a Research o Tool Ops según contexto
4. **Tool Ops** ejecuta acciones con MCP (Model Context Protocol)
5. **Summarizer** comprime conversación para contexto largo

### Frontend (React 18 + TypeScript + Vite + Framer Motion + Tailwind)

```
┌──────────────────────────────────────────┐
│          Login Screen (splash)           │
└──────────────┬───────────────────────────┘
               │ onEnter
        ┌──────▼─────────┐
        │  Main App      │
        └──────┬─────────┘
               │
      ┌────────┴────────┐
      │                 │
   ┌──▼──────┐   ┌──────▼────┐
   │ Chat    │   │ Obs        │
   │ View    │   │ Dashboard  │
   └──┬──────┘   └──────┬─────┘
      │                 │
  ┌───▼─────────┐   ┌───▼──────────────┐
  │ 3 Panels    │   │ 4 KPI Cards      │
  │ ├─ Trace    │   │ ├─ Volumen       │
  │ ├─ Chat     │   │ ├─ Costos        │
  │ └─ Ficha    │   │ ├─ Impacto       │
  │             │   │ └─ Seguridad     │
  │             │   │                  │
  │             │   │ Traces Table     │
  │             │   │ RAG Evals        │
  └─────────────┘   │ Proyección       │
                    └──────────────────┘
```

#### Stack UI
- **Framework**: React 18 + TypeScript
- **Build**: Vite (2.5s dev, <2s rebuild)
- **Styling**: Tailwind CSS + custom dark theme
- **Animations**: Framer Motion + CSS keyframes
- **Icons**: Lucide React
- **State**: React hooks + Context API (chat), SSE streaming for real-time
- **Colors**: Green (#00C389), Purple (#6B4EFF), Orange (#FF8C42), Dark (#0D1117)

#### Componentes principales
- `App.tsx` — Shell, view switching, header/footer
- `ChatPanel.tsx` — Chat interface con SSE streaming, action cards
- `TracePanel.tsx` — Real-time agent execution visualization
- `FichaSidebar.tsx` — Customer segmentation + confidence bars
- `ObsDashboard.tsx` — Observability dashboard con métricas live
- `LoginScreen.tsx` — Splash screen de bienvenida

---

## Variables de entorno

Ver `.env.example` para la lista completa. Las mínimas:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `OPENAI_API_KEY` | API key del proveedor | `sk-proj-...` |
| `LLM_MODEL` | Modelo a usar | `gpt-4o-mini` |
| `REDIS_URL` | URL de Redis | `redis://localhost:6379` |
| `VITE_API_BASE_URL` | URL del backend (frontend) | `http://localhost:8000` |
| `ADMIN_JWT_SECRET` | Secret para admin panel | `change-this-in-prod` |

---

## Scripts y herramientas

### Backend

```bash
# Clustering inicial (analytics)
python backend/scripts/generate_initial_profiles.py

# Tests
cd backend && pytest tests/ -v

# Linting
ruff check . --fix
mypy app/
```

### Frontend

```bash
# Dev server (hot reload)
npm run dev

# Build production
npm run build

# Type checking
npm run type-check
```

### Docker

```bash
# Levantar todo con docker-compose
cd infrastructure
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

---

## Stack técnico

| Componente | Tecnología | Nota |
|---|---|---|
| **Orquestación** | LangGraph | Supervisory pattern + subgraphs |
| **LLMs** | LiteLLM | OpenAI, Anthropic, Google compatible |
| **RAG** | Redis + Sentence Transformers | Vector search, sparse retrieval |
| **Async** | FastAPI + asyncio | End-to-end non-blocking I/O |
| **Streaming** | Server-Sent Events (SSE) | Real-time trace + completion |
| **Seguridad** | Custom SLM guardrails | Fail-closed, injection prevention |
| **Analytics** | scikit-learn + joblib | K-means clustering, offline profiles |
| **Frontend** | React 18 + Tailwind | Dark theme, Framer Motion animations |
| **Admin** | Integrated in frontend | Metrics, traces table, eval scores |

---

## Endpoints principales

### Chat
- **POST** `/chat/stream` — Query con SSE streaming de respuesta y traces

### Admin / Observability
- **GET** `/admin/metrics` — Volume, costs, success rates, latency
- **GET** `/admin/evals/ragas` — Faithfulness, answer relevancy, F1 score
- **GET** `/admin/traces?limit=50` — Recent execution traces

### RAG
- **POST** `/rag/retrieve` — Retrieve documents by query (internal use)

---

## Configuración en producción

### Google Cloud Run
```bash
# Build y deploy automático via Cloud Build
# Ver .github/workflows/deploy.yml para el pipeline CI/CD
```

### Variables críticas
- `ADMIN_JWT_SECRET` → Cambiar a valor fuerte
- `OPENAI_API_KEY` → Usar Secret Manager en GCP
- `REDIS_URL` → Usar Cloud Memorystore en lugar de localhost
- `BACKEND_RELOAD=false` → Desactivar reload en producción

---

## Contribir

1. Clonar y crear branch: `git checkout -b feature/my-feature`
2. Cambios en backend → actualizar `pyproject.toml` + tests
3. Cambios en frontend → `npm run type-check` + `npm run build`
4. Commit: `git commit -m "feat: add my feature"`
5. Push y PR

---

## Troubleshooting

**Backend no conecta a Redis**
```bash
redis-cli ping
# Si falla, iniciar: redis-server
```

**Frontend no compila**
```bash
cd frontend-demo
npm install
npm run build
```

**SSE connection closed**
- Verificar CORS en backend (`CORS_ALLOW_ORIGINS`)
- Verificar `VITE_API_BASE_URL` en frontend

---

## Licencia

MIT (Datathon 2026 — Hey Banco + Coagente)

---

**Hecho en 🇲🇽 con ❤️ por el equipo Coagente**
