# Hey Banco · Havi backend

Agente conversacional con personalización por clustering no supervisado para
el Datathon 2026 de Hey Banco.

## Stack

Python 3.11 · FastAPI · LangGraph · LiteLLM · Redis · RedisVL · scikit-learn.

## Estructura

```
backend/
├── app/
│   ├── main.py                       # FastAPI bootstrap
│   ├── api/routes.py                 # POST /chat/stream (SSE) + healthz
│   ├── core/
│   │   ├── config.py                 # Settings (env vars)
│   │   ├── database.py               # Redis async client
│   │   └── llm.py                    # LiteLLM wrapper
│   ├── analytics/
│   │   ├── engine.py                 # Carga .joblib, predict + mock fallback
│   │   └── models/                   # Output de los scripts offline (.joblib)
│   ├── rag/vector_store.py           # RedisVL HNSW hybrid search
│   └── agents/
│       ├── state.py                  # GlobalState (TypedDict)
│       ├── supervisor.py             # Grafo LangGraph
│       ├── micro_agents/
│       │   ├── ficha_injector.py     # Inyecta ficha de Redis al estado
│       │   ├── guardrail_slm.py      # Seguridad (rule-based + step-up auth)
│       │   ├── profiler_slm.py       # Combina ficha + texto del turno
│       │   └── summarizer_slm.py     # Respuesta final + tarjetas accionables
│       └── teams/
│           ├── research/agents.py    # plan + gather + draft con personalización
│           └── tool_ops/agents.py    # saldo / transferencia / movimientos
├── scripts/agents/offline/
│   ├── _common.py                    # Loaders robustos (utf-8-sig, sexo→genero)
│   ├── 01_train_conductual.py        # K=7
│   ├── 02_train_transaccional.py     # K elegido por silhouette
│   ├── 03_train_salud_financiera.py  # K=4
│   ├── 04_build_fichas_redis.py      # Une asignaciones → ficha:{user_id}
│   └── run_all_offline.sh            # Corre los 4 en orden
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar ANTHROPIC_API_KEY
```

## Pipeline offline (genera modelos + fichas en Redis)

Los 3 modelos se entrenan con los CSVs reales del datathon. Coloca los
archivos en `./data/`:

```
data/
├── hey_clientes.csv         # 15,025 filas
├── hey_productos.csv        # 38,909 filas
└── hey_transacciones.csv    # 802,384 filas
```

Luego corre:

```bash
DATA_DIR=./data \
MODELS_DIR=./backend/app/analytics/models \
REDIS_URL=redis://localhost:6379 \
bash backend/scripts/agents/offline/run_all_offline.sh
```

Esto produce en `MODELS_DIR`:

- `conductual_kmeans.joblib` + `_features.json` + `_assignments.parquet`
- `transaccional_kmeans.joblib` + `_features.json` + `_assignments.parquet`
- `salud_financiera_kmeans.joblib` + `_features.json` + `_assignments.parquet`

Y deja en Redis ~15K claves `ficha:USR-XXXXX` con la estructura:

```json
{
  "user_id": "USR-00001",
  "segmentos": {
    "conductual":     {"cluster": 3, "name": "joven_digital_hey_pro"},
    "transaccional":  {"cluster": 0, "name": "consumidor_digital_ocio",
                       "top_spending_categories": ["servicios_digitales", "entretenimiento"]},
    "salud_financiera": {"cluster": 1, "name": "en_construccion_crediticia",
                         "offer_strategy": "productos_construccion_historial_y_cashback"}
  },
  "sugerencias_candidatas": ["hey_pro", "cashback_hey_pro", "tarjeta_credito_garantizada"],
  "version": "1.0"
}
```

## Levantar el backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Probar

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USR-00001",
    "message": "Quiero saber qué me conviene para empezar a invertir"
  }'
```

## Topología del grafo

```
START
  → ficha_injector  (Redis: ficha:{user_id})
  → guardrail       (rule-based; bloquea o step-up auth)
       ├ blocked  → summarizer (canned)
       └ ok       → profiler   (combina ficha + texto)
                    ↓
                 router (intent)
                    ├ research → plan_research → gather_context → draft_response
                    └ tool_ops → tool_ops_node
                    ↓
                 summarizer (final + UI components)
                    ↓
                  END
```

## Notas sobre los datos

Detectado al validar contra los CSVs reales:

- **Encoding UTF-8 con BOM** → todo se carga con `encoding='utf-8-sig'`.
- **El diccionario dice `genero`, el CSV usa `sexo`** (M/H/SE) →
  `_common.load_clientes()` lo renombra al cargar.
- **Categorías MCC en data real** incluyen `transferencia` y `retiro_cajero`
  fuera del catálogo de 14 → el modelo transaccional los acepta sin romper.
- **`monto` siempre positivo**; la dirección sale de `tipo_operacion`.

## Fallbacks (resilience)

- Sin Redis o sin `ficha:{user_id}` → `ficha_injector` arma una sintética con
  el `AnalyticsEngine`.
- Sin modelos `.joblib` → `AnalyticsEngine` cae a un MOCK SHA-256 determinista.
- Sin RedisVL → `VectorStore.hybrid_search` devuelve `[]` (RAG opcional).
- Sin LiteLLM o fallo de LLM → cada nodo usa su fallback (canned, defaults).

Esto significa que el endpoint `/chat/stream` **nunca falla** por falta de
dependencias externas: degrada limpiamente.
