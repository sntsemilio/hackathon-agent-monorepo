"""
backend/app/agents/micro_agents/ficha_injector.py
==================================================

Primer nodo del supervisor. Lee `ficha:{user_id}` de Redis y la mete en
`state["ficha_cliente"]`. Si la ficha no existe, hace fallback al
AnalyticsEngine (que internamente usa MOCK SHA-256 si tampoco hay modelos).

Diseño:
  - El cliente Redis viaja en `state["_redis_client"]` (lo inyecta routes.py).
  - El prefijo viaja en `state["_ficha_prefix"]` (default "ficha:").
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.analytics.engine import AnalyticsEngine, SALUD_OFFER
from app.core.config import get_settings

logger = logging.getLogger(__name__)


# Engine global. Se inicializa una vez por proceso. El supervisor llama a
# `init_engine_once()` durante el bootstrap.
_engine: Optional[AnalyticsEngine] = None


def init_engine_once() -> AnalyticsEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = AnalyticsEngine(settings.MODELS_DIR)
        _engine.load()
    return _engine


async def ficha_injector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hidrata `ficha_cliente` en el estado.
    Orden de búsqueda:
        1. Redis: ficha:{user_id}
        2. AnalyticsEngine.predict_segments_for_user (mock SHA-256 fallback)
    """
    user_id = state.get("user_id") or ""
    if not user_id:
        logger.warning("ficha_injector: user_id vacío")
        return {"ficha_cliente": None}

    redis_client = state.get("_redis_client")
    prefix = state.get("_ficha_prefix") or "ficha:"

    if redis_client is not None:
        key = f"{prefix}{user_id}"
        try:
            raw = await _redis_get(redis_client, key)
            if raw:
                ficha = json.loads(raw)
                logger.info("ficha_injector: HIT Redis %s", key)
                return {"ficha_cliente": ficha}
            logger.info("ficha_injector: MISS Redis %s", key)
        except Exception:
            logger.exception("ficha_injector: error leyendo Redis %s", key)

    # Fallback: armar ficha sintética con el engine
    engine = init_engine_once()
    segs = engine.predict_segments_for_user(user_id)

    ficha = {
        "user_id": user_id,
        "segmentos": segs,
        "sugerencias_candidatas": _suggestions_from_segments(segs),
        "version": "fallback-1.0",
    }
    return {"ficha_cliente": ficha}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _redis_get(client: Any, key: str) -> Optional[str]:
    """Compat con redis.asyncio y redis sync."""
    res = client.get(key)
    if hasattr(res, "__await__"):
        res = await res
    return res


def _suggestions_from_segments(segs: Dict[str, Any]) -> list[str]:
    cond = (segs.get("conductual") or {}).get("name", "")
    salud = (segs.get("salud_financiera") or {}).get("name", "")

    if salud == "presion_financiera":
        return ["plan_pago_reestructura"]
    if cond == "actividad_atipica_alerta":
        return ["verificacion_identidad"]

    out = []
    if salud == "activo_saludable":
        out += ["inversion_hey", "seguro_vida"]
    if salud == "solido_sin_credito":
        out += ["tarjeta_credito_hey", "inversion_hey"]
    if cond == "joven_digital_hey_pro":
        out = ["hey_pro", "cashback_hey_pro"] + out
    if cond == "empresario_alto_volumen":
        out = ["cuenta_negocios", "credito_pyme"] + out

    seen, dedup = set(), []
    for s in out:
        if s not in seen:
            seen.add(s); dedup.append(s)
    return dedup[:3] or ["hey_pro"]
