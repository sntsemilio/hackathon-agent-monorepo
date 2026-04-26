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


# ---------------------------------------------------------------------------
# Demo fichas — garantizan segmentos correctos para los 8 usuarios demo
# aunque Redis esté vacío. Coinciden con FALLBACK_USERS del frontend.
# ---------------------------------------------------------------------------
_DEMO_FICHAS: Dict[str, Dict[str, Any]] = {
    "USR-00001": {
        "user_id": "USR-00001",
        "segmentos": {
            "conductual": {"name": "actividad_atipica_alerta", "label": "Actividad atípica",
                           "description": "Patrones de uso inusuales detectados"},
            "transaccional": {"name": "comprador_presencial_frecuente", "label": "Comprador presencial",
                              "top_spending_categories": ["Retail", "Supermercado", "Gasolina"]},
            "salud_financiera": {"name": "presion_financiera", "label": "Presión financiera",
                                 "offer_strategy": "Educación financiera, no venta agresiva",
                                 "risk_level": "high"},
        },
        "sugerencias_candidatas": ["verificacion_identidad", "educacion_financiera_hey"],
        "gasto": 3500, "ahorro": 2100, "inversion": 0, "credito": 8900, "health_score": 45,
        "version": "demo-1.0",
    },
    "USR-00042": {
        "user_id": "USR-00042",
        "segmentos": {
            "conductual": {"name": "profesional_prospero_inversor", "label": "Profesional próspero",
                           "description": "Alto ingreso, inversiones activas, alta satisfacción"},
            "transaccional": {"name": "ahorrador_inversor", "label": "Ahorrador inversor",
                              "top_spending_categories": ["Inversiones", "Restaurantes", "Viajes"]},
            "salud_financiera": {"name": "activo_saludable", "label": "Activo saludable",
                                 "offer_strategy": "Productos premium, inversión y patrimonio",
                                 "risk_level": "low"},
        },
        "sugerencias_candidatas": ["inversion_hey", "cuenta_maestra", "seguro_vida"],
        "gasto": 12500, "ahorro": 45000, "inversion": 250000, "credito": 15000, "health_score": 95,
        "version": "demo-1.0",
    },
    "USR-00108": {
        "user_id": "USR-00108",
        "segmentos": {
            "conductual": {"name": "joven_digital_hey_pro", "label": "Joven digital Hey Pro",
                           "description": "Joven, Hey Pro activo, alto uso digital"},
            "transaccional": {"name": "consumidor_digital_ocio", "label": "Consumidor digital",
                              "top_spending_categories": ["Streaming", "Juegos", "Comida a domicilio"]},
            "salud_financiera": {"name": "en_construccion_crediticia", "label": "En construcción crediticia",
                                 "offer_strategy": "Construcción de historial y cashback",
                                 "risk_level": "medium"},
        },
        "sugerencias_candidatas": ["tarjeta_credito_hey", "cashback_hey_pro", "hey_pro"],
        "gasto": 4200, "ahorro": 8500, "inversion": 5000, "credito": 3000, "health_score": 78,
        "version": "demo-1.0",
    },
    "USR-00205": {
        "user_id": "USR-00205",
        "segmentos": {
            "conductual": {"name": "cliente_promedio_estable", "label": "Cliente estable",
                           "description": "Satisfecho, uso regular, sin señales de churn"},
            "transaccional": {"name": "pagador_servicios_hogar", "label": "Pagador servicios",
                              "top_spending_categories": ["Servicios", "Supermercado", "Educación"]},
            "salud_financiera": {"name": "activo_saludable", "label": "Activo saludable",
                                 "offer_strategy": "Upsell gradual: Hey Pro, seguros, inversión básica",
                                 "risk_level": "low"},
        },
        "sugerencias_candidatas": ["hey_pro", "seguro_viaje", "inversion_hey"],
        "gasto": 5800, "ahorro": 12000, "inversion": 8000, "credito": 5000, "health_score": 82,
        "version": "demo-1.0",
    },
    "USR-00310": {
        "user_id": "USR-00310",
        "segmentos": {
            "conductual": {"name": "usuario_estres_financiero", "label": "Estrés financiero",
                           "description": "Utilización de crédito alta, señales de estrés"},
            "transaccional": {"name": "pagador_servicios_hogar", "label": "Pagador servicios",
                              "top_spending_categories": ["Renta", "Servicios", "Farmacia"]},
            "salud_financiera": {"name": "presion_financiera", "label": "Presión financiera",
                                 "offer_strategy": "Reestructuración, planes de pago, no venta agresiva",
                                 "risk_level": "high"},
        },
        "sugerencias_candidatas": ["plan_pago_reestructura", "asesoria_financiera"],
        "gasto": 6500, "ahorro": 1200, "inversion": 0, "credito": 22000, "health_score": 38,
        "version": "demo-1.0",
    },
    "USR-00415": {
        "user_id": "USR-00415",
        "segmentos": {
            "conductual": {"name": "usuario_basico_bajo_enganche", "label": "Usuario básico",
                           "description": "Nuevo cliente, bajo uso, potencial de activación"},
            "transaccional": {"name": "comprador_presencial_frecuente", "label": "Comprador presencial",
                              "top_spending_categories": ["Supermercado", "Farmacia", "Transporte"]},
            "salud_financiera": {"name": "solido_sin_credito", "label": "Sólido sin crédito",
                                 "offer_strategy": "Primer crédito, ahorro automatizado, educación",
                                 "risk_level": "low"},
        },
        "sugerencias_candidatas": ["primer_ahorro", "tarjeta_credito_garantizada", "onboarding_premium"],
        "gasto": 2100, "ahorro": 3500, "inversion": 0, "credito": 0, "health_score": 65,
        "version": "demo-1.0",
    },
    "USR-00520": {
        "user_id": "USR-00520",
        "segmentos": {
            "conductual": {"name": "empresario_alto_volumen", "label": "Empresario activo",
                           "description": "Alto volumen de operaciones, perfil empresarial"},
            "transaccional": {"name": "viajero_internacional", "label": "Viajero internacional",
                              "top_spending_categories": ["Proveedores", "Viajes de negocios", "Software"]},
            "salud_financiera": {"name": "activo_saludable", "label": "Activo saludable",
                                 "offer_strategy": "Cuenta empresarial, nómina, crédito PYME",
                                 "risk_level": "low"},
        },
        "sugerencias_candidatas": ["cuenta_negocios", "credito_pyme", "seguro_vida"],
        "gasto": 45000, "ahorro": 80000, "inversion": 120000, "credito": 35000, "health_score": 92,
        "version": "demo-1.0",
    },
    "USR-00630": {
        "user_id": "USR-00630",
        "segmentos": {
            "conductual": {"name": "en_construccion_crediticia", "label": "Construyendo historial",
                           "description": "Orientado al ahorro, construyendo historial crediticio"},
            "transaccional": {"name": "consumidor_digital_ocio", "label": "Consumidor digital",
                              "top_spending_categories": ["Entretenimiento", "Comida", "Ropa"]},
            "salud_financiera": {"name": "en_construccion_crediticia", "label": "En construcción",
                                 "offer_strategy": "Tarjeta garantizada, reporte de pagos, educación",
                                 "risk_level": "medium"},
        },
        "sugerencias_candidatas": ["tarjeta_credito_garantizada", "primer_ahorro", "codi"],
        "gasto": 3800, "ahorro": 15000, "inversion": 2000, "credito": 2000, "health_score": 71,
        "version": "demo-1.0",
    },
}


async def ficha_injector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hidrata `ficha_cliente` en el estado.
    Orden de búsqueda:
        1. Redis: ficha:{user_id}
        2. _DEMO_FICHAS (garantiza fichas correctas para usuarios demo)
        3. AnalyticsEngine.predict_segments_for_user (fallback KMeans)
    """
    user_id = state.get("user_id") or ""
    if not user_id:
        logger.warning("ficha_injector: user_id vacío")
        return {"ficha_cliente": None}

    redis_client = state.get("_redis_client")
    prefix = state.get("_ficha_prefix") or "ficha:"

    # 1. Redis (fuente de verdad en producción)
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

    # 2. Demo fichas hardcoded (datathon — garantiza segmentos correctos)
    if user_id in _DEMO_FICHAS:
        logger.info("ficha_injector: usando demo ficha para %s", user_id)
        return {"ficha_cliente": _DEMO_FICHAS[user_id]}

    # 3. Fallback: armar ficha sintética con el engine
    engine = init_engine_once()
    default_features = _generate_default_features(user_id)
    segs = engine.predict_segments_for_user(user_id, features=default_features)

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


def _generate_default_features(user_id: str = "") -> Dict[str, Dict[str, float]]:
    """
    Generate reasonable default features for kmeans prediction when
    user profile data is unavailable. Features are seeded by user_id
    to ensure diverse clustering across users.
    """
    import hashlib

    # Use user_id to seed feature variation (deterministic randomization)
    h = hashlib.sha256(user_id.encode()).digest()

    # Scale factors based on user_id hash (0.1x to 3x variation for diversity)
    scale_c = 0.2 + (h[0] / 255.0) * 2.8  # conductual scale: 0.2 to 3.0
    scale_t = 0.2 + (h[1] / 255.0) * 2.8  # transaccional scale: 0.2 to 3.0
    scale_s = 0.2 + (h[2] / 255.0) * 2.8  # salud scale: 0.2 to 3.0

    return {
        "conductual": {
            "gasto": 5000.0 * scale_c,
            "ahorro": 10000.0 * scale_c,
            "inversion": 5000.0 * scale_c,
            "credito_utilizado": 3000.0 * scale_c,
            "num_transacciones": 50.0 * scale_c,
        },
        "transaccional": {
            "retail": 2000.0 * scale_t,
            "restaurantes": 1000.0 * scale_t,
            "servicios": 1500.0 * scale_t,
            "transporte": 500.0 * scale_t,
            "entretenimiento": 800.0 * scale_t,
            "otros": 1200.0 * scale_t,
        },
        "salud_financiera": {
            "ingresos": 50000.0 * scale_s,
            "egresos": 8000.0 * scale_s,
            "credito_activo": 15000.0 * scale_s,
            "credito_utilizado": 3000.0 * scale_s,
            "ahorro_total": 30000.0 * scale_s,
            "num_productos": 3.0 * scale_s,
        },
    }


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
