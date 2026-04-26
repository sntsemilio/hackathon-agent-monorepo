"""
backend/app/observability/feature_flags.py
===========================================

Feature flag service con soporte A/B por segmento.
Lee flags de Redis hash ``feature_flags`` con fallback a defaults in-memory.

Flags iniciales:
  - suggestions_v2          : nueva lógica de sugerencias
  - proactive_notifications : notificaciones push WebSocket
  - voice_input             : habilitar Web Speech API
  - personalization         : toggle de personalización (bypass FichaInjector)
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Defaults que se usan si Redis no tiene el flag
DEFAULT_FLAGS: Dict[str, Dict[str, Any]] = {
    "suggestions_v2": {
        "enabled": True,
        "description": "Nueva lógica de sugerencias candidatas v2",
        "variants": ["control", "treatment"],
        "segment_overrides": {},
    },
    "proactive_notifications": {
        "enabled": True,
        "description": "Notificaciones proactivas vía WebSocket",
        "variants": ["on", "off"],
        "segment_overrides": {},
    },
    "voice_input": {
        "enabled": True,
        "description": "Input de voz con Web Speech API",
        "variants": ["on", "off"],
        "segment_overrides": {},
    },
    "personalization": {
        "enabled": True,
        "description": "Toggle de personalización vía FichaInjector",
        "variants": ["on", "off"],
        "segment_overrides": {},
    },
    "action_cards": {
        "enabled": True,
        "description": "Mostrar action cards con deep links",
        "variants": ["on", "off"],
        "segment_overrides": {},
    },
    "trace_panel": {
        "enabled": True,
        "description": "Mostrar agent trace panel en el frontend",
        "variants": ["on", "off"],
        "segment_overrides": {},
    },
}


class FeatureFlagService:
    """Lee y escribe feature flags en Redis con fallback in-memory."""

    def __init__(self, redis_key: str = "feature_flags") -> None:
        self._redis_key = redis_key
        self._local: Dict[str, Dict[str, Any]] = {**DEFAULT_FLAGS}

    async def load_from_redis(self, redis_client: Any) -> None:
        """Carga flags de Redis hash al cache local."""
        if redis_client is None:
            return
        try:
            raw = redis_client.hgetall(self._redis_key)
            if hasattr(raw, "__await__"):
                raw = await raw
            if raw:
                for name, value in raw.items():
                    try:
                        self._local[name] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        pass
                logger.info("Feature flags cargados de Redis: %d flags", len(raw))
        except Exception:
            logger.exception("Error cargando feature flags de Redis")

    async def save_flag(
        self, redis_client: Any, name: str, config: Dict[str, Any]
    ) -> None:
        """Persiste un flag a Redis y actualiza cache local."""
        self._local[name] = config
        if redis_client is not None:
            try:
                res = redis_client.hset(
                    self._redis_key, name, json.dumps(config, default=str)
                )
                if hasattr(res, "__await__"):
                    await res
            except Exception:
                logger.exception("Error guardando feature flag %s en Redis", name)

    def is_enabled(
        self,
        flag_name: str,
        user_id: str = "",
        segment: str = "",
    ) -> bool:
        """Evalúa si un flag está habilitado para un usuario/segmento."""
        flag = self._local.get(flag_name)
        if flag is None:
            return False

        if not flag.get("enabled", False):
            return False

        # Segment override
        overrides = flag.get("segment_overrides", {})
        if segment and segment in overrides:
            return bool(overrides[segment])

        return True

    def get_variant(self, flag_name: str, user_id: str = "") -> str:
        """Retorna la variante A/B para un usuario (hash determinista)."""
        flag = self._local.get(flag_name)
        if flag is None:
            return "control"

        variants = flag.get("variants", ["control", "treatment"])
        if not variants:
            return "control"

        # Hash determinista del user_id para asignación consistente
        if user_id:
            h = hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest()  # noqa: S324
            idx = int(h[:8], 16) % len(variants)
            return variants[idx]

        return variants[0]

    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        return {**self._local}

    def get_flag(self, name: str) -> Optional[Dict[str, Any]]:
        return self._local.get(name)


# Singleton global
_flag_service: FeatureFlagService | None = None


def get_feature_flags() -> FeatureFlagService:
    global _flag_service
    if _flag_service is None:
        _flag_service = FeatureFlagService()
    return _flag_service
