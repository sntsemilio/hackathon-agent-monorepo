"""
backend/app/analytics/engine.py
================================

Carga los 3 modelos `.joblib` entrenados offline y expone una API uniforme
para predecir el cluster de un usuario en línea (cuando no hay ficha cacheada
en Redis o cuando se quiere recalcular).

Si los .joblib NO existen (p.ej. en un fresh checkout sin scripts corridos),
cae a un MOCK determinista basado en SHA-256(user_id) — útil para tests y
para que el agente nunca se rompa por falta de modelos.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Listado de segmentos (espejo de los scripts offline)
# ---------------------------------------------------------------------------
CONDUCTUAL_SEGMENTS = [
    "usuario_basico_bajo_enganche", "profesional_prospero_inversor",
    "usuario_estres_financiero", "joven_digital_hey_pro",
    "actividad_atipica_alerta", "empresario_alto_volumen",
    "cliente_promedio_estable",
]
TRANSACCIONAL_SEGMENTS = [
    "consumidor_digital_ocio", "pagador_servicios_hogar",
    "comprador_presencial_frecuente", "viajero_internacional",
    "ahorrador_inversor", "transaccional_promedio",
]
SALUD_SEGMENTS = [
    "solido_sin_credito", "en_construccion_crediticia",
    "activo_saludable", "presion_financiera",
]
SALUD_OFFER = {
    "solido_sin_credito": "ofrecer_primer_credito_o_inversion",
    "en_construccion_crediticia": "productos_construccion_historial_y_cashback",
    "activo_saludable": "inversion_seguros_premium",
    "presion_financiera": "alivio_planes_pago_NO_aumentar_deuda",
}


# ---------------------------------------------------------------------------
# Loader de modelos
# ---------------------------------------------------------------------------
class _ModelBundle:
    """Wrapper sobre lo que guarda joblib en cada script offline."""

    def __init__(self, path: Path):
        self.path = path
        self.loaded = False
        self.model = None
        self.scaler = None
        self.feature_cols: List[str] = []
        self.cluster_to_name: Dict[int, str] = {}
        self.extras: Dict[str, Any] = {}

    def try_load(self) -> bool:
        if not self.path.exists():
            logger.warning("Modelo no encontrado: %s — usaré mock", self.path)
            return False
        try:
            data = joblib.load(self.path)
            self.model = data["kmeans"]
            self.scaler = data["scaler"]
            self.feature_cols = list(data["feature_cols"])
            self.cluster_to_name = {int(k): v for k, v in data["cluster_to_name"].items()}
            self.extras = {k: v for k, v in data.items()
                           if k not in {"kmeans", "scaler", "feature_cols", "cluster_to_name"}}
            self.loaded = True
            logger.info("Modelo cargado %s (n_clusters=%d)",
                        self.path.name, len(self.cluster_to_name))
            return True
        except Exception:
            logger.exception("Fallo al cargar %s — usaré mock", self.path)
            return False

    def predict(self, features_row: Dict[str, float]) -> int:
        if not self.loaded:
            raise RuntimeError("Modelo no cargado")
        x = np.array([[features_row.get(c, 0.0) for c in self.feature_cols]], dtype=float)
        x_std = self.scaler.transform(x)
        return int(self.model.predict(x_std)[0])


class AnalyticsEngine:
    """API pública del módulo. Singleton-friendly."""

    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self.conductual = _ModelBundle(self.models_dir / "conductual_kmeans.joblib")
        self.transaccional = _ModelBundle(self.models_dir / "transaccional_kmeans.joblib")
        self.salud = _ModelBundle(self.models_dir / "salud_financiera_kmeans.joblib")
        self._loaded = False

    def load(self) -> None:
        c = self.conductual.try_load()
        t = self.transaccional.try_load()
        s = self.salud.try_load()
        self._loaded = all([c, t, s])
        if not self._loaded:
            logger.warning("AnalyticsEngine: usando MOCK SHA-256 para segmentos faltantes")

    @property
    def fully_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # API por user_id (sólo cuando NO se tienen las features ya calculadas)
    # En el flujo del agente, las fichas ya están en Redis vía script 04,
    # así que esta función es fallback / one-off.
    # ------------------------------------------------------------------
    def predict_segments_for_user(self, user_id: str,
                                  features: Optional[Dict[str, Dict[str, float]]] = None
                                  ) -> Dict[str, Any]:
        if features is None or not all([self.conductual.loaded,
                                        self.transaccional.loaded,
                                        self.salud.loaded]):
            return self._mock_segments(user_id)

        cond_id = self.conductual.predict(features.get("conductual", {}))
        trans_id = self.transaccional.predict(features.get("transaccional", {}))
        salud_id = self.salud.predict(features.get("salud_financiera", {}))

        salud_name = self.salud.cluster_to_name.get(salud_id, "en_construccion_crediticia")
        return {
            "conductual": {
                "cluster": cond_id,
                "name": self.conductual.cluster_to_name.get(cond_id, "cliente_promedio_estable"),
            },
            "transaccional": {
                "cluster": trans_id,
                "name": self.transaccional.cluster_to_name.get(trans_id, "transaccional_promedio"),
                "top_spending_categories": (self.transaccional.extras
                                            .get("top_categories", {})
                                            .get(trans_id, [])),
            },
            "salud_financiera": {
                "cluster": salud_id,
                "name": salud_name,
                "offer_strategy": SALUD_OFFER.get(salud_name, ""),
            },
        }

    # ------------------------------------------------------------------
    def _mock_segments(self, user_id: str) -> Dict[str, Any]:
        h = hashlib.sha256(user_id.encode("utf-8")).digest()
        cond_idx = h[0] % len(CONDUCTUAL_SEGMENTS)
        trans_idx = h[1] % len(TRANSACCIONAL_SEGMENTS)
        salud_idx = h[2] % len(SALUD_SEGMENTS)
        salud_name = SALUD_SEGMENTS[salud_idx]
        return {
            "conductual": {"cluster": cond_idx, "name": CONDUCTUAL_SEGMENTS[cond_idx]},
            "transaccional": {
                "cluster": trans_idx,
                "name": TRANSACCIONAL_SEGMENTS[trans_idx],
                "top_spending_categories": [],
            },
            "salud_financiera": {
                "cluster": salud_idx,
                "name": salud_name,
                "offer_strategy": SALUD_OFFER.get(salud_name, ""),
            },
        }
